# src/news_fetcher.py

import hashlib
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import feedparser
import pandas as pd
import requests
import streamlit as st

try:
    from config import RSS_FEEDS, DEFAULT_WATCHLIST
except Exception:
    RSS_FEEDS = []
    DEFAULT_WATCHLIST = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_secret(name, default=None):
    """
    Henter Streamlit secret uden at crashe lokalt.
    """
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _safe_get(url, params=None, headers=None, timeout=15):
    """
    Simpel requests wrapper.
    """
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return response
    except Exception:
        return None


def _normalize_date(value):
    """
    Returnerer dato som string.
    """
    if not value:
        return ""

    try:
        if isinstance(value, str):
            return value[:19].replace("T", " ")
        return str(value)
    except Exception:
        return ""


def _make_news_id(title, url):
    """
    Bruges til deduplication.
    """
    raw = f"{title}|{url}".lower().strip()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _clean_text(text):
    if not text:
        return ""
    return str(text).replace("\n", " ").replace("\r", " ").strip()


def _standard_news_item(
    title,
    source,
    url,
    published="",
    summary="",
    raw_text="",
    tickers=None,
    source_type="news",
    credibility="medium",
):
    title = _clean_text(title)
    summary = _clean_text(summary)
    raw_text = _clean_text(raw_text or f"{title} {summary}")

    return {
        "id": _make_news_id(title, url),
        "title": title,
        "source": source,
        "url": url,
        "published": _normalize_date(published),
        "summary": summary,
        "raw_text": raw_text,
        "source_type": source_type,
        "credibility": credibility,
        "source_tickers": tickers or [],
    }


def deduplicate_news(news_items):
    """
    Fjerner dubletter baseret på id/url/title.
    """
    seen = set()
    unique = []

    for item in news_items:
        news_id = item.get("id") or _make_news_id(
            item.get("title", ""),
            item.get("url", ""),
        )

        if news_id in seen:
            continue

        seen.add(news_id)
        unique.append(item)

    return unique


# ─────────────────────────────────────────────────────────────────────────────
# RSS feeds
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=15 * 60)
def fetch_rss_news(max_per_feed=30):
    """
    Henter nyheder fra RSS-feeds.
    """
    news = []

    feeds = RSS_FEEDS or [
        {
            "name": "CNBC Top News",
            "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        },
        {
            "name": "MarketWatch Top Stories",
            "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        },
        {
            "name": "Yahoo Finance",
            "url": "https://finance.yahoo.com/news/rssindex",
        },
    ]

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])

            for entry in parsed.entries[:max_per_feed]:
                title = entry.get("title", "")
                url = entry.get("link", "")
                summary = entry.get("summary", "")
                published = (
                    entry.get("published", "")
                    or entry.get("updated", "")
                )

                if not title or not url:
                    continue

                news.append(
                    _standard_news_item(
                        title=title,
                        source=feed.get("name", "RSS"),
                        url=url,
                        published=published,
                        summary=summary,
                        raw_text=f"{title} {summary}",
                        source_type="rss",
                        credibility="medium",
                    )
                )

        except Exception:
            continue

    return news


# ─────────────────────────────────────────────────────────────────────────────
# GDELT
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=15 * 60)
def fetch_gdelt_news(
    query=None,
    max_records=75,
    timespan="24h",
):
    """
    Henter globale nyheder fra GDELT DOC API.

    GDELT er god til makrotemaer, geopolitik, sektortrends og bred dækning.
    """
    if query is None:
        query = (
            "stock market OR inflation OR interest rates OR Federal Reserve OR "
            "earnings OR oil prices OR AI OR semiconductor OR recession OR banks"
        )

    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "timespan": timespan,
        "sort": "HybridRel",
    }

    response = _safe_get(url, params=params)

    if response is None:
        return []

    try:
        data = response.json()
    except Exception:
        return []

    articles = data.get("articles", [])
    news = []

    for article in articles:
        title = article.get("title", "")
        url_article = article.get("url", "")
        source = article.get("domain", "GDELT")
        published = article.get("seendate", "")
        summary = article.get("snippet", "")

        if not title or not url_article:
            continue

        news.append(
            _standard_news_item(
                title=title,
                source=f"GDELT / {source}",
                url=url_article,
                published=published,
                summary=summary,
                raw_text=f"{title} {summary}",
                source_type="gdelt",
                credibility="medium",
            )
        )

    return news


