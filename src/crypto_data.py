# src/crypto_data.py

import requests
import pandas as pd
import streamlit as st


COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


MEMECOIN_IDS = [
    "dogecoin",
    "shiba-inu",
    "pepe",
    "bonk",
    "dogwifcoin",
    "floki",
    "brett",
    "mog-coin",
    "popcat",
]


BLUECHIP_CRYPTO_IDS = [
    "bitcoin",
    "ethereum",
    "solana",
    "binancecoin",
    "ripple",
    "cardano",
    "avalanche-2",
    "chainlink",
    "polkadot",
    "near",
]


def _safe_get(url, params=None, timeout=15):
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=5 * 60)
def get_crypto_markets(
    vs_currency="usd",
    per_page=100,
    page=1,
    category=None,
):
    """
    Henter crypto market data fra CoinGecko.
    """
    url = f"{COINGECKO_BASE_URL}/coins/markets"

    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    }

    if category:
        params["category"] = category

    data = _safe_get(url, params=params)

    if not data:
        return pd.DataFrame()

    rows = []

    for coin in data:
        rows.append(
            {
                "ID": coin.get("id"),
                "Symbol": str(coin.get("symbol", "")).upper(),
                "Navn": coin.get("name"),
                "Pris": coin.get("current_price"),
                "Market Cap": coin.get("market_cap"),
                "Market Cap Rank": coin.get("market_cap_rank"),
                "Volumen 24h": coin.get("total_volume"),
                "Ændring 1h (%)": coin.get("price_change_percentage_1h_in_currency"),
                "Ændring 24h (%)": coin.get("price_change_percentage_24h"),
                "Ændring 7d (%)": coin.get("price_change_percentage_7d_in_currency"),
                "ATH": coin.get("ath"),
                "ATH ændring (%)": coin.get("ath_change_percentage"),
                "Image": coin.get("image"),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=5 * 60)
def get_selected_crypto_markets(coin_ids, vs_currency="usd"):
    """
    Henter data for specifikke crypto IDs.
    """
    if not coin_ids:
        return pd.DataFrame()

    url = f"{COINGECKO_BASE_URL}/coins/markets"

    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    }

    data = _safe_get(url, params=params)

    if not data:
        return pd.DataFrame()

    rows = []

    for coin in data:
        rows.append(
            {
                "ID": coin.get("id"),
                "Symbol": str(coin.get("symbol", "")).upper(),
                "Navn": coin.get("name"),
                "Pris": coin.get("current_price"),
                "Market Cap": coin.get("market_cap"),
                "Market Cap Rank": coin.get("market_cap_rank"),
                "Volumen 24h": coin.get("total_volume"),
                "Ændring 1h (%)": coin.get("price_change_percentage_1h_in_currency"),
                "Ændring 24h (%)": coin.get("price_change_percentage_24h"),
                "Ændring 7d (%)": coin.get("price_change_percentage_7d_in_currency"),
                "ATH": coin.get("ath"),
                "ATH ændring (%)": coin.get("ath_change_percentage"),
                "Image": coin.get("image"),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=10 * 60)
def get_trending_crypto():
    """
    Henter trending coins fra CoinGecko.
    """
    url = f"{COINGECKO_BASE_URL}/search/trending"

    data = _safe_get(url)

    if not data:
        return pd.DataFrame()

    coins = data.get("coins", [])
    rows = []

    for item in coins:
        coin = item.get("item", {})

        rows.append(
            {
                "ID": coin.get("id"),
                "Symbol": str(coin.get("symbol", "")).upper(),
                "Navn": coin.get("name"),
                "Market Cap Rank": coin.get("market_cap_rank"),
                "Score": coin.get("score"),
                "Pris BTC": coin.get("price_btc"),
            }
        )

    return pd.DataFrame(rows)


def calculate_crypto_risk_score(row):
    """
    Simpel crypto risk-score.
    Højere score = højere risiko.
    """
    risk = 0

    market_cap = row.get("Market Cap") or 0
    volume = row.get("Volumen 24h") or 0
    change_24h = row.get("Ændring 24h (%)") or 0
    change_7d = row.get("Ændring 7d (%)") or 0
    rank = row.get("Market Cap Rank") or 9999

    # Lille market cap = højere risiko
    if market_cap < 50_000_000:
        risk += 30
    elif market_cap < 250_000_000:
        risk += 20
    elif market_cap < 1_000_000_000:
        risk += 10

    # Ekstreme prisbevægelser
    if abs(change_24h) > 30:
        risk += 25
    elif abs(change_24h) > 15:
        risk += 15
    elif abs(change_24h) > 8:
        risk += 8

    if abs(change_7d) > 80:
        risk += 25
    elif abs(change_7d) > 40:
        risk += 15

    # Lav rank = mindre risiko, høj rank = højere risiko
    if rank > 500:
        risk += 20
    elif rank > 200:
        risk += 10

    # Lav volumen ift. market cap kan være problem
    if market_cap and volume:
        vol_to_mc = volume / market_cap

        if vol_to_mc < 0.01:
            risk += 15
        elif vol_to_mc > 1:
            risk += 10

    risk = max(0, min(100, round(risk, 1)))

    if risk >= 75:
        label = "Meget høj risiko"
    elif risk >= 55:
        label = "Høj risiko"
    elif risk >= 35:
        label = "Moderat risiko"
    else:
        label = "Lavere relativ risiko"

    return risk, label


def calculate_crypto_research_score(row):
    """
    Research-score for crypto.
    Ikke en købsanbefaling.
    """
    score = 0

    change_1h = row.get("Ændring 1h (%)") or 0
    change_24h = row.get("Ændring 24h (%)") or 0
    change_7d = row.get("Ændring 7d (%)") or 0
    market_cap = row.get("Market Cap") or 0
    volume = row.get("Volumen 24h") or 0

    # Momentum
    if change_24h > 20:
        score += 25
    elif change_24h > 10:
        score += 18
    elif change_24h > 3:
        score += 10

    if change_7d > 50:
        score += 20
    elif change_7d > 20:
        score += 12
    elif change_7d > 5:
        score += 6

    # Kort momentum
    if change_1h > 5:
        score += 10
    elif change_1h > 2:
        score += 5

    # Likviditet
    if market_cap and volume:
        vol_to_mc = volume / market_cap

        if 0.05 <= vol_to_mc <= 0.5:
            score += 20
        elif vol_to_mc > 0.5:
            score += 10
        elif vol_to_mc < 0.01:
            score -= 15

    # Market cap filter
    if market_cap > 1_000_000_000:
        score += 15
    elif market_cap > 250_000_000:
        score += 10
    elif market_cap < 25_000_000:
        score -= 20

    risk_score, _ = calculate_crypto_risk_score(row)

    # Straf for meget høj risiko
    if risk_score >= 75:
        score -= 25
    elif risk_score >= 55:
        score -= 12

    score = max(0, min(100, round(score, 1)))

    if score >= 75:
        label = "Stærk research-kandidat"
    elif score >= 60:
        label = "Interessant momentum-kandidat"
    elif score >= 45:
        label = "Overvåg"
    elif score >= 30:
        label = "Svag kandidat"
    else:
        label = "Lav prioritet"

    return score, label
