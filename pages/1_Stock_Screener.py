# pages/1_Stock_Screener.py — Aktiescreener

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import SECTOR_TICKERS, DEFAULT_WATCHLIST, DISCLAIMER
from src.market_data import get_market_overview
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.scoring import calculate_scores, calculate_research_candidate_score
from src.utils import format_percent, format_number


st.set_page_config(
    page_title="Aktiescreener",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Aktiescreener")
st.caption(DISCLAIMER)


# ── Hjælpefunktioner ──────────────────────────────────────────────────────────
@st.cache_data(ttl=24 * 60 * 60)
def get_sp500_tickers():
    """
    Henter S&P 500 tickers fra Wikipedia.
    Yahoo Finance bruger '-' i stedet for '.' for enkelte tickers.
    Eksempel: BRK.B -> BRK-B
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]

        tickers = df["Symbol"].dropna().astype(str).tolist()
        tickers = [ticker.replace(".", "-") for ticker in tickers]

        return sorted(list(set(tickers)))

    except Exception as e:
        st.sidebar.warning(
            "Kunne ikke hente S&P 500-listen. Bruger standardlisten i stedet."
        )
        return DEFAULT_WATCHLIST


def get_sector_tickers(selected_sectors):
    """
    Returnerer tickers fra valgte sektorer.
    """
    tickers = []

    for sector in selected_sectors:
        tickers.extend(SECTOR_TICKERS.get(sector, []))

    return sorted(list(set(tickers)))


def parse_custom_tickers(text):
    """
    Parser custom tickers fra tekstfelt.
    Accepterer komma, mellemrum og linjeskift.
    """
    if not text:
        return []

    cleaned = (
        text.replace("\n", ",")
        .replace(" ", ",")
        .replace(";", ",")
    )

    tickers = [
        ticker.strip().upper()
        for ticker in cleaned.split(",")
        if ticker.strip()
    ]

    return sorted(list(set(tickers)))


# ── Sidebar filtre ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtre")

    universe_choice = st.selectbox(
        "Vælg aktieunivers",
        [
            "Sektorer",
            "S&P 500",
            "Sektorer + S&P 500",
            "Standard watchlist",
            "Custom tickers",
        ],
        index=1,
    )

    selected_sectors = []

    if universe_choice in ["Sektorer", "Sektorer + S&P 500"]:
        selected_sectors = st.multiselect(
            "Sektor",
            options=list(SECTOR_TICKERS.keys()),
            default=list(SECTOR_TICKERS.keys()),
        )

    custom_text = ""

    if universe_choice == "Custom tickers":
        custom_text = st.text_area(
            "Indsæt tickers",
            value="AAPL, MSFT, NVDA, TSLA, AMZN",
            help="Skriv tickers separeret med komma, mellemrum eller linjeskift.",
        )

    max_stocks = st.slider(
        "Maks antal aktier at scanne",
        min_value=25,
        max_value=500,
        value=150,
        step=25,
        help="Jo flere aktier, jo længere tid tager det at hente data.",
    )

    min_change, max_change = st.slider(
        "Daglig ændring (%)",
        -20.0,
        20.0,
        (-20.0, 20.0),
        step=0.5,
    )

    min_vol_ratio = st.slider(
        "Min. volumen ift. gennemsnit (x)",
        0.0,
        5.0,
        0.0,
        0.1,
    )

    sort_col = st.selectbox(
        "Sorter efter",
        [
            "Research-score",
            "Ændring (%)",
            "Købsinteresse",
            "Salgspres",
            "Opmærksomhed",
            "Vol/Avg",
            "Nyheder",
        ],
    )

    sort_asc = st.checkbox("Stigende rækkefølge", value=False)

    if st.button("🔄 Opdater data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Byg ticker-univers ────────────────────────────────────────────────────────
sector_tickers = get_sector_tickers(selected_sectors)
sp500_tickers = get_sp500_tickers()

if universe_choice == "Sektorer":
    selected_tickers = sector_tickers

elif universe_choice == "S&P 500":
    selected_tickers = sp500_tickers

elif universe_choice == "Sektorer + S&P 500":
    selected_tickers = sorted(list(set(sector_tickers + sp500_tickers)))

elif universe_choice == "Standard watchlist":
    selected_tickers = DEFAULT_WATCHLIST

elif universe_choice == "Custom tickers":
    selected_tickers = parse_custom_tickers(custom_text)

else:
    selected_tickers = DEFAULT_WATCHLIST


selected_tickers = sorted(list(set(selected_tickers)))

if not selected_tickers:
    st.info("Ingen tickers valgt. Vælg et aktieunivers eller indsæt custom tickers.")
    st.stop()


# Begræns antal aktier, så appen ikke bliver for langsom
selected_tickers = selected_tickers[:max_stocks]

st.info(
    f"Scanner **{len(selected_tickers)} aktier** fra universet: **{universe_choice}**."
)


# ── Hent data ─────────────────────────────────────────────────────────────────
tickers_df = load_tickers_df()

with st.spinner(f"Henter markedsdata for {len(selected_tickers)} aktier…"):
    overview = get_market_overview(selected_tickers)

if overview.empty:
    st.warning("Ingen markedsdata fundet. Prøv færre tickers eller et andet univers.")
    st.stop()

with st.spinner("Henter og analyserer nyheder…"):
    raw_news = fetch_all_news()

    for item in raw_news:
        item["sentiment"] = analyze_sentiment(item.get("raw_text", ""))

    news = enrich_news_with_stocks(raw_news, tickers_df)


# ── Byg screener-tabel ────────────────────────────────────────────────────────
rows = []

for _, row in overview.iterrows():
    ticker = row["Ticker"]
    change = row.get("Ændring (%)", 0) or 0
    vol_r = row.get("Vol/Avg", 0) or 0

    if not (min_change <= change <= max_change):
        continue

    if vol_r < min_vol_ratio:
        continue

    ticker_info = {
        "change_pct": change,
        "volume": row.get("Volumen"),
        "avg_volume": (
            row.get("Volumen") / vol_r
            if vol_r and vol_r > 0
            else None
        ),
    }

    rel_news = [
        n for n in news
        if ticker in n.get("affected_tickers", [])
    ]

    scores = calculate_scores(ticker_info, rel_news)
    research = calculate_research_candidate_score(row, scores)

    rows.append(
        {
            "Ticker": ticker,
            "Navn": row.get("Navn", ticker),
            "Sektor": row.get("Sektor", ""),
            "Pris (USD)": row.get("Pris (USD)"),
            "Ændring (%)": change,
            "Vol/Avg": vol_r,
            "Market Cap": row.get("Market Cap"),
            "Beta": row.get("Beta"),
            "Købsinteresse": scores["buy_score"],
            "Salgspres": scores["sell_score"],
            "Opmærksomhed": scores["attention_score"],
            "Research-score": research["research_score"],
            "Research-vurdering": research["research_label"],
            "Status": scores["label"],
            "Nyheder": len(rel_news),
        }
    )


if not rows:
    st.warning("Ingen aktier matcher de valgte filtre.")
    st.stop()

df = pd.DataFrame(rows)


# ── Sortering ─────────────────────────────────────────────────────────────────
if sort_col in df.columns:
    df = df.sort_values(sort_col, ascending=sort_asc)


# ── KPI'er ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Screener-overblik")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Aktier vist", len(df))
col2.metric("Gns. ændring", format_percent(df["Ændring (%)"].mean()))
col3.metric("Gns. købsinteresse", f"{df['Købsinteresse'].mean():.1f}")
col4.metric("Gns. research-score", f"{df['Research-score'].mean():.1f}")


# ── Research-kandidater ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔎 Potentielle research-kandidater")

top_research = df.sort_values("Research-score", ascending=False).head(15)

top_research_display = top_research.copy()

top_research_display["Pris (USD)"] = top_research_display["Pris (USD)"].apply(
    lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
)

top_research_display["Ændring (%)"] = top_research_display["Ændring (%)"].apply(
    format_percent
)

top_research_display["Market Cap"] = top_research_display["Market Cap"].apply(
    format_number
)

top_research_display["Beta"] = top_research_display["Beta"].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
)

st.dataframe(
    top_research_display[
        [
            "Ticker",
            "Navn",
            "Pris (USD)",
            "Ændring (%)",
            "Vol/Avg",
            "Købsinteresse",
            "Salgspres",
            "Opmærksomhed",
            "Research-score",
            "Research-vurdering",
            "Nyheder",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.warning(
    "Research-score er ikke en købsanbefaling. Den viser kun aktier, "
    "som ud fra momentum, volumen, nyheder og sentiment kan være relevante "
    "at undersøge nærmere."
)


# ── Vis samlet tabel ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 Alle resultater — {len(df)} aktier")

df_display = df.copy()

df_display["Pris (USD)"] = df_display["Pris (USD)"].apply(
    lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
)

df_display["Ændring (%)"] = df_display["Ændring (%)"].apply(format_percent)

df_display["Market Cap"] = df_display["Market Cap"].apply(format_number)

df_display["Beta"] = df_display["Beta"].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
)

try:
    st.dataframe(
        df_display.style
        .background_gradient(subset=["Købsinteresse"], cmap="Greens")
        .background_gradient(subset=["Salgspres"], cmap="Reds")
        .background_gradient(subset=["Opmærksomhed"], cmap="Blues")
        .background_gradient(subset=["Research-score"], cmap="Purples"),
        use_container_width=True,
        hide_index=True,
    )
except Exception:
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )


# ── Hurtig søgning ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔎 Hurtig søgning")

search = st.text_input("Søg efter aktie, ticker eller navn")

if search:
    mask = (
        df["Ticker"].astype(str).str.upper().str.contains(search.upper(), na=False)
        |
        df["Navn"].astype(str).str.lower().str.contains(search.lower(), na=False)
    )

    search_df = df[mask].copy()

    if search_df.empty:
        st.info("Ingen aktier matcher søgningen.")
    else:
        st.dataframe(
            search_df,
            use_container_width=True,
            hide_index=True,
        )
