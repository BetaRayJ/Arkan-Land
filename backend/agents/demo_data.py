"""Realistic demo/mock market data for offline or restricted-network environments."""

import random
import time
from datetime import datetime, timedelta

_R = random.Random(42)


def _jitter(base: float, pct: float = 0.005) -> float:
    return round(base * (1 + _R.uniform(-pct, pct)), 4)


MOCK_OVERVIEW = {
    "S&P 500":      {"symbol": "^GSPC", "display_name": "S&P 500",      "price": 5312.41, "change": 47.28,  "change_pct": 0.90,  "prev_close": 5265.13, "volume": 3_400_000_000},
    "NASDAQ":       {"symbol": "^IXIC", "display_name": "NASDAQ",       "price": 16782.53, "change": 182.34, "change_pct": 1.10, "prev_close": 16600.19, "volume": 5_100_000_000},
    "Dow Jones":    {"symbol": "^DJI",  "display_name": "Dow Jones",    "price": 39312.00, "change": -128.4, "change_pct": -0.33, "prev_close": 39440.40, "volume": 310_000_000},
    "Russell 2000": {"symbol": "^RUT",  "display_name": "Russell 2000", "price": 2078.25, "change": 11.42,  "change_pct": 0.55,  "prev_close": 2066.83, "volume": 1_200_000_000},
    "VIX":          {"symbol": "^VIX",  "display_name": "VIX",          "price": 13.82,   "change": -0.74,  "change_pct": -5.08, "prev_close": 14.56,   "volume": 0},
    "Gold":         {"symbol": "GC=F",  "display_name": "Gold",         "price": 2328.60, "change": 14.30,  "change_pct": 0.62,  "prev_close": 2314.30, "volume": 145_000},
    "Oil (WTI)":    {"symbol": "CL=F",  "display_name": "Oil (WTI)",    "price": 79.42,   "change": -0.68,  "change_pct": -0.85, "prev_close": 80.10,   "volume": 320_000},
    "10Y Bond":     {"symbol": "^TNX",  "display_name": "10Y Bond",     "price": 4.412,   "change": 0.024,  "change_pct": 0.55,  "prev_close": 4.388,   "volume": 0},
    "BTC/USD":      {"symbol": "BTC-USD","display_name": "BTC/USD",     "price": 63248.00, "change": 1428.0, "change_pct": 2.31, "prev_close": 61820.00,"volume": 28_000_000_000},
    "ETH/USD":      {"symbol": "ETH-USD","display_name": "ETH/USD",     "price": 3142.50, "change": -82.30, "change_pct": -2.55, "prev_close": 3224.80, "volume": 14_000_000_000},
}

MOCK_QUOTES = {
    "AAPL":  {"symbol": "AAPL",  "name": "Apple Inc.",                "price": 189.84, "change": 2.14,  "change_pct": 1.14,  "volume": 58_000_000, "market_cap": 2_950_000_000_000, "pe_ratio": 28.4, "high_52w": 199.62, "low_52w": 164.08},
    "MSFT":  {"symbol": "MSFT",  "name": "Microsoft Corporation",     "price": 415.32, "change": 5.88,  "change_pct": 1.44,  "volume": 22_000_000, "market_cap": 3_084_000_000_000, "pe_ratio": 36.1, "high_52w": 430.82, "low_52w": 309.45},
    "GOOGL": {"symbol": "GOOGL", "name": "Alphabet Inc.",             "price": 174.22, "change": -1.32, "change_pct": -0.75, "volume": 19_000_000, "market_cap": 2_156_000_000_000, "pe_ratio": 24.8, "high_52w": 193.31, "low_52w": 129.40},
    "AMZN":  {"symbol": "AMZN",  "name": "Amazon.com Inc.",           "price": 184.72, "change": 3.12,  "change_pct": 1.72,  "volume": 31_000_000, "market_cap": 1_929_000_000_000, "pe_ratio": 46.2, "high_52w": 201.20, "low_52w": 118.35},
    "NVDA":  {"symbol": "NVDA",  "name": "NVIDIA Corporation",        "price": 878.36, "change": 42.18, "change_pct": 5.04,  "volume": 44_000_000, "market_cap": 2_166_000_000_000, "pe_ratio": 66.3, "high_52w": 974.00, "low_52w": 373.06},
    "META":  {"symbol": "META",  "name": "Meta Platforms Inc.",       "price": 492.18, "change": -8.42, "change_pct": -1.68, "volume": 16_000_000, "market_cap": 1_256_000_000_000, "pe_ratio": 25.6, "high_52w": 531.49, "low_52w": 279.40},
    "TSLA":  {"symbol": "TSLA",  "name": "Tesla Inc.",                "price": 172.98, "change": -4.82, "change_pct": -2.71, "volume": 98_000_000, "market_cap": 553_000_000_000,  "pe_ratio": 41.8, "high_52w": 299.29, "low_52w": 138.80},
    "JPM":   {"symbol": "JPM",   "name": "JPMorgan Chase & Co.",      "price": 201.34, "change": 1.88,  "change_pct": 0.94,  "volume": 9_200_000,  "market_cap": 578_000_000_000,  "pe_ratio": 12.4, "high_52w": 223.08, "low_52w": 135.19},
    "BAC":   {"symbol": "BAC",   "name": "Bank of America Corp.",     "price": 38.42,  "change": 0.62,  "change_pct": 1.64,  "volume": 42_000_000, "market_cap": 304_000_000_000,  "pe_ratio": 13.8, "high_52w": 44.44,  "low_52w": 24.96},
    "XOM":   {"symbol": "XOM",   "name": "Exxon Mobil Corporation",   "price": 113.42, "change": -1.28, "change_pct": -1.12, "volume": 18_000_000, "market_cap": 455_000_000_000,  "pe_ratio": 14.2, "high_52w": 123.75, "low_52w": 95.77},
    "AMD":   {"symbol": "AMD",   "name": "Advanced Micro Devices",    "price": 162.34, "change": 8.44,  "change_pct": 5.49,  "volume": 52_000_000, "market_cap": 263_000_000_000,  "pe_ratio": 48.2, "high_52w": 227.30, "low_52w": 96.37},
    "INTC":  {"symbol": "INTC",  "name": "Intel Corporation",         "price": 30.82,  "change": -0.94, "change_pct": -2.96, "volume": 38_000_000, "market_cap": 130_000_000_000,  "pe_ratio": None, "high_52w": 51.28,  "low_52w": 26.86},
    "NFLX":  {"symbol": "NFLX",  "name": "Netflix Inc.",              "price": 628.48, "change": 12.38, "change_pct": 2.01,  "volume": 4_800_000,  "market_cap": 269_000_000_000,  "pe_ratio": 45.2, "high_52w": 700.99, "low_52w": 344.73},
    "DIS":   {"symbol": "DIS",   "name": "The Walt Disney Company",   "price": 108.24, "change": -1.14, "change_pct": -1.04, "volume": 12_000_000, "market_cap": 197_000_000_000,  "pe_ratio": 32.4, "high_52w": 123.74, "low_52w": 78.73},
    "COIN":  {"symbol": "COIN",  "name": "Coinbase Global Inc.",      "price": 218.42, "change": 14.82, "change_pct": 7.27,  "volume": 9_400_000,  "market_cap": 53_000_000_000,   "pe_ratio": 28.4, "high_52w": 283.33, "low_52w": 60.00},
    "PLTR":  {"symbol": "PLTR",  "name": "Palantir Technologies",     "price": 23.84,  "change": 0.98,  "change_pct": 4.29,  "volume": 64_000_000, "market_cap": 51_000_000_000,   "pe_ratio": 82.4, "high_52w": 27.50,  "low_52w": 13.92},
    "SHOP":  {"symbol": "SHOP",  "name": "Shopify Inc.",              "price": 71.22,  "change": 2.44,  "change_pct": 3.55,  "volume": 9_000_000,  "market_cap": 90_000_000_000,   "pe_ratio": 74.8, "high_52w": 91.40,  "low_52w": 43.84},
    "SOFI":  {"symbol": "SOFI",  "name": "SoFi Technologies Inc.",    "price": 7.84,   "change": -0.22, "change_pct": -2.73, "volume": 32_000_000, "market_cap": 8_200_000_000,    "pe_ratio": None, "high_52w": 10.84,  "low_52w": 6.01},
    "RIVN":  {"symbol": "RIVN",  "name": "Rivian Automotive Inc.",    "price": 9.42,   "change": -0.58, "change_pct": -5.80, "volume": 28_000_000, "market_cap": 9_800_000_000,    "pe_ratio": None, "high_52w": 28.05,  "low_52w": 8.26},
    "BABA":  {"symbol": "BABA",  "name": "Alibaba Group Holding",     "price": 78.14,  "change": 3.42,  "change_pct": 4.58,  "volume": 22_000_000, "market_cap": 192_000_000_000,  "pe_ratio": 15.8, "high_52w": 102.65, "low_52w": 66.63},
    "GME":   {"symbol": "GME",   "name": "GameStop Corp.",            "price": 18.24,  "change": -1.12, "change_pct": -5.79, "volume": 14_000_000, "market_cap": 8_000_000_000,    "pe_ratio": None, "high_52w": 64.83,  "low_52w": 10.56},
    "CRM":   {"symbol": "CRM",   "name": "Salesforce Inc.",           "price": 282.48, "change": 6.84,  "change_pct": 2.48,  "volume": 6_400_000,  "market_cap": 273_000_000_000,  "pe_ratio": 44.2, "high_52w": 318.71, "low_52w": 193.61},
    "PYPL":  {"symbol": "PYPL",  "name": "PayPal Holdings Inc.",      "price": 63.82,  "change": -2.14, "change_pct": -3.24, "volume": 14_000_000, "market_cap": 67_000_000_000,   "pe_ratio": 16.2, "high_52w": 92.28,  "low_52w": 56.04},
    "UBER":  {"symbol": "UBER",  "name": "Uber Technologies Inc.",    "price": 72.44,  "change": 1.84,  "change_pct": 2.61,  "volume": 18_000_000, "market_cap": 153_000_000_000,  "pe_ratio": 36.8, "high_52w": 81.82,  "low_52w": 39.46},
    "SNOW":  {"symbol": "SNOW",  "name": "Snowflake Inc.",            "price": 152.34, "change": 4.22,  "change_pct": 2.85,  "volume": 7_200_000,  "market_cap": 50_000_000_000,   "pe_ratio": None, "high_52w": 237.72, "low_52w": 107.13},
    "HOOD":  {"symbol": "HOOD",  "name": "Robinhood Markets Inc.",    "price": 18.42,  "change": 0.88,  "change_pct": 5.02,  "volume": 22_000_000, "market_cap": 16_500_000_000,   "pe_ratio": None, "high_52w": 24.61,  "low_52w": 9.44},
    "SQ":    {"symbol": "SQ",    "name": "Block Inc.",                "price": 68.24,  "change": -1.88, "change_pct": -2.68, "volume": 9_800_000,  "market_cap": 42_000_000_000,   "pe_ratio": 48.6, "high_52w": 88.63,  "low_52w": 41.56},
    "NIO":   {"symbol": "NIO",   "name": "NIO Inc.",                  "price": 4.82,   "change": 0.22,  "change_pct": 4.78,  "volume": 48_000_000, "market_cap": 9_600_000_000,    "pe_ratio": None, "high_52w": 16.78,  "low_52w": 3.61},
    "PDD":   {"symbol": "PDD",   "name": "PDD Holdings Inc.",         "price": 138.42, "change": 7.82,  "change_pct": 5.99,  "volume": 8_600_000,  "market_cap": 191_000_000_000,  "pe_ratio": 14.8, "high_52w": 163.63, "low_52w": 93.46},
    "BTC-USD": {"symbol": "BTC-USD", "name": "Bitcoin USD",          "price": 63248.00,"change": 1428.0,"change_pct": 2.31, "volume": 28_000_000_000,"market_cap": 1_244_000_000_000,"pe_ratio": None,"high_52w": 73750.0,"low_52w": 15487.0},
    "ETH-USD": {"symbol": "ETH-USD", "name": "Ethereum USD",         "price": 3142.50, "change": -82.3, "change_pct": -2.55,"volume": 14_000_000_000,"market_cap": 377_000_000_000,"pe_ratio": None,"high_52w": 4092.0, "low_52w": 1508.0},
    "SPY":   {"symbol": "SPY",   "name": "SPDR S&P 500 ETF",         "price": 528.24, "change": 4.72,  "change_pct": 0.90,  "volume": 62_000_000, "market_cap": None, "pe_ratio": None, "high_52w": 544.07, "low_52w": 407.02},
    "QQQ":   {"symbol": "QQQ",   "name": "Invesco QQQ Trust",        "price": 448.34, "change": 4.92,  "change_pct": 1.11,  "volume": 38_000_000, "market_cap": None, "pe_ratio": None, "high_52w": 461.97, "low_52w": 338.41},
}

