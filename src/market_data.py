# src/market_data.py — Henter markedsdata via yfinance
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from config import CACHE_TTL_MARKET


@st.cache_data(ttl=CACHE_TTL_MARKET, show_spinner=False)
def get_stock_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    Hent OHLCV-historik for én aktie.
    period: '1d','5d','1mo','3mo','6mo','1y','2y','5y','max'
    """
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        # Flad MultiIndex-kolonner hvis de findes
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.warning(f"Kunne ikke hente historik for {ticker}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_MARKET, show_spinner=False)
def get_ticker_info(ticker: str) -> dict:
    """Hent nøgleinfo for én aktie via yfinance."""
    try:
        t   = yf.Ticker(ticker)
        inf = t.info or {}
        hist = get_stock_history(ticker, period="5d")

        price      = inf.get("currentPrice") or inf.get("regularMarketPrice")
        prev_close = inf.get("previousClose") or inf.get("regularMarketPreviousClose")
        change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close else 0

        return {
            "ticker":       ticker,
            "name":         inf.get("shortName", ticker),
            "sector":       inf.get("sector", "Ukendt"),
            "industry":     inf.get("industry", ""),
            "country":      inf.get("country", ""),
            "price":        price,
            "prev_close":   prev_close,
            "change_pct":   change_pct,
            "volume":       inf.get("volume") or inf.get("regularMarketVolume"),
            "avg_volume":   inf.get("averageVolume"),
            "market_cap":   inf.get("marketCap"),
            "week_52_high": inf.get("fiftyTwoWeekHigh"),
            "week_52_low":  inf.get("fiftyTwoWeekLow"),
            "pe_ratio":     inf.get("trailingPE"),
            "eps":          inf.get("trailingEps"),
            "dividend":     inf.get("dividendYield"),
            "beta":         inf.get("beta"),
            "description":  inf.get("longBusinessSummary", ""),
        }
    except Exception as e:
        return {"ticker": ticker, "name": ticker, "error": str(e)}


@st.cache_data(ttl=CACHE_TTL_MARKET, show_spinner=False)
def get_market_overview(tickers: list) -> pd.DataFrame:
    """
    Hent overbliksdata for en liste af tickers.
    Returnér DataFrame med én række per aktie.
    """
    rows = []
    for ticker in tickers:
        info = get_ticker_info(ticker)
        if "error" in info and "price" not in info:
            continue
        volume     = info.get("volume") or 0
        avg_volume = info.get("avg_volume") or 1
        vol_ratio  = volume / avg_volume if avg_volume else 0

        rows.append({
            "Ticker":          info.get("ticker", ticker),
            "Navn":            info.get("name", ticker),
            "Sektor":          info.get("sector", "Ukendt"),
            "Pris (USD)":      info.get("price"),
            "Ændring (%)":     info.get("change_pct"),
            "Volumen":         volume,
            "Vol/Avg":         round(vol_ratio, 2),
            "Market Cap":      info.get("market_cap"),
            "P/E":             info.get("pe_ratio"),
            "52W High":        info.get("week_52_high"),
            "52W Low":         info.get("week_52_low"),
            "Beta":            info.get("beta"),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Beregn RSI (Relative Strength Index)."""
    delta = prices.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Beregn Simple Moving Average."""
    return prices.rolling(window=period).mean()


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tilføj tekniske indikatorer (SMA, RSI) til en OHLCV-DataFrame."""
    if df.empty or "Close" not in df.columns:
        return df
    df = df.copy()
    close = df["Close"].squeeze()
    for period in [20, 50, 200]:
        df[f"SMA{period}"] = calculate_sma(close, period)
    df["RSI"] = calculate_rsi(close)
    return df


@st.cache_data(ttl=CACHE_TTL_MARKET, show_spinner=False)
def get_top_movers(tickers: list) -> dict:
    """
    Find top-vindere, -tabere og aktier med usædvanlig høj volumen.
    Returnér dict med tre lister.
    """
    overview = get_market_overview(tickers)
    if overview.empty:
        return {"gainers": [], "losers": [], "high_volume": []}

    df = overview.dropna(subset=["Ændring (%)"])

    gainers     = df.nlargest(5,  "Ændring (%)").to_dict("records")
    losers      = df.nsmallest(5, "Ændring (%)").to_dict("records")
    high_volume = df[df["Vol/Avg"] > 1.5].nlargest(5, "Vol/Avg").to_dict("records")

    return {
        "gainers":     gainers,
        "losers":      losers,
        "high_volume": high_volume,
    }


@st.cache_data(ttl=CACHE_TTL_MARKET, show_spinner=False)
def get_ticker_news(ticker: str, max_items: int = 10) -> list:
    """Hent nyheder fra yfinance for en specifik aktie."""
    try:
        t    = yf.Ticker(ticker)
        news = t.news or []
        result = []
        for item in news[:max_items]:
            ct = item.get("content", {})
            result.append({
                "title":     ct.get("title", item.get("title", "Ingen titel")),
                "url":       ct.get("canonicalUrl", {}).get("url", item.get("link", "#")),
                "source":    ct.get("provider", {}).get("displayName", "Yahoo Finance"),
                "published": ct.get("pubDate", item.get("providerPublishTime", "")),
                "summary":   ct.get("summary", item.get("summary", "")),
                "ticker":    ticker,
            })
        return result
    except Exception:
        return []