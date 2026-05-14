"""News aggregation agent — sources: RSS feeds from major financial outlets."""

import re
import html
import logging
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

SOURCES: list[dict[str, str]] = [
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "category": "market",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "category": "market",
    },
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "category": "economy",
    },
    {
        "name": "CNBC Markets",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "category": "market",
    },
    {
        "name": "CNBC Finance",
        "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
        "category": "economy",
    },
    {
        "name": "Seeking Alpha",
        "url": "https://seekingalpha.com/market_currents.xml",
        "category": "analysis",
    },
    {
        "name": "Investopedia",
        "url": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
        "category": "education",
    },
    {
        "name": "Bloomberg Markets",
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "category": "market",
    },
]

# Financial keywords to extract for trending topics
FINANCIAL_KEYWORDS = {
    "FED", "FOMC", "INFLATION", "GDP", "RATE", "RATES", "RECESSION", "BULL", "BEAR",
    "IPO", "SPO", "MERGER", "ACQUISITION", "EARNINGS", "DIVIDEND", "BUYBACK",
    "CRYPTO", "BITCOIN", "ETHEREUM", "AI", "CHIP", "SEMICONDUCTOR", "OIL", "GOLD",
    "BONDS", "YIELDS", "DOLLAR", "EURO", "JOBS", "UNEMPLOYMENT", "CPI", "PPI",
    "RALLY", "SELLOFF", "CORRECTION", "CRASH", "SURGE", "PLUNGE", "SOAR",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE  = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = html.unescape(text)
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


class NewsAgent:
    """Fetches and analyses financial news from multiple RSS feeds."""

    @staticmethod
    def _parse_rss(url: str, max_items: int = 12) -> list[dict[str, Any]]:
        """Fetch and parse an RSS/Atom feed without feedparser."""
        NS = {
            "atom":    "http://www.w3.org/2005/Atom",
            "media":   "http://search.yahoo.com/mrss/",
            "content": "http://purl.org/rss/1.0/modules/content/",
        }

        req = urllib.request.Request(url, headers={"User-Agent": "ArkanFinance/1.0 RSS reader"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()

        root = ET.fromstring(raw)

        # Support both RSS <item> and Atom <entry>
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        entries: list[dict[str, Any]] = []
        for item in items[:max_items]:
            def get(tag: str, attr: str | None = None) -> str:
                el = item.find(tag)
                if el is None:
                    return ""
                if attr:
                    return el.get(attr, "")
                return el.text or ""

            title   = _clean(get("title") or get("{http://www.w3.org/2005/Atom}title"))
            link    = (get("link") or get("guid") or
                       item.findtext("{http://www.w3.org/2005/Atom}link") or
                       (item.find("{http://www.w3.org/2005/Atom}link") or {}).get("href", ""))
            summary = _clean(
                get("description") or
                get("{http://purl.org/rss/1.0/modules/content/}encoded") or
                get("{http://www.w3.org/2005/Atom}summary") or
                get("{http://www.w3.org/2005/Atom}content")
            )
            pub = get("pubDate") or get("{http://www.w3.org/2005/Atom}published") or get("{http://www.w3.org/2005/Atom}updated")

            if title:
                entries.append({
                    "title":     title,
                    "link":      link,
                    "summary":   summary[:400],
                    "published": pub,
                })
        return entries

    def fetch_all(self, limit: int = 60, category: str = "all") -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []

        for source in SOURCES:
            if category != "all" and source["category"] != category:
                continue
            try:
                entries = self._parse_rss(source["url"])
                for entry in entries:
                    articles.append({
                        **entry,
                        "source":   source["name"],
                        "category": source["category"],
                        "image":    None,
                    })
            except Exception as exc:
                logger.warning("news fetch failed for %s: %s", source["name"], exc)

        # Deduplicate by title prefix
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for art in articles:
            key = art["title"][:60].lower()
            if key not in seen:
                seen.add(key)
                unique.append(art)

        unique.sort(key=lambda x: x["published"], reverse=True)
        return unique[:limit]

    def get_hot(self) -> dict[str, Any]:
        articles = self.fetch_all(limit=120)

        # Count word/ticker frequency across all headlines + summaries
        word_counts: Counter = Counter()
        ticker_re = re.compile(r"\b([A-Z]{2,5})\b")

        for art in articles:
            text = art["title"].upper() + " " + art["summary"].upper()
            # Generic financial keywords
            for kw in FINANCIAL_KEYWORDS:
                if kw in text:
                    word_counts[kw] += 1
            # Short uppercase tokens that look like tickers
            for match in ticker_re.findall(art["title"].upper()):
                if match not in {"THE", "AND", "FOR", "ARE", "BUT", "NOT",
                                 "YOU", "ALL", "CAN", "HER", "WAS", "ONE",
                                 "OUR", "OUT", "WHO", "ITS", "HOW", "HAS",
                                 "HAD", "GET", "MAY", "NEW", "NOW", "WAY",
                                 "WITH", "THIS", "FROM", "THAT", "THEY",
                                 "WILL", "BEEN", "HAVE", "WHAT", "WERE",
                                 "SAYS", "SAID", "AFTER", "ABOUT", "INTO"}:
                    word_counts[match] += 2  # headline mentions weight more

        trending = [
            {"keyword": kw, "count": cnt}
            for kw, cnt in word_counts.most_common(25)
        ]

        # Top articles with engagement score (headline mention of trending word)
        top_keywords = {t["keyword"] for t in trending[:10]}
        scored: list[dict[str, Any]] = []
        for art in articles:
            text_upper = art["title"].upper()
            score = sum(1 for kw in top_keywords if kw in text_upper)
            scored.append({**art, "hot_score": score})

        scored.sort(key=lambda x: x["hot_score"], reverse=True)

        return {
            "trending_topics": trending,
            "hot_articles":    scored[:20],
        }

    def get_by_symbol(self, symbol: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return articles mentioning a specific ticker symbol."""
        all_articles = self.fetch_all(limit=120)
        sym = symbol.upper()
        return [
            art for art in all_articles
            if sym in art["title"].upper() or sym in art["summary"].upper()
        ][:limit]