MOCK_SECTORS = [
    {"sector": "Technology",       "etf": "XLK",  "change_pct": 1.82,  "price": 208.42},
    {"sector": "Communication",    "etf": "XLC",  "change_pct": 1.44,  "price": 82.34},
    {"sector": "Consumer Disc.",   "etf": "XLY",  "change_pct": 0.88,  "price": 182.14},
    {"sector": "Financials",       "etf": "XLF",  "change_pct": 0.72,  "price": 41.28},
    {"sector": "Industrials",      "etf": "XLI",  "change_pct": 0.38,  "price": 124.82},
    {"sector": "Materials",        "etf": "XLB",  "change_pct": 0.22,  "price": 91.44},
    {"sector": "Healthcare",       "etf": "XLV",  "change_pct": -0.14, "price": 142.88},
    {"sector": "Real Estate",      "etf": "XLRE", "change_pct": -0.44, "price": 38.22},
    {"sector": "Consumer Staples", "etf": "XLP",  "change_pct": -0.62, "price": 74.38},
    {"sector": "Utilities",        "etf": "XLU",  "change_pct": -0.84, "price": 67.14},
    {"sector": "Energy",           "etf": "XLE",  "change_pct": -1.22, "price": 88.92},
]

MOCK_MOVERS = {
    "gainers": [
        {"symbol": "NVDA",  "price": 878.36, "change_pct": 5.04},
        {"symbol": "AMD",   "price": 162.34, "change_pct": 5.49},
        {"symbol": "COIN",  "price": 218.42, "change_pct": 7.27},
        {"symbol": "PDD",   "price": 138.42, "change_pct": 5.99},
        {"symbol": "HOOD",  "price": 18.42,  "change_pct": 5.02},
    ],
    "losers": [
        {"symbol": "RIVN", "price": 9.42,  "change_pct": -5.80},
        {"symbol": "GME",  "price": 18.24, "change_pct": -5.79},
        {"symbol": "TSLA", "price": 172.98,"change_pct": -2.71},
        {"symbol": "INTC", "price": 30.82, "change_pct": -2.96},
        {"symbol": "PYPL", "price": 63.82, "change_pct": -3.24},
    ],
}

