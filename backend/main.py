"""
Arkan Finance Platform — FastAPI backend
Orchestrates MarketAgent, NewsAgent, and PortfolioAgent.
"""

import asyncio
import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import MarketAgent, NewsAgent, PortfolioAgent, demo_data

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR       = Path(__file__).parent
PORTFOLIO_FILE = BASE_DIR / "portfolio.json"
FRONTEND_DIR   = BASE_DIR.parent


def _has_internet() -> bool:
    """Probe Yahoo Finance with a real HTTP request (not just TCP)."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
            headers={"User-Agent": "ArkanFinance/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

LIVE_MODE = _has_internet()
logger.info("Network mode: %s", "LIVE" if LIVE_MODE else "DEMO")

# ------------------------------------------------------------------ #
#  In-memory cache                                                      #
# ------------------------------------------------------------------ #

_cache: dict[str, Any] = {}
_cache_ts: dict[str, float] = {}
CACHE_TTL = 60  # seconds


def _cached(key: str, fn, ttl: int = CACHE_TTL):
    now = time.time()
    if key in _cache and now - _cache_ts.get(key, 0) < ttl:
        return _cache[key]
    value = fn()
    _cache[key] = value
    _cache_ts[key] = now
    return value


# ------------------------------------------------------------------ #
#  Agent singletons                                                     #
# ------------------------------------------------------------------ #

market_agent    = MarketAgent()
news_agent      = NewsAgent()
portfolio_agent = PortfolioAgent(PORTFOLIO_FILE)

# ------------------------------------------------------------------ #
#  Background refresh task                                              #
# ------------------------------------------------------------------ #

async def _background_refresh():
    """Warms the live-data cache every 60 s. Skipped in DEMO mode."""
    while True:
        if LIVE_MODE:
            try:
                logger.info("Background refresh: market overview")
                _cached("overview", market_agent.get_overview, ttl=0)
            except Exception as exc:
                logger.warning("Background refresh error: %s", exc)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_background_refresh())
    yield
    task.cancel()


# ------------------------------------------------------------------ #
#  App                                                                  #
# ------------------------------------------------------------------ #

app = FastAPI(title="Arkan Finance Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
#  Serve frontend                                                        #
# ------------------------------------------------------------------ #

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


# ------------------------------------------------------------------ #
#  Market endpoints                                                     #
# ------------------------------------------------------------------ #

@app.get("/api/market/overview")
async def market_overview():
    if not LIVE_MODE:
        return demo_data.MOCK_OVERVIEW
    return _cached("overview", market_agent.get_overview)


@app.get("/api/market/sectors")
async def sectors():
    if not LIVE_MODE:
        return demo_data.MOCK_SECTORS
    return _cached("sectors", market_agent.get_sector_performance, ttl=120)


@app.get("/api/market/movers")
async def movers():
    if not LIVE_MODE:
        return demo_data.MOCK_MOVERS
    return _cached("movers", market_agent.get_movers, ttl=120)


@app.get("/api/quotes")
async def quotes(symbols: str = Query(..., description="Comma-separated tickers")):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(400, "No symbols provided")
    if not LIVE_MODE:
        return {s: demo_data.MOCK_QUOTES.get(s, {"symbol": s, "price": 100.0, "change": 0, "change_pct": 0, "name": s}) for s in symbol_list}
    return market_agent.get_quotes(symbol_list)


@app.get("/api/quote/{symbol}")
async def quote(symbol: str):
    sym = symbol.upper()
    if not LIVE_MODE:
        return demo_data.MOCK_QUOTES.get(sym, {"symbol": sym, "price": 100.0, "change": 0.5, "change_pct": 0.5, "name": sym})
    try:
        return market_agent.get_quote(sym)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/api/chart/{symbol}")
async def chart(
    symbol: str,
    period: str   = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1d",  pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"),
):
    sym = symbol.upper()
    key = f"chart_{sym}_{period}_{interval}"
    if not LIVE_MODE:
        return {
            "symbol":   sym,
            "period":   period,
            "interval": interval,
            "data":     demo_data.mock_chart(sym, period, interval),
            "demo":     True,
        }
    try:
        return _cached(key, lambda: {
            "symbol":   sym,
            "period":   period,
            "interval": interval,
            "data":     market_agent.get_chart(sym, period, interval),
        }, ttl=300)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1)):
    sym = q.strip().upper()
    if not LIVE_MODE:
        hits = [v for k, v in demo_data.MOCK_QUOTES.items() if sym in k or sym in v.get("name", "").upper()]
        return [{"symbol": h["symbol"], "name": h["name"], "type": "EQUITY", "exchange": "NASDAQ"} for h in hits[:5]]
    return market_agent.search(q)


@app.get("/api/technicals/{symbol}")
async def technicals(symbol: str):
    if not LIVE_MODE:
        import random; rsi = random.randint(28, 72)
        return {"symbol": symbol.upper(), "sma20": None, "sma50": None, "rsi14": rsi, "signal": "Overbought" if rsi>70 else "Oversold" if rsi<30 else "Neutral", "demo": True}
    try:
        return market_agent.get_technicals(symbol)
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ------------------------------------------------------------------ #
#  News endpoints                                                       #
# ------------------------------------------------------------------ #

@app.get("/api/news")
async def news(
    limit:    int = Query(30, ge=1, le=100),
    category: str = Query("all"),
):
    if not LIVE_MODE:
        filtered = [n for n in demo_data.MOCK_NEWS if category == "all" or n["category"] == category]
        return filtered[:limit]
    key = f"news_{category}_{limit}"
    return _cached(key, lambda: news_agent.fetch_all(limit, category), ttl=300)


@app.get("/api/news/hot")
async def news_hot():
    if not LIVE_MODE:
        return demo_data.MOCK_HOT
    return _cached("news_hot", news_agent.get_hot, ttl=300)


@app.get("/api/news/{symbol}")
async def news_for_symbol(symbol: str, limit: int = Query(10, ge=1, le=50)):
    sym = symbol.upper()
    if not LIVE_MODE:
        return [n for n in demo_data.MOCK_NEWS if sym in n["title"].upper() or sym in n["summary"].upper()][:limit]
    return news_agent.get_by_symbol(sym, limit)


# ------------------------------------------------------------------ #
#  Portfolio endpoints                                                  #
# ------------------------------------------------------------------ #

@app.get("/api/portfolio")
async def get_portfolio():
    try:
        data = portfolio_agent.get()
        # In demo mode yfinance can't fetch prices — inject from mock data
        if not LIVE_MODE:
            for pos in data.get("positions", []):
                sym  = pos["symbol"]
                mock = demo_data.MOCK_QUOTES.get(sym, {})
                if mock and pos.get("current_price", 0) == 0:
                    last = mock.get("price", pos["avg_cost"])
                    prev = last / (1 + mock.get("change_pct", 0) / 100)
                    pos["current_price"]  = last
                    pos["prev_close"]     = round(prev, 2)
                    pos["market_value"]   = round(pos["shares"] * last, 2)
                    pos["cost_basis"]     = round(pos["shares"] * pos["avg_cost"], 2)
                    pos["unrealized_pnl"] = round(pos["market_value"] - pos["cost_basis"], 2)
                    pos["unrealized_pct"] = round((pos["unrealized_pnl"] / pos["cost_basis"] * 100) if pos["cost_basis"] else 0, 2)
                    pos["day_change"]     = round(pos["shares"] * (last - prev), 2)
                    pos["day_change_pct"] = round(mock.get("change_pct", 0), 2)
            # Recalculate totals
            invested   = sum(p.get("market_value", 0)  for p in data.get("positions", []))
            total_cost = sum(p.get("cost_basis", 0)    for p in data.get("positions", []))
            day_pnl    = sum(p.get("day_change", 0)    for p in data.get("positions", []))
            cash       = data.get("cash", 0)
            total      = round(cash + invested, 2)
            for pos in data.get("positions", []):
                pos["weight_pct"] = round(pos["market_value"] / total * 100, 2) if total else 0
            data["total_value"]    = total
            data["invested_value"] = round(invested, 2)
            data["total_cost"]     = round(total_cost, 2)
            data["total_pnl"]      = round(invested - total_cost, 2)
            data["total_pnl_pct"]  = round((invested - total_cost) / total_cost * 100 if total_cost else 0, 2)
            data["day_pnl"]        = round(day_pnl, 2)
        return data
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/api/portfolio/allocation")
async def portfolio_allocation():
    return portfolio_agent.get_allocation()


class PositionIn(BaseModel):
    symbol:   str
    shares:   float
    avg_cost: float
    notes:    Optional[str] = ""


@app.post("/api/portfolio/position")
async def add_position(body: PositionIn):
    if body.shares <= 0:
        raise HTTPException(400, "shares must be > 0")
    if body.avg_cost <= 0:
        raise HTTPException(400, "avg_cost must be > 0")
    return portfolio_agent.add_position(body.symbol, body.shares, body.avg_cost, body.notes or "")


@app.delete("/api/portfolio/position/{symbol}")
async def remove_position(symbol: str):
    result = portfolio_agent.remove_position(symbol)
    if not result["success"]:
        raise HTTPException(404, f"{symbol} not found in portfolio")
    return result


class CashIn(BaseModel):
    amount: float


@app.put("/api/portfolio/cash")
async def update_cash(body: CashIn):
    if body.amount < 0:
        raise HTTPException(400, "Cash cannot be negative")
    return portfolio_agent.update_cash(body.amount)


class RenameIn(BaseModel):
    name: str


@app.put("/api/portfolio/rename")
async def rename_portfolio(body: RenameIn):
    return portfolio_agent.rename(body.name)


# ------------------------------------------------------------------ #
#  AI Analysis (optional — requires ANTHROPIC_API_KEY in .env)         #
# ------------------------------------------------------------------ #

class AnalyzeRequest(BaseModel):
    question: str
    context:  Optional[str] = ""


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "AI analysis unavailable — set ANTHROPIC_API_KEY in backend/.env")

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = (
        "You are Arkan, an expert financial analyst AI assistant. "
        "Provide concise, actionable, evidence-based financial analysis. "
        "Never provide personalised investment advice; always note market risks. "
        "Format answers in Markdown. Keep responses under 400 words."
    )

    user_content = body.question
    if body.context:
        user_content = f"Context:\n{body.context}\n\nQuestion: {body.question}"

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_content}],
            system=system_prompt,
        )
        return {"answer": message.content[0].text}
    except Exception as exc:
        raise HTTPException(500, f"AI error: {exc}")


# ------------------------------------------------------------------ #
#  Health                                                               #
# ------------------------------------------------------------------ #

@app.get("/api/health")
async def health():
    return {
        "status":     "ok",
        "live_mode":  LIVE_MODE,
        "ai_enabled": bool(os.getenv("ANTHROPIC_API_KEY", "")),
    }
