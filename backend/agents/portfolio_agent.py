"""Portfolio management agent — persists to a JSON file, enriches with live prices."""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)

DEFAULT_CASH = 100_000.0


class PortfolioAgent:
    """Manages a JSON-persisted portfolio; enriches positions with live market data."""

    def __init__(self, filepath: Path) -> None:
        self._file = filepath
        if not self._file.exists():
            self._save(self._blank())

    # ------------------------------------------------------------------ #
    #  Persistence                                                          #
    # ------------------------------------------------------------------ #

    def _blank(self) -> dict[str, Any]:
        return {
            "positions": [],
            "cash":      DEFAULT_CASH,
            "created":   datetime.now().isoformat(),
            "name":      "My Portfolio",
        }

    def _load(self) -> dict[str, Any]:
        try:
            with open(self._file) as fh:
                return json.load(fh)
        except Exception:
            data = self._blank()
            self._save(data)
            return data

    def _save(self, data: dict[str, Any]) -> None:
        with open(self._file, "w") as fh:
            json.dump(data, fh, indent=2)

    # ------------------------------------------------------------------ #
    #  Read                                                                 #
    # ------------------------------------------------------------------ #

    def get(self) -> dict[str, Any]:
        """Return portfolio enriched with current market prices."""
        portfolio = self._load()
        positions = portfolio.get("positions", [])

        if not positions:
            portfolio.update({
                "total_value":    portfolio.get("cash", DEFAULT_CASH),
                "invested_value": 0.0,
                "total_cost":     0.0,
                "total_pnl":      0.0,
                "total_pnl_pct":  0.0,
                "day_pnl":        0.0,
            })
            return portfolio

        # Batch-fetch prices
        symbols = list({p["symbol"] for p in positions})
        prices: dict[str, dict[str, float]] = {}
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for sym in symbols:
                try:
                    fi   = tickers.tickers[sym].fast_info
                    last = float(fi.last_price)
                    prev = float(fi.previous_close)
                    prices[sym] = {"last": last, "prev": prev}
                except Exception as exc:
                    logger.warning("price fetch failed for %s: %s", sym, exc)
                    prices[sym] = {"last": 0.0, "prev": 0.0}
        except Exception as exc:
            logger.error("batch price fetch error: %s", exc)

        cash          = float(portfolio.get("cash", DEFAULT_CASH))
        invested      = 0.0
        total_cost    = 0.0
        day_pnl       = 0.0

        enriched: list[dict[str, Any]] = []
        for pos in positions:
            sym     = pos["symbol"]
            shares  = float(pos["shares"])
            avg_cost = float(pos["avg_cost"])
            p       = prices.get(sym, {"last": avg_cost, "prev": avg_cost})

            market_val = round(shares * p["last"],  2)
            cost_basis = round(shares * avg_cost,    2)
            unreal_pnl = round(market_val - cost_basis, 2)
            unreal_pct = round((unreal_pnl / cost_basis * 100) if cost_basis else 0, 2)
            day_chg    = round(shares * (p["last"] - p["prev"]), 2)
            day_pct    = round(((p["last"] - p["prev"]) / p["prev"] * 100) if p["prev"] else 0, 2)

            invested   += market_val
            total_cost += cost_basis
            day_pnl    += day_chg

            enriched.append({
                **pos,
                "current_price":   round(p["last"], 4),
                "prev_close":      round(p["prev"], 4),
                "market_value":    market_val,
                "cost_basis":      cost_basis,
                "unrealized_pnl":  unreal_pnl,
                "unrealized_pct":  unreal_pct,
                "day_change":      day_chg,
                "day_change_pct":  day_pct,
                "weight_pct":      0.0,  # filled in below
            })

        total_value = round(cash + invested, 2)

        # Portfolio weights
        for pos in enriched:
            pos["weight_pct"] = round(pos["market_value"] / total_value * 100, 2) if total_value else 0

        portfolio["positions"]    = enriched
        portfolio["total_value"]  = total_value
        portfolio["invested_value"] = round(invested, 2)
        portfolio["total_cost"]   = round(total_cost, 2)
        portfolio["total_pnl"]    = round(invested - total_cost, 2)
        portfolio["total_pnl_pct"] = round(
            (invested - total_cost) / total_cost * 100 if total_cost else 0, 2
        )
        portfolio["day_pnl"]      = round(day_pnl, 2)
        return portfolio

    # ------------------------------------------------------------------ #
    #  Write                                                                #
    # ------------------------------------------------------------------ #

    def add_position(
        self,
        symbol: str,
        shares: float,
        avg_cost: float,
        notes: str = "",
    ) -> dict[str, Any]:
        portfolio = self._load()
        sym = symbol.upper()
        existing = next((p for p in portfolio["positions"] if p["symbol"] == sym), None)

        if existing:
            total_shares = existing["shares"] + shares
            total_cost   = existing["shares"] * existing["avg_cost"] + shares * avg_cost
            existing["shares"]   = round(total_shares, 6)
            existing["avg_cost"] = round(total_cost / total_shares, 4)
            if notes:
                existing["notes"] = notes
        else:
            portfolio["positions"].append({
                "id":      int(time.time() * 1000),
                "symbol":  sym,
                "shares":  round(shares, 6),
                "avg_cost": round(avg_cost, 4),
                "notes":   notes,
                "added":   datetime.now().isoformat(),
            })

        self._save(portfolio)
        return {"success": True, "symbol": sym}

    def remove_position(self, symbol: str) -> dict[str, Any]:
        portfolio = self._load()
        before = len(portfolio["positions"])
        portfolio["positions"] = [
            p for p in portfolio["positions"] if p["symbol"] != symbol.upper()
        ]
        self._save(portfolio)
        return {"success": len(portfolio["positions"]) < before}

    def update_cash(self, amount: float) -> dict[str, Any]:
        portfolio = self._load()
        portfolio["cash"] = round(amount, 2)
        self._save(portfolio)
        return {"success": True, "cash": portfolio["cash"]}

    def rename(self, name: str) -> dict[str, Any]:
        portfolio = self._load()
        portfolio["name"] = name
        self._save(portfolio)
        return {"success": True}

    def get_allocation(self) -> list[dict[str, Any]]:
        """Return simplified allocation breakdown for charting."""
        portfolio = self.get()
        total = portfolio.get("total_value", 1)
        alloc = []
        for pos in portfolio.get("positions", []):
            alloc.append({
                "symbol": pos["symbol"],
                "value":  pos["market_value"],
                "pct":    pos["weight_pct"],
            })
        cash = portfolio.get("cash", 0)
        alloc.append({"symbol": "CASH", "value": round(cash, 2), "pct": round(cash / total * 100, 2)})
        return sorted(alloc, key=lambda x: x["value"], reverse=True)
