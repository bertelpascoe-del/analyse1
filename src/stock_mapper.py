# src/stock_mapper.py — Kobler nyheder til berørte aktier
import re
import pandas as pd
from config import COMPANY_ALIASES, SECTOR_TRIGGERS


def load_tickers_df() -> pd.DataFrame:
    """Indlæs tickers fra CSV."""
    try:
        return pd.read_csv("data/tickers.csv")
    except Exception:
        # Minimal fallback
        return pd.DataFrame({
            "ticker": ["AAPL", "MSFT", "NVDA"],
            "name":   ["Apple", "Microsoft", "Nvidia"],
            "sector": ["Technology", "Technology", "Technology"],
        })


def map_news_to_stocks(news_item: dict, tickers_df: pd.DataFrame = None) -> list:
    """
    Find aktier der er berørt af en nyhed.
    Returnér liste af dicts: {ticker, name, reason, impact_type}
    impact_type: 'direkte' | 'indirekte'
    """
    if tickers_df is None:
        tickers_df = load_tickers_df()

    raw_text = (
        news_item.get("raw_text", "") + " " +
        news_item.get("title",    "") + " " +
        news_item.get("summary",  "")
    ).lower()

    results   = {}   # ticker → info

    # ── 1. Eksplicitte tickers i teksten ($AAPL eller "AAPL") ────────────────
    ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|(?<!\w)([A-Z]{2,5})(?!\w)')
    known_tickers  = set(tickers_df["ticker"].str.upper())

    for match in ticker_pattern.finditer(
        news_item.get("raw_text", "") + " " + news_item.get("title", "")
    ):
        candidate = (match.group(1) or match.group(2) or "").upper()
        if candidate in known_tickers:
            row = tickers_df[tickers_df["ticker"].str.upper() == candidate].iloc[0]
            results[candidate] = {
                "ticker":      candidate,
                "name":        row.get("name", candidate),
                "reason":      "Ticker direkte nævnt i nyheden",
                "impact_type": "direkte",
            }

    # Eksplicitte tickers fra Finnhub-feltet
    for t in news_item.get("tickers", []):
        t_upper = t.strip().upper()
        if t_upper and t_upper in known_tickers:
            row = tickers_df[tickers_df["ticker"].str.upper() == t_upper].iloc[0]
            results[t_upper] = {
                "ticker":      t_upper,
                "name":        row.get("name", t_upper),
                "reason":      "Angivet af nyhedskilde",
                "impact_type": "direkte",
            }

    # ── 2. Virksomhedsnavne / aliaser ────────────────────────────────────────
    for alias, ticker in COMPANY_ALIASES.items():
        if ticker and alias in raw_text and ticker not in results:
            if ticker.upper() in known_tickers:
                row = tickers_df[
                    tickers_df["ticker"].str.upper() == ticker.upper()
                ]
                if not row.empty:
                    results[ticker] = {
                        "ticker":      ticker,
                        "name":        row.iloc[0].get("name", ticker),
                        "reason":      f"Virksomhedsnavn '{alias}' fundet",
                        "impact_type": "direkte",
                    }

    # ── 3. Sektortriggers / makronøgleord ────────────────────────────────────
    for keyword, affected_tickers in SECTOR_TRIGGERS.items():
        if keyword in raw_text:
            for t in affected_tickers:
                if t not in results and t.upper() in known_tickers:
                    row = tickers_df[
                        tickers_df["ticker"].str.upper() == t.upper()
                    ]
                    if not row.empty:
                        results[t] = {
                            "ticker":      t,
                            "name":        row.iloc[0].get("name", t),
                            "reason":      f"Sektornøgleord '{keyword}' fundet",
                            "impact_type": "indirekte",
                        }

    return list(results.values())[:10]   # Max 10 per nyhed


def enrich_news_with_stocks(
    news_list: list, tickers_df: pd.DataFrame = None
) -> list:
    """
    Tilføj 'affected_stocks' og 'primary_ticker' til hvert nyhedsemne.
    """
    if tickers_df is None:
        tickers_df = load_tickers_df()

    enriched = []
    for item in news_list:
        affected = map_news_to_stocks(item, tickers_df)
        item["affected_stocks"]  = affected
        item["primary_ticker"]   = affected[0]["ticker"] if affected else None
        item["affected_tickers"] = [s["ticker"] for s in affected]
        enriched.append(item)

    return enriched