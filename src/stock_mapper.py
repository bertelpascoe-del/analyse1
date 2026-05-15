# src/stock_mapper.py

import os
import re
import pandas as pd
import streamlit as st

from config import COMPANY_ALIASES, SECTOR_TRIGGERS, SECTOR_TICKERS


@st.cache_data(ttl=24 * 60 * 60)
def load_tickers_df():
    """
    Loader ticker-data fra data/tickers.csv hvis filen findes.
    Hvis den ikke findes, opbygges en fallback-tabel ud fra config.py.
    """

    possible_paths = [
        "data/tickers.csv",
        os.path.join(os.path.dirname(__file__), "..", "data", "tickers.csv"),
    ]

    for path in possible_paths:
        try:
            if os.path.exists(path):
                df = pd.read_csv(path)

                # Standardiser kolonnenavne
                rename_map = {
                    "ticker": "Ticker",
                    "symbol": "Ticker",
                    "name": "Name",
                    "company": "Name",
                    "sector": "Sector",
                }

                df = df.rename(columns=rename_map)

                if "Ticker" not in df.columns:
                    continue

                if "Name" not in df.columns:
                    df["Name"] = df["Ticker"]

                if "Sector" not in df.columns:
                    df["Sector"] = ""

                df["Ticker"] = df["Ticker"].astype(str).str.upper()

                return df[["Ticker", "Name", "Sector"]].drop_duplicates()

        except Exception:
            continue

    # Fallback hvis CSV ikke findes
    rows = []

    for sector, tickers in SECTOR_TICKERS.items():
        for ticker in tickers:
            rows.append(
                {
                    "Ticker": ticker,
                    "Name": ticker,
                    "Sector": sector,
                }
            )

    # Tilføj aliases fra COMPANY_ALIASES
    for company_name, ticker in COMPANY_ALIASES.items():
        if ticker:
            rows.append(
                {
                    "Ticker": str(ticker).upper(),
                    "Name": company_name.title(),
                    "Sector": "",
                }
            )

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=["Ticker", "Name", "Sector"])

    df["Ticker"] = df["Ticker"].astype(str).str.upper()

    return df[["Ticker", "Name", "Sector"]].drop_duplicates()


def _safe_text(value):
    """
    Konverterer tekstfelt til lowercase string.
    """
    if value is None:
        return ""

    return str(value).lower()


def _extract_direct_tickers(text, known_tickers):
    """
    Finder direkte ticker-symboler i tekst.
    Eksempel: AAPL, MSFT, NVDA.
    """

    found = set()

    if not text:
        return found

    text_upper = str(text).upper()

    for ticker in known_tickers:
        ticker = str(ticker).upper()

        # Undgå meget korte tilfældige matches
        if len(ticker) < 2:
            continue

        pattern = r"\b" + re.escape(ticker) + r"\b"

        if re.search(pattern, text_upper):
            found.add(ticker)

    return found


def _extract_alias_tickers(text):
    """
    Finder tickers ud fra virksomhedsnavne/aliases.
    """

    found = set()
    text_lower = _safe_text(text)

    for alias, ticker in COMPANY_ALIASES.items():
        if not ticker:
            continue

        alias_lower = str(alias).lower()

        if alias_lower in text_lower:
            found.add(str(ticker).upper())

    return found


def _extract_sector_trigger_tickers(text):
    """
    Finder indirekte berørte tickers ud fra sektor-/temaord.
    Eksempel: AI, oil, banks, inflation.
    """

    found = set()
    text_lower = _safe_text(text)

    for keyword, tickers in SECTOR_TRIGGERS.items():
        keyword_lower = str(keyword).lower()

        if keyword_lower in text_lower:
            for ticker in tickers:
                found.add(str(ticker).upper())

    return found


def map_news_to_stocks(news_item, tickers_df):
    """
    Mapper én nyhed til relevante tickers.

    Returnerer:
    - affected_tickers
    - direct_tickers
    - indirect_tickers
    """

    title = news_item.get("title", "")
    summary = news_item.get("summary", "")
    raw_text = news_item.get("raw_text", "")

    combined_text = f"{title} {summary} {raw_text}"

    if tickers_df is not None and not tickers_df.empty and "Ticker" in tickers_df.columns:
        known_tickers = tickers_df["Ticker"].dropna().astype(str).str.upper().unique().tolist()
    else:
        known_tickers = []

    direct_tickers = set()
    indirect_tickers = set()

    direct_tickers.update(_extract_direct_tickers(combined_text, known_tickers))
    direct_tickers.update(_extract_alias_tickers(combined_text))

    indirect_tickers.update(_extract_sector_trigger_tickers(combined_text))

    affected_tickers = sorted(list(direct_tickers.union(indirect_tickers)))

    return {
        "affected_tickers": affected_tickers,
        "direct_tickers": sorted(list(direct_tickers)),
        "indirect_tickers": sorted(list(indirect_tickers - direct_tickers)),
    }


def enrich_news_with_stocks(news_items, tickers_df=None):
    """
    Tilføjer aktie-kobling til hver nyhed.

    Input:
    - news_items: liste af nyheder
    - tickers_df: dataframe med Ticker, Name, Sector

    Output:
    - liste af nyheder med affected_tickers, direct_tickers og indirect_tickers
    """

    if tickers_df is None:
        tickers_df = load_tickers_df()

    enriched = []

    for item in news_items:
        if not isinstance(item, dict):
            continue

        mapped = map_news_to_stocks(item, tickers_df)

        new_item = item.copy()
        new_item["affected_tickers"] = mapped["affected_tickers"]
        new_item["direct_tickers"] = mapped["direct_tickers"]
        new_item["indirect_tickers"] = mapped["indirect_tickers"]

        enriched.append(new_item)

    return enriched