# ─────────────────────────────────────────────────────────────────────────────
# Finnhub
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=15 * 60)
def fetch_finnhub_market_news(category="general", max_items=50):
    """
    Henter generelle markedsnyheder fra Finnhub.
    Kræver FINNHUB_API_KEY.
    """
    api_key = _get_secret("FINNHUB_API_KEY")

    if not api_key:
        return []

    url = "https://finnhub.io/api/v1/news"

    params = {
        "category": category,
        "token": api_key,
    }

    response = _safe_get(url, params=params)

    if response is None:
        return []

    try:
        data = response.json()
    except Exception:
        return []

    news = []

    for item in data[:max_items]:
        title = item.get("headline", "")
        url_item = item.get("url", "")
        summary = item.get("summary", "")
        source = item.get("source", "Finnhub")
        timestamp = item.get("datetime")

        if timestamp:
            published = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            published = ""

        if not title or not url_item:
            continue

        news.append(
            _standard_news_item(
                title=title,
                source=f"Finnhub / {source}",
                url=url_item,
                published=published,
                summary=summary,
                raw_text=f"{title} {summary}",
                source_type="finnhub_market",
                credibility="high",
            )
        )

    return news


@st.cache_data(ttl=30 * 60)
def fetch_finnhub_company_news(tickers=None, days_back=3, max_per_ticker=10):
    """
    Henter selskabsspecifikke nyheder fra Finnhub.
    Kræver FINNHUB_API_KEY.
    """
    api_key = _get_secret("FINNHUB_API_KEY")

    if not api_key:
        return []

    tickers = tickers or DEFAULT_WATCHLIST[:20]

    to_date = datetime.utcnow().date()
    from_date = to_date - timedelta(days=days_back)

    all_news = []

    for ticker in tickers:
        url = "https://finnhub.io/api/v1/company-news"

        params = {
            "symbol": ticker,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "token": api_key,
        }

        response = _safe_get(url, params=params)

        if response is None:
            continue

        try:
            data = response.json()
        except Exception:
            continue

        for item in data[:max_per_ticker]:
            title = item.get("headline", "")
            url_item = item.get("url", "")
            summary = item.get("summary", "")
            source = item.get("source", "Finnhub")
            timestamp = item.get("datetime")

            if timestamp:
                published = datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc,
                ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                published = ""

            if not title or not url_item:
                continue

            all_news.append(
                _standard_news_item(
                    title=title,
                    source=f"Finnhub Company / {source}",
                    url=url_item,
                    published=published,
                    summary=summary,
                    raw_text=f"{title} {summary}",
                    tickers=[ticker],
                    source_type="finnhub_company",
                    credibility="high",
                )
            )

        # skån gratis API-limits
        time.sleep(0.05)

    return all_news