MOCK_NEWS = [
    {"title": "Fed Signals Possible Rate Cut Later This Year as Inflation Cools", "summary": "Federal Reserve officials hinted at potential interest rate reductions as the latest CPI data showed inflation edging closer to the 2% target, boosting equity markets.", "link": "#", "published": "Thu, 14 May 2026 14:30:00 +0000", "source": "Reuters Business",    "category": "economy"},
    {"title": "NVIDIA Posts Record Quarterly Revenue Driven by AI Chip Demand",   "summary": "NVIDIA Corporation reported a record $26B in quarterly revenue, exceeding analyst forecasts by 12%, with its data center segment growing 427% year-over-year.", "link": "#", "published": "Thu, 14 May 2026 13:00:00 +0000", "source": "Yahoo Finance",       "category": "market"},
    {"title": "Bitcoin Surges Past $63,000 as Spot ETF Inflows Accelerate",       "summary": "Bitcoin climbed above the $63,000 mark as institutional inflows into spot Bitcoin ETFs reached $800M in a single day, the highest since the product's January launch.", "link": "#", "published": "Thu, 14 May 2026 12:15:00 +0000", "source": "MarketWatch",         "category": "market"},
    {"title": "S&P 500 Approaches All-Time High on Strong Tech Earnings Season",   "summary": "The S&P 500 index approached record territory as a wave of upside earnings surprises from major technology companies bolstered investor confidence.", "link": "#", "published": "Thu, 14 May 2026 11:30:00 +0000", "source": "CNBC Markets",         "category": "market"},
    {"title": "Apple Vision Pro 2 Pre-Orders Hit Record, Boosting Supplier Stocks","summary": "Strong pre-order data for the second-generation Apple Vision Pro headset lifted shares of key suppliers including TSMC, Qualcomm, and Sony.", "link": "#", "published": "Thu, 14 May 2026 10:45:00 +0000", "source": "Seeking Alpha",        "category": "analysis"},
    {"title": "Amazon Web Services Revenue Accelerates to 21% Growth in Q1 2026",  "summary": "AWS, Amazon's cloud computing unit, delivered $28.8B in quarterly revenue—representing 21% YoY growth—as enterprise AI workloads drove adoption of its generative AI services.", "link": "#", "published": "Thu, 14 May 2026 10:00:00 +0000", "source": "Yahoo Finance",       "category": "market"},
    {"title": "Oil Dips Below $80 as OPEC+ Production Data Disappoints Bulls",     "summary": "Crude oil fell modestly after OPEC+ figures showed higher-than-expected production among member nations, easing supply concerns that had supported prices.", "link": "#", "published": "Thu, 14 May 2026 09:30:00 +0000", "source": "Reuters Business",    "category": "economy"},
    {"title": "Tesla Recalls 125,000 Vehicles Over Software Autopilot Issue",      "summary": "The National Highway Traffic Safety Administration announced a Tesla recall affecting 125,000 Model S, X, and Y vehicles due to an Autopilot system defect that could lead to unintended braking.", "link": "#", "published": "Thu, 14 May 2026 09:00:00 +0000", "source": "MarketWatch",         "category": "market"},
    {"title": "Microsoft Azure AI Bookings Surge 60% as Enterprises Rush to Adopt","summary": "Microsoft's cloud division reported a 60% spike in Azure AI service bookings during its third fiscal quarter, validating massive capex investments made in 2025.", "link": "#", "published": "Thu, 14 May 2026 08:30:00 +0000", "source": "CNBC Finance",         "category": "economy"},
    {"title": "Gold Holds Near $2,330 as Dollar Weakens on Soft CPI Reading",      "summary": "Spot gold traded near two-week highs as softer-than-expected US CPI data weakened the dollar, making bullion more attractive to foreign buyers.", "link": "#", "published": "Wed, 13 May 2026 22:00:00 +0000", "source": "Reuters Business",    "category": "economy"},
    {"title": "Palantir Wins $2.4B US Army AI Contract, Shares Jump 8%",           "summary": "Palantir Technologies secured a $2.4 billion multi-year contract to provide AI-driven battlefield analytics software to the US Army, sending shares sharply higher in after-hours trading.", "link": "#", "published": "Wed, 13 May 2026 20:00:00 +0000", "source": "Seeking Alpha",        "category": "analysis"},
    {"title": "GameStop CEO Ryan Cohen Teases Mystery Acquisition in Letter",      "summary": "GameStop CEO Ryan Cohen published a shareholder letter hinting at a significant strategic acquisition outside of gaming, causing renewed retail investor speculation.", "link": "#", "published": "Wed, 13 May 2026 18:30:00 +0000", "source": "MarketWatch",         "category": "market"},
    {"title": "Coinbase Q1 Earnings Beat Forecasts as Trading Volume Doubles",     "summary": "Coinbase reported Q1 2026 net revenue of $2.2B, up 115% YoY, driven by a surge in crypto trading volumes following the Bitcoin halving event.", "link": "#", "published": "Wed, 13 May 2026 16:00:00 +0000", "source": "Yahoo Finance",       "category": "market"},
    {"title": "US Jobs Market Remains Resilient with 215K New Nonfarm Payrolls",   "summary": "April's nonfarm payroll report showed 215,000 new jobs added to the US economy, beating the 190,000 consensus estimate and keeping the unemployment rate at 3.9%.", "link": "#", "published": "Wed, 13 May 2026 14:30:00 +0000", "source": "Reuters Business",    "category": "economy"},
    {"title": "Meta Unveils Orion AR Glasses — Could Replace Smartphones by 2028", "summary": "Meta Platforms revealed 'Orion', its most advanced augmented reality glasses, with a full-color holographic display and 8-hour battery life, targeting mass production by 2028.", "link": "#", "published": "Wed, 13 May 2026 12:00:00 +0000", "source": "CNBC Markets",         "category": "market"},
    {"title": "Robinhood Launches Zero-Fee Futures Trading for Retail Investors",  "summary": "Robinhood introduced no-commission futures trading for retail customers across equity index, metals, and energy futures, pressuring established brokerages.", "link": "#", "published": "Wed, 13 May 2026 10:00:00 +0000", "source": "Seeking Alpha",        "category": "analysis"},
    {"title": "Alibaba Beats Revenue Estimates, Plans $5B Buyback",                "summary": "Alibaba Group's fiscal Q4 revenue grew 9% to ¥236B ($32.6B), topping forecasts, and the company announced a $5B share repurchase program as part of a strategic restructuring.", "link": "#", "published": "Tue, 12 May 2026 14:00:00 +0000", "source": "Yahoo Finance",       "category": "market"},
    {"title": "What the Fed's Pause Means for Your Portfolio Right Now",           "summary": "With the Federal Reserve on hold, investors should reassess duration risk in fixed income, consider dividend growth equities, and maintain exposure to commodity hedges.", "link": "#", "published": "Tue, 12 May 2026 12:00:00 +0000", "source": "Investopedia",        "category": "education"},
]

