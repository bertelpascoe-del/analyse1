# pages/4_Sector_Analysis.py — Sektoranalyse
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import SECTOR_TICKERS, DISCLAIMER
from src.market_data import get_market_overview
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.charts import plot_sector_heatmap, plot_sentiment_distribution

st.set_page_config(page_title="Sektoranalyse", page_icon="🏭", layout="wide")
st.title("🏭 Sektoranalyse")
st.caption(DISCLAIMER)

# ── Hent data ─────────────────────────────────────────────────────────────────
all_tickers = [t for tickers in SECTOR_TICKERS.values() for t in tickers]
tickers_df  = load_tickers_df()

with st.spinner("Henter sektordata…"):
    overview = get_market_overview(all_tickers)

with st.spinner("Henter nyheder…"):
    raw_news = fetch_all_news()
    for item in raw_news:
        item["sentiment"] = analyze_sentiment(item.get("raw_text", ""))
    news = enrich_news_with_stocks(raw_news, tickers_df)

# ── Byg sektor-aggregat ───────────────────────────────────────────────────────
if overview.empty:
    st.warning("Sektordata ikke tilgængeligt.")
    st.stop()

sector_stats = {}
for sector, tickers in SECTOR_TICKERS.items():
    sec_df = overview[overview["Ticker"].isin(tickers)]
    if sec_df.empty:
        continue

    avg_change = sec_df["Ændring (%)"].mean()
    avg_vol_r  = sec_df["Vol/Avg"].mean()
    total_cap  = sec_df["Market Cap"].sum()

    # Nyheder for sektoren
    sec_news = [
        n for n in news
        if any(t in n.get("affected_tickers", []) for t in tickers)
    ]
    pos_news = sum(1 for n in sec_news if "positiv" in n.get("sentiment",{}).get("label","").lower())
    neg_news = sum(1 for n in sec_news if "negativ" in n.get("sentiment",{}).get("label","").lower())

    sector_stats[sector] = {
        "Sektor":          sector,
        "Ændring (%)":     round(avg_change, 2),
        "Gns. Vol/Avg":    round(avg_vol_r,  2),
        "Antal aktier":    len(sec_df),
        "Nyheder total":   len(sec_news),
        "Positive nyheder": pos_news,
        "Negative nyheder": neg_news,
    }

if not sector_stats:
    st.warning("Ingen sektordata at vise.")
    st.stop()

sector_df = pd.DataFrame(sector_stats.values())

# ── KPI ───────────────────────────────────────────────────────────────────────
best_sector  = sector_df.loc[sector_df["Ændring (%)"].idxmax(), "Sektor"]
worst_sector = sector_df.loc[sector_df["Ændring (%)"].idxmin(), "Sektor"]
most_news    = sector_df.loc[sector_df["Nyheder total"].idxmax(), "Sektor"]

c1, c2, c3 = st.columns(3)
c1.metric("Bedste sektor",  best_sector,  f"{sector_df.loc[sector_df['Sektor']==best_sector,'Ændring (%)'].values[0]:+.2f}%")
c2.metric("Svageste sektor", worst_sector, f"{sector_df.loc[sector_df['Sektor']==worst_sector,'Ændring (%)'].values[0]:+.2f}%")
c3.metric("Mest omtalt",    most_news,    f"{sector_df.loc[sector_df['Sektor']==most_news,'Nyheder total'].values[0]} nyheder")

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Sektor-performance (daglig ændring %)")
change_dict = dict(zip(sector_df["Sektor"], sector_df["Ændring (%)"]))
st.plotly_chart(plot_sector_heatmap(change_dict), use_container_width=True)

# ── Sektor-tabel ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Sektor-detaljer")
st.dataframe(
    sector_df.style
    .background_gradient(subset=["Ændring (%)"],      cmap="RdYlGn")
    .background_gradient(subset=["Positive nyheder"],  cmap="Greens")
    .background_gradient(subset=["Negative nyheder"],  cmap="Reds"),
    use_container_width=True,
    hide_index=True,
)

# ── Sektor-drill-down ─────────────────────────────────────────────────────────
st.markdown("---")
selected_sector = st.selectbox("Vælg sektor for detaljer", list(SECTOR_TICKERS.keys()))
if selected_sector:
    sec_tickers = SECTOR_TICKERS[selected_sector]
    sec_df      = overview[overview["Ticker"].isin(sec_tickers)].copy()

    st.subheader(f"{selected_sector} — Aktier")
    if not sec_df.empty:
        st.dataframe(sec_df, use_container_width=True, hide_index=True)

    st.subheader(f"{selected_sector} — Nyheder")
    sec_news = [
        n for n in news
        if any(t in n.get("affected_tickers", []) for t in sec_tickers)
    ]
    if sec_news:
        st.plotly_chart(
            plot_sentiment_distribution(sec_news),
            use_container_width=True,
        )
        for item in sec_news[:6]:
            label = item.get("sentiment", {}).get("label", "Neutral")
            st.markdown(
                f"**[{item.get('title','')}]({item.get('url','#')})**  "
                f"| {item.get('source','')} | {label}"
            )
    else:
        st.info(f"Ingen nyheder fundet for {selected_sector}.")