# ─────────────────────────────────────────────────────────────────────────────
# Alpha Vantage News Sentiment
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30 * 60)
def fetch_alpha_vantage_news(tickers=None, limit=100):
    """
    Henter news sentiment fra Alpha Vantage.
    Kræver ALPHA_VANTAGE_API_KEY.
    """
    api_key = _get_secret("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        return []

    tickers = tickers or DEFAULT_WATCHLIST[:10]
    ticker_string = ",".join(tickers[:25])

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker_string,
        "limit": limit,
        "apikey": api_key,
    }

    response = _safe_get(url, params=params)

    if response is None:
        return []

    try:
        data = response.json()
    except Exception:
        return []

    feed = data.get("feed", [])
    news = []

    for item in feed:
        title = item.get("title", "")
        url_item = item.get("url", "")
        source = item.get("source", "Alpha Vantage")
        published = item.get("time_published", "")
        summary = item.get("summary", "")

        ticker_sentiment = item.get("ticker_sentiment", [])
        item_tickers = [
            ts.get("ticker")
            for ts in ticker_sentiment
            if ts.get("ticker")
        ]

        if not title or not url_item:
            continue

        news_item = _standard_news_item(
            title=title,
            source=f"Alpha Vantage / {source}",
            url=url_item,
            published=published,
            summary=summary,
            raw_text=f"{title} {summary}",
            tickers=item_tickers,
            source_type="alpha_vantage",
            credibility="high",
        )

        news_item["alpha_overall_sentiment_score"] = item.get(
            "overall_sentiment_score"
        )
        news_item["alpha_overall_sentiment_label"] = item.get(
            "overall_sentiment_label"
        )
        news_item["alpha_ticker_sentiment"] = ticker_sentiment

        news.append(news_item)

    return news


# ─────────────────────────────────────────────────────────────────────────────
# SEC EDGAR latest filings
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30 * 60)
def fetch_sec_latest_filings(max_items=50):
    """
    Henter seneste SEC-filings via company_tickers + submissions er tungt,
    så denne simple version bruger SEC's recent submissions RSS.
    """
    sec_feeds = [
        {
            "name": "SEC Latest 8-K",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&count=100&output=atom",
        },
        {
            "name": "SEC Latest 10-Q",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-Q&count=100&output=atom",
        },
        {
            "name": "SEC Latest 10-K",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-K&count=100&output=atom",
        },
    ]

    headers = {
        "User-Agent": "StockDashboard/1.0 contact@example.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }

    news = []

    for feed in sec_feeds:
        try:
            response = _safe_get(
                feed["url"],
                headers=headers,
                timeout=15,
            )

            if response is None:
                continue

            parsed = feedparser.parse(response.text)

            for entry in parsed.entries[:max_items]:
                title = entry.get("title", "")
                url = entry.get("link", "")
                summary = entry.get("summary", "")
                published = entry.get("updated", "") or entry.get("published", "")

                if not title or not url:
                    continue

                news.append(
                    _standard_news_item(
                        title=title,
                        source=feed["name"],
                        url=url,
                        published=published,
                        summary=summary,
                        raw_text=f"{title} {summary}",
                        source_type="sec_filing",
                        credibility="official",
                    )
                )

        except Exception:
            continue

    return news


# ─────────────────────────────────────────────────────────────────────────────
# Main fetcher
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=15 * 60)
def fetch_all_news(
    tickers=None,
    include_rss=True,
    include_gdelt=True,
    include_finnhub=True,
    include_alpha_vantage=True,
    include_sec=True,
    max_total=300,
):
    """
    Samlet news fetcher.
    Returnerer deduplikeret liste af nyheder.
    """
    tickers = tickers or DEFAULT_WATCHLIST
    all_news = []

    if include_rss:
        all_news.extend(fetch_rss_news(max_per_feed=40))

    if include_gdelt:
        all_news.extend(
            fetch_gdelt_news(
                max_records=100,
                timespan="24h",
            )
        )

    if include_finnhub:
        all_news.extend(fetch_finnhub_market_news(max_items=50))
        all_news.extend(
            fetch_finnhub_company_news(
                tickers=tickers[:25],
                days_back=3,
                max_per_ticker=8,
            )
        )

    if include_alpha_vantage:
        all_news.extend(
            fetch_alpha_vantage_news(
                tickers=tickers[:25],
                limit=100,
            )
        )

    if include_sec:
        all_news.extend(fetch_sec_latest_filings(max_items=40))

    all_news = deduplicate_news(all_news)

    # Sortér groft efter published-string, hvis muligt
    try:
        all_news = sorted(
            all_news,
            key=lambda x: x.get("published", ""),
            reverse=True,
        )
    except Exception:
        pass

    return all_news[:max_total]
