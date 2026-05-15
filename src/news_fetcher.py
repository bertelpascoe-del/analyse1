# src/news_fetcher.py — Henter nyheder fra RSS-feeds og valgfrie API'er
import feedparser
import requests
import streamlit as st
from datetime import datetime, timezone
import time as time_module
from config import RSS_FEEDS, CACHE_TTL_NEWS

# Fallback-nyheder hvis alle feeds fejler
FALLBACK_NEWS = [
    {
        "title":     "Markedsdata midlertidigt utilgængelig",
        "source":    "System",
        "published": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "url":       "#",
        "summary":   "Nyhedsfeeds er ikke tilgængelige i øjeblikket. "
                     "Tjek din internetforbindelse, eller opdater siden om lidt.",
        "tickers":   [],
        "raw_text":  "",
    }
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; StockDashboard/1.0; "
        "+https://github.com/your-repo)"
    )
}


def _parse_date(entry) -> str:
    """Forsøg at parse dato fra et feedparser-entry."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def fetch_rss_feed(feed_info: dict, timeout: int = 8) -> list:
    """
    Hent og parse ét RSS-feed.
    Returnér liste af normaliserede nyhedsemner.
    """
    items = []
    try:
        resp = requests.get(
            feed_info["url"], headers=HEADERS, timeout=timeout
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:15]:
            title   = getattr(entry, "title",   "Ingen titel")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            # Rens HTML fra summary
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            link    = getattr(entry, "link", "#")

            items.append({
                "title":     title,
                "source":    feed_info["name"],
                "published": _parse_date(entry),
                "url":       link,
                "summary":   summary[:500],
                "raw_text":  f"{title} {summary}",
                "tickers":   [],   # Udfyldes af stock_mapper
            })
    except requests.exceptions.Timeout:
        pass   # Feed timeout — ignorer stille
    except Exception:
        pass   # Andet fejl — ignorer stille

    return items


@st.cache_data(ttl=CACHE_TTL_NEWS, show_spinner=False)
def fetch_all_rss_news() -> list:
    """Hent nyheder fra alle konfigurerede RSS-feeds."""
    all_news = []
    for feed_info in RSS_FEEDS:
        items = fetch_rss_feed(feed_info)
        all_news.extend(items)
        time_module.sleep(0.2)   # Respektér rate limits

    # Dedupliker på titel
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title_key = item["title"].strip().lower()[:80]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(item)

    return unique_news if unique_news else FALLBACK_NEWS


@st.cache_data(ttl=CACHE_TTL_NEWS, show_spinner=False)
def fetch_newsapi_news(query: str = "stock market", page_size: int = 20) -> list:
    """
    Valgfrit: Hent nyheder fra NewsAPI (kræver NEWS_API_KEY i Streamlit Secrets).
    """
    try:
        api_key = st.secrets.get("NEWS_API_KEY", "")
        if not api_key:
            return []
        url    = "https://newsapi.org/v2/everything"
        params = {
            "q":        query,
            "language": "en",
            "sortBy":   "publishedAt",
            "pageSize": page_size,
            "apiKey":   api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title":    a.get("title",       "Ingen titel"),
                "source":   a.get("source", {}).get("name", "NewsAPI"),
                "published": a.get("publishedAt", "")[:16].replace("T", " "),
                "url":       a.get("url",         "#"),
                "summary":   a.get("description", "") or a.get("content", ""),
                "raw_text":  f"{a.get('title','')} {a.get('description','')}",
                "tickers":   [],
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception:
        return []


@st.cache_data(ttl=CACHE_TTL_NEWS, show_spinner=False)
def fetch_finnhub_market_news(category: str = "general") -> list:
    """
    Valgfrit: Hent nyheder fra Finnhub (kræver FINNHUB_API_KEY i Streamlit Secrets).
    """
    try:
        api_key = st.secrets.get("FINNHUB_API_KEY", "")
        if not api_key:
            return []
        url    = "https://finnhub.io/api/v1/news"
        params = {"category": category, "token": api_key}
        resp   = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json()
        return [
            {
                "title":     a.get("headline", "Ingen titel"),
                "source":    a.get("source",   "Finnhub"),
                "published": datetime.fromtimestamp(
                    a.get("datetime", 0), tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M"),
                "url":       a.get("url",     "#"),
                "summary":   a.get("summary", ""),
                "raw_text":  f"{a.get('headline','')} {a.get('summary','')}",
                "tickers":   a.get("related", "").split(",") if a.get("related") else [],
            }
            for a in articles
        ]
    except Exception:
        return []


def fetch_all_news() -> list:
    """
    Kombiner alle nyhedskilder.
    Rangér: Finnhub > NewsAPI > RSS.
    Returnér en samlet, deduplikeret liste.
    """
    rss_news     = fetch_all_rss_news()
    newsapi_news = fetch_newsapi_news()
    finnhub_news = fetch_finnhub_market_news()

    combined   = finnhub_news + newsapi_news + rss_news
    seen       = set()
    deduplicated = []
    for item in combined:
        key = item.get("title", "").strip().lower()[:80]
        if key and key not in seen:
            seen.add(key)
            deduplicated.append(item)

    return deduplicated[:80] if deduplicated else FALLBACK_NEWS