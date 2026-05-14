"""Market data gathering agent — sources: Yahoo Finance via yfinance."""

import yfinance as yf
from typing import Any
import logging

logger = logging.getLogger(__name__)

INDICES: dict[str, str] = {
    "S&P 500":      "^GSPC",
    "NASDAQ":       "^IXIC",
    "Dow Jones":    "^DJI",
    "Russell 2000": "^RUT",
    "VIX":          "^VIX",
    "Gold":         "GC=F",
    "Oil (WTI)":    "CL=F",
    "10Y Bond":     "^TNX",
    "BTC/USD":      "BTC-USD",
    "ETH/USD":      "ETH-USD",
}

SECTOR_ETFS: dict[str, str] = {
    "Technology":       "XLK",
    "Healthcare":       "XLV",
    "Financials":       "XLF",
    "Energy":           "XLE",
    "Consumer Disc.":   "XLY",
    "Consumer Staples": "XLP",
    "Industrials":      "XLI",
    "Materials":        "XLB",
    "Real Estate":      "XLRE",
    "Utilities":        "XLU",
    "Communication":    "XLC",
}

MOVER_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "BAC", "XOM",
    "AMD", "INTC", "CRM", "NFLX", "DIS", "UBER", "COIN", "PLTR", "SNOW", "SHOP",
    "GME", "AMC", "SOFI", "RIVN", "NIO", "BABA", "PDD", "PYPL", "HOOD", "SQ",
]


class MarketAgent:
    """Gathers live market data: quotes, charts, sector performance, movers."""

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _quote_from_ticker(self, symbol: str, ticker: yf.Ticker) -> dict[str, Any]:
        fi = ticker.fast_info
        try:
            last = float(fi.last_price)
            prev = float(fi.previous_close)
        except Exception:
            hist = ticker.history(period="5d", interval="1d")
            if hist.empty:
                return {"symbol": symbol, "error": "no data"}
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last

        change = last - prev
        change_pct = (change / prev * 100) if prev else 0.0

        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            pass

        return {
            "symbol":     symbol,
            "name":       info.get("shortName") or info.get("longName") or symbol,
            "price":      round(last, 4),
            "change":     round(change, 4),
            "change_pct": round(change_pct, 4),
            "prev_close": round(prev, 4),
            "volume":     int(fi.three_month_average_volume or 0),
            "market_cap": info.get("marketCap"),
            "pe_ratio":   info.get("trailingPE"),
            "high_52w":   info.get("fiftyTwoWeekHigh"),
            "low_52w":    info.get("fiftyTwoWeekLow"),
            "currency":   info.get("currency", "USD"),
        }

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_quote(self, symbol: str) -> dict[str, Any]:
        ticker = yf.Ticker(symbol.upper())
        return self._quote_from_ticker(symbol.upper(), ticker)

    def get_quotes(self, symbols: list[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        tickers = yf.Tickers(" ".join(s.upper() for s in symbols))
        for sym in symbols:
            sym_upper = sym.upper()
            try:
                t = tickers.tickers[sym_upper]
                result[sym_upper] = self._quote_from_ticker(sym_upper, t)
            except Exception as exc:
                logger.warning("quote failed for %s: %s", sym_upper, exc)
                result[sym_upper] = {"symbol": sym_upper, "error": str(exc)}
        return result

    def get_overview(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, sym in INDICES.items():
            try:
                q = self.get_quote(sym)
                q["display_name"] = name
                result[name] = q
            except Exception as exc:
                logger.warning("overview failed for %s: %s", name, exc)
                result[name] = {"symbol": sym, "display_name": name, "error": str(exc)}
        return result

    def get_chart(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period, interval=interval, auto_adjust=True)
        if hist.empty:
            return []
        return [
            {
                "t": int(ts.timestamp() * 1000),
                "o": round(float(row.Open), 4),
                "h": round(float(row.High), 4),
                "l": round(float(row.Low), 4),
                "c": round(float(row.Close), 4),
                "v": int(row.Volume),
            }
            for ts, row in hist.iterrows()
        ]

    def get_sector_performance(self) -> list[dict[str, Any]]:
        result = []
        for sector, etf in SECTOR_ETFS.items():
            try:
                q = self.get_quote(etf)
                result.append({
                    "sector":     sector,
                    "etf":        etf,
                    "change_pct": q.get("change_pct", 0),
                    "price":      q.get("price", 0),
                })
            except Exception:
                result.append({"sector": sector, "etf": etf, "change_pct": 0, "price": 0})
        return sorted(result, key=lambda x: x["change_pct"], reverse=True)

    def get_movers(self) -> dict[str, Any]:
        quotes = self.get_quotes(MOVER_UNIVERSE)
        valid = [v for v in quotes.values() if "change_pct" in v and "error" not in v]
        valid.sort(key=lambda x: x["change_pct"], reverse=True)
        return {
            "gainers": valid[:5],
            "losers":  list(reversed(valid[-5:])),
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        sym = query.strip().upper()
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info or {}
            if info.get("symbol"):
                return [{
                    "symbol":   info["symbol"],
                    "name":     info.get("shortName", ""),
                    "type":     info.get("quoteType", ""),
                    "exchange": info.get("exchange", ""),
                }]
        except Exception:
            pass
        return []

    def get_technicals(self, symbol: str) -> dict[str, Any]:
        """Basic technical indicators: SMA20, SMA50, RSI14."""
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="3mo", interval="1d", auto_adjust=True)
        if len(hist) < 20:
            return {}

        closes = hist["Close"]
        sma20 = round(float(closes.rolling(20).mean().iloc[-1]), 2)
        sma50 = round(float(closes.rolling(50).mean().iloc[-1]), 2) if len(closes) >= 50 else None

        # RSI-14
        delta = closes.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss
        rsi14 = round(float(100 - 100 / (1 + rs.iloc[-1])), 2)

        return {
            "symbol": symbol.upper(),
            "sma20":  sma20,
            "sma50":  sma50,
            "rsi14":  rsi14,
            "signal": (
                "Overbought" if rsi14 > 70 else
                "Oversold"   if rsi14 < 30 else
                "Neutral"
            ),
        }