MOCK_HOT = {
    "trending_topics": [
        {"keyword": "AI",         "count": 18},
        {"keyword": "NVDA",       "count": 14},
        {"keyword": "FED",        "count": 12},
        {"keyword": "BITCOIN",    "count": 11},
        {"keyword": "RATES",      "count": 9},
        {"keyword": "EARNINGS",   "count": 8},
        {"keyword": "INFLATION",  "count": 7},
        {"keyword": "CHIP",       "count": 6},
        {"keyword": "CRYPTO",     "count": 6},
        {"keyword": "PLTR",       "count": 5},
        {"keyword": "TESLA",      "count": 5},
        {"keyword": "IPO",        "count": 4},
        {"keyword": "GOLD",       "count": 4},
        {"keyword": "MERGER",     "count": 3},
        {"keyword": "BUYBACK",    "count": 3},
    ],
    "hot_articles": MOCK_NEWS[:10],
}


def mock_chart(symbol: str, period: str = "1mo", interval: str = "1d") -> list[dict]:
    """Generate a realistic random-walk price series."""
    base = MOCK_QUOTES.get(symbol.upper(), {}).get("price", 100.0) or 100.0

    if period in ("1d",):
        n, ms_step = 78, 5 * 60 * 1000
    elif period in ("5d",):
        n, ms_step = 195, 15 * 60 * 1000
    elif period in ("1mo",):
        n, ms_step = 22, 86_400_000
    elif period in ("3mo",):
        n, ms_step = 63, 86_400_000
    elif period in ("6mo",):
        n, ms_step = 126, 86_400_000
    elif period in ("1y",):
        n, ms_step = 252, 86_400_000
    elif period in ("2y",):
        n, ms_step = 504, 86_400_000
    elif period in ("5y",):
        n, ms_step = 260, 7 * 86_400_000
    else:
        n, ms_step = 22, 86_400_000

    now_ms    = int(time.time() * 1000)
    start_ms  = now_ms - n * ms_step

    rng  = random.Random(hash(symbol + period))
    prev = base * 0.85  # start a bit below current
    data = []
    for i in range(n):
        t  = start_ms + i * ms_step
        ch = prev * rng.gauss(0.0003, 0.012)
        o  = round(prev, 2)
        c  = round(max(prev + ch, 0.01), 2)
        h  = round(max(o, c) * (1 + abs(rng.gauss(0, 0.004))), 2)
        l  = round(min(o, c) * (1 - abs(rng.gauss(0, 0.004))), 2)
        v  = int(abs(rng.gauss(20_000_000, 8_000_000)))
        data.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
        prev = c
    # Pin last point to known price
    if data:
        data[-1]["c"] = base
    return data
