# pages/6_Crypto_Memecoin_Scanner.py

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.crypto_data import (
    get_crypto_markets,
    get_selected_crypto_markets,
    get_trending_crypto,
    calculate_crypto_risk_score,
    calculate_crypto_research_score,
    MEMECOIN_IDS,
    BLUECHIP_CRYPTO_IDS,
)
from src.utils import format_number, format_percent


st.set_page_config(
    page_title="Crypto & Memecoin Scanner",
    page_icon="🪙",
    layout="wide",
)

st.title("🪙 Crypto & Memecoin Scanner")
st.caption(
    "Scanner crypto-markedet for momentum, volumen, risiko og research-kandidater. "
    "Dette er ikke finansiel rådgivning."
)


with st.sidebar:
    st.header("Indstillinger")

    universe = st.selectbox(
        "Vælg univers",
        [
            "Top crypto market",
            "Memecoins",
            "Bluechip crypto",
            "Custom CoinGecko IDs",
        ],
    )

    per_page = st.slider(
        "Antal coins",
        min_value=25,
        max_value=250,
        value=100,
        step=25,
    )

    custom_ids = ""

    if universe == "Custom CoinGecko IDs":
        custom_ids = st.text_area(
            "CoinGecko IDs",
            value="bitcoin,ethereum,solana,dogecoin,pepe",
            help="Brug CoinGecko IDs, fx bitcoin, ethereum, dogecoin, pepe.",
        )

    min_volume = st.number_input(
        "Min. 24h volumen USD",
        min_value=0,
        value=1_000_000,
        step=500_000,
    )

    min_market_cap = st.number_input(
        "Min. market cap USD",
        min_value=0,
        value=10_000_000,
        step=5_000_000,
    )

    sort_col = st.selectbox(
        "Sorter efter",
        [
            "Research-score",
            "Ændring 24h (%)",
            "Ændring 7d (%)",
            "Volumen 24h",
            "Market Cap",
            "Risk-score",
        ],
    )

    if st.button("🔄 Opdater crypto-data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Hent data ────────────────────────────────────────────────────────────────
if universe == "Top crypto market":
    df = get_crypto_markets(per_page=per_page)

elif universe == "Memecoins":
    df = get_selected_crypto_markets(MEMECOIN_IDS)

elif universe == "Bluechip crypto":
    df = get_selected_crypto_markets(BLUECHIP_CRYPTO_IDS)

elif universe == "Custom CoinGecko IDs":
    ids = [
        x.strip().lower()
        for x in custom_ids.replace("\n", ",").split(",")
        if x.strip()
    ]
    df = get_selected_crypto_markets(ids)

else:
    df = get_crypto_markets(per_page=per_page)


if df.empty:
    st.warning("Ingen crypto-data fundet. Prøv et andet univers eller færre coins.")
    st.stop()


# ── Beregn scores ────────────────────────────────────────────────────────────
risk_scores = []
risk_labels = []
research_scores = []
research_labels = []

for _, row in df.iterrows():
    risk_score, risk_label = calculate_crypto_risk_score(row)
    research_score, research_label = calculate_crypto_research_score(row)

    risk_scores.append(risk_score)
    risk_labels.append(risk_label)
    research_scores.append(research_score)
    research_labels.append(research_label)

df["Risk-score"] = risk_scores
df["Risiko"] = risk_labels
df["Research-score"] = research_scores
df["Research-vurdering"] = research_labels


# ── Filtre ───────────────────────────────────────────────────────────────────
df = df[
    (df["Volumen 24h"].fillna(0) >= min_volume)
    &
    (df["Market Cap"].fillna(0) >= min_market_cap)
]

if df.empty:
    st.warning("Ingen coins matcher filtrene.")
    st.stop()


if sort_col in df.columns:
    df = df.sort_values(sort_col, ascending=False)


# ── KPI ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Crypto-overblik")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Coins vist", len(df))
col2.metric("Gns. 24h ændring", format_percent(df["Ændring 24h (%)"].mean()))
col3.metric("Gns. risk-score", f"{df['Risk-score'].mean():.1f}")
col4.metric("Gns. research-score", f"{df['Research-score'].mean():.1f}")


# ── Trending ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔥 Trending crypto på CoinGecko")

trending = get_trending_crypto()

if not trending.empty:
    st.dataframe(
        trending,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Kunne ikke hente trending crypto-data.")


# ── Research-kandidater ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔎 Crypto research-kandidater")

top_research = df.sort_values("Research-score", ascending=False).head(25)

display_research = top_research.copy()

display_research["Pris"] = display_research["Pris"].apply(
    lambda x: f"${x:,.8f}" if pd.notna(x) and x < 1 else f"${x:,.2f}" if pd.notna(x) else "N/A"
)
display_research["Market Cap"] = display_research["Market Cap"].apply(format_number)
display_research["Volumen 24h"] = display_research["Volumen 24h"].apply(format_number)
display_research["Ændring 1h (%)"] = display_research["Ændring 1h (%)"].apply(format_percent)
display_research["Ændring 24h (%)"] = display_research["Ændring 24h (%)"].apply(format_percent)
display_research["Ændring 7d (%)"] = display_research["Ændring 7d (%)"].apply(format_percent)

st.dataframe(
    display_research[
        [
            "Symbol",
            "Navn",
            "Pris",
            "Market Cap",
            "Volumen 24h",
            "Ændring 1h (%)",
            "Ændring 24h (%)",
            "Ændring 7d (%)",
            "Risk-score",
            "Risiko",
            "Research-score",
            "Research-vurdering",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.warning(
    "Research-score er ikke en købsanbefaling. Crypto og især memecoins kan være ekstremt volatile, "
    "illikvide og påvirket af hype, whales og sociale medier."
)


# ── Top movers ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ Crypto top movers")

col_g, col_l = st.columns(2)

with col_g:
    st.markdown("### 🟢 Største 24h stigninger")
    gainers = df.sort_values("Ændring 24h (%)", ascending=False).head(15).copy()

    gainers["Ændring 24h (%)"] = gainers["Ændring 24h (%)"].apply(format_percent)
    gainers["Market Cap"] = gainers["Market Cap"].apply(format_number)
    gainers["Volumen 24h"] = gainers["Volumen 24h"].apply(format_number)

    st.dataframe(
        gainers[
            [
                "Symbol",
                "Navn",
                "Ændring 24h (%)",
                "Market Cap",
                "Volumen 24h",
                "Risk-score",
                "Risiko",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with col_l:
    st.markdown("### 🔴 Største 24h fald")
    losers = df.sort_values("Ændring 24h (%)", ascending=True).head(15).copy()

    losers["Ændring 24h (%)"] = losers["Ændring 24h (%)"].apply(format_percent)
    losers["Market Cap"] = losers["Market Cap"].apply(format_number)
    losers["Volumen 24h"] = losers["Volumen 24h"].apply(format_number)

    st.dataframe(
        losers[
            [
                "Symbol",
                "Navn",
                "Ændring 24h (%)",
                "Market Cap",
                "Volumen 24h",
                "Risk-score",
                "Risiko",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# ── Alle resultater ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 Alle crypto-resultater — {len(df)} coins")

df_display = df.copy()

df_display["Pris"] = df_display["Pris"].apply(
    lambda x: f"${x:,.8f}" if pd.notna(x) and x < 1 else f"${x:,.2f}" if pd.notna(x) else "N/A"
)
df_display["Market Cap"] = df_display["Market Cap"].apply(format_number)
df_display["Volumen 24h"] = df_display["Volumen 24h"].apply(format_number)
df_display["Ændring 1h (%)"] = df_display["Ændring 1h (%)"].apply(format_percent)
df_display["Ændring 24h (%)"] = df_display["Ændring 24h (%)"].apply(format_percent)
df_display["Ændring 7d (%)"] = df_display["Ændring 7d (%)"].apply(format_percent)

try:
    st.dataframe(
        df_display.style
        .background_gradient(subset=["Research-score"], cmap="Greens")
        .background_gradient(subset=["Risk-score"], cmap="Reds"),
        use_container_width=True,
        hide_index=True,
    )
except Exception:
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )
