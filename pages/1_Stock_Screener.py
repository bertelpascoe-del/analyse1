# pages/1_Stock_Screener.py — Aktiescreener
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import SECTOR_TICKERS, DISCLAIMER
from src.market_data import get_market_overview
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.scoring import calculate_scores
from src.utils import format_percent, format_number

st.set_page_config(page_title="Aktiescreener", page_icon="🔍", layout="wide")
st.title("🔍 Aktiescreener")
st.caption(DISCLAIMER)

# ── Alle tickers ──────────────────────────────────────────────────────────────
all_tickers = [t for tickers in SECTOR_TICKERS.values() for t in tickers]
tickers_df  = load_tickers_df()

# ── Filtre i sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtre")
    selected_sectors = st.multiselect(
        "Sektor",
        options=list(SECTOR_TICKERS.keys()),
        default=list(SECTOR_TICKERS.keys()),
    )
    min_change, max_change = st.slider(
        "Daglig ændring (%)", -20.0, 20.0, (-20.0, 20.0), step=0.5
    )
    min_vol_ratio = st.slider("Min. volumen ift. gennemsnit (x)", 0.0, 5.0, 0.0, 0.1)

    sort_col = st.selectbox(
        "Sorter efter",
        ["Ændring (%)", "Købsinteresse", "Salgspres", "Opmærksomhed", "Vol/Avg"],
    )
    sort_asc = st.checkbox("Stigende rækkefølge", value=False)

    if st.button("🔄 Opdater data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Filtrér tickers ud fra valgte sektorer ────────────────────────────────────
filtered_tickers = []
for sector in selected_sectors:
    filtered_tickers.extend(SECTOR_TICKERS.get(sector, []))
filtered_tickers = list(set(filtered_tickers))

if not filtered_tickers:
    st.info("Vælg mindst én sektor i sidebaren.")
    st.stop()

# ── Hent data ─────────────────────────────────────────────────────────────────
with st.spinner("Henter markedsdata…"):
    overview = get_market_overview(filtered_tickers)

with st.spinner("Henter nyheder…"):
    raw_news = fetch_all_news()
    for item in raw_news:
        item["sentiment"] = analyze_sentiment(item.get("raw_text", ""))
    news = enrich_news_with_stocks(raw_news, tickers_df)

# ── Byg screener-tabel ────────────────────────────────────────────────────────
rows = []
for _, row in overview.iterrows():
    ticker = row["Ticker"]
    change = row.get("Ændring (%)", 0) or 0
    vol_r  = row.get("Vol/Avg", 0) or 0

    if not (min_change <= change <= max_change):
        continue
    if vol_r < min_vol_ratio:
        continue

    ticker_inf = {
        "change_pct": change,
        "volume":     row.get("Volumen"),
        "avg_volume": (row.get("Volumen") / vol_r) if vol_r > 0 else None,
    }
    rel_news = [n for n in news if ticker in n.get("affected_tickers", [])]
    scores   = calculate_scores(ticker_inf, rel_news)

    rows.append({
        "Ticker":        ticker,
        "Navn":          row.get("Navn", ticker),
        "Sektor":        row.get("Sektor", ""),
        "Pris (USD)":    row.get("Pris (USD)"),
        "Ændring (%)":   change,
        "Vol/Avg":       vol_r,
        "Market Cap":    row.get("Market Cap"),
        "Beta":          row.get("Beta"),
        "Købsinteresse": scores["buy_score"],
        "Salgspres":     scores["sell_score"],
        "Opmærksomhed":  scores["attention_score"],
        "Status":        scores["label"],
        "Nyheder":       len(rel_news),
    })

if not rows:
    st.warning("Ingen aktier matcher de valgte filtre.")
    st.stop()

df = pd.DataFrame(rows)

# Sorter
if sort_col in df.columns:
    df = df.sort_values(sort_col, ascending=sort_asc)

# ── Vis tabel ─────────────────────────────────────────────────────────────────
st.subheader(f"Resultater — {len(df)} aktier")

# Format kolonner
df_display = df.copy()
df_display["Pris (USD)"]  = df_display["Pris (USD)"].apply(
    lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
)
df_display["Ændring (%)"] = df_display["Ændring (%)"].apply(format_percent)
df_display["Market Cap"]  = df_display["Market Cap"].apply(format_number)
df_display["Beta"]        = df_display["Beta"].apply(
    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
)

st.dataframe(
    df_display.style
    .background_gradient(subset=["Købsinteresse"], cmap="Greens")
    .background_gradient(subset=["Salgspres"],     cmap="Reds")
    .background_gradient(subset=["Opmærksomhed"],  cmap="Blues"),
    use_container_width=True,
    hide_index=True,
)

# ── Hurtig søgning ────────────────────────────────────────────────────────────
st.markdown("---")
search = st.text_input("🔎 Søg efter aktie (ticker eller navn)")
if search:
    mask = (
        df["Ticker"].str.upper().str.contains(search.upper()) |
        df["Navn"].str.lower().str.contains(search.lower())
    )
    st.dataframe(df[mask], use_container_width=True, hide_index=True)