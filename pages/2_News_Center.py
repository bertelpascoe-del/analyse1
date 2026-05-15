# pages/2_News_Center.py — Nyhedscenter
import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import DISCLAIMER
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.charts import plot_sentiment_distribution, plot_most_mentioned
from src.utils import sentiment_label_to_emoji

st.set_page_config(page_title="Nyhedscenter", page_icon="📰", layout="wide")
st.title("📰 Nyhedscenter")
st.caption(DISCLAIMER)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.news-card {
    background:#1e2130; border-radius:10px;
    padding:14px 16px; margin-bottom:10px;
    border-left:4px solid #2196f3;
}
.positive { border-left-color: #00c853 !important; }
.negative { border-left-color: #d50000 !important; }
.neutral  { border-left-color: #9e9e9e !important; }
.ticker-badge {
    background:#2a2d3e; border-radius:4px;
    padding:2px 7px; font-size:0.75rem;
    margin-right:4px; color:#90caf9;
    display:inline-block;
}
</style>
""", unsafe_allow_html=True)

# ── Hent data ─────────────────────────────────────────────────────────────────
with st.spinner("Henter nyheder…"):
    raw_news   = fetch_all_news()
    tickers_df = load_tickers_df()
    for item in raw_news:
        item["sentiment"] = analyze_sentiment(item.get("raw_text", ""))
    news = enrich_news_with_stocks(raw_news, tickers_df)

# ── Sidebar-filtre ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtre")

    sources = sorted({item.get("source", "Ukendt") for item in news})
    sel_sources = st.multiselect("Kilde", sources, default=sources)

    sentiments = ["Meget positiv", "Positiv", "Neutral", "Negativ", "Meget negativ"]
    sel_sent = st.multiselect("Sentiment", sentiments, default=sentiments)

    impacts = ["Høj", "Mellem", "Lav"]
    sel_impact = st.multiselect("Påvirkningsgrad", impacts, default=impacts)

    ticker_search = st.text_input("Ticker-filter (fx NVDA)")

    if st.button("🔄 Opdater nyheder", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Filtrér nyheder ───────────────────────────────────────────────────────────
filtered = []
for item in news:
    sent   = item.get("sentiment", {})
    label  = sent.get("label",  "Neutral")
    impact = sent.get("impact", "Lav")
    source = item.get("source", "Ukendt")

    if source not in sel_sources:
        continue
    if label not in sel_sent:
        continue
    if impact not in sel_impact:
        continue
    if ticker_search:
        if ticker_search.upper() not in [t.upper() for t in item.get("affected_tickers", [])]:
            continue
    filtered.append(item)

# ── Statistik-chips ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Nyheder vist",   len(filtered))
col2.metric("Positive",       sum(1 for n in filtered if "positiv" in n.get("sentiment",{}).get("label","").lower()))
col3.metric("Negative",       sum(1 for n in filtered if "negativ" in n.get("sentiment",{}).get("label","").lower()))

# ── Graf-oversigt ─────────────────────────────────────────────────────────────
if filtered:
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.plotly_chart(plot_sentiment_distribution(filtered), use_container_width=True)
    with col_chart2:
        st.plotly_chart(plot_most_mentioned(filtered), use_container_width=True)

st.markdown("---")
st.subheader(f"📋 Nyheder ({len(filtered)})")

# ── Nyhedskort ────────────────────────────────────────────────────────────────
for item in filtered[:40]:
    sent  = item.get("sentiment", {})
    label = sent.get("label", "Neutral")
    emoji = sentiment_label_to_emoji(label)
    css   = (
        "positive" if "positiv" in label.lower()
        else "negative" if "negativ" in label.lower()
        else "neutral"
    )
    tickers_html = " ".join(
        f"<span class='ticker-badge'>{t}</span>"
        for t in item.get("affected_tickers", [])[:6]
    )
    affected_html = ""
    if item.get("affected_stocks"):
        rows = []
        for s in item["affected_stocks"][:4]:
            rows.append(
                f"<b>{s['ticker']}</b> ({s['impact_type']}) — {s['reason']}"
            )
        affected_html = "<br><small style='color:#b0bec5'>" + " | ".join(rows) + "</small>"

    exp_text = sent.get("explanation", "")

    st.markdown(f"""
<div class='news-card {css}'>
  <b>{emoji} {item.get('title','')}</b><br>
  <small style='color:#9e9e9e'>
    {item.get('source','')} · {item.get('published','')} ·
    Sentiment: <b>{label}</b> · Påvirkning: <b>{sent.get('impact','Lav')}</b>
  </small><br>
  {tickers_html}
  <br><small>{item.get('summary','')[:200]}</small>
  {affected_html}
  <br><small style='color:#80cbc4'><i>{exp_text}</i></small>
  <br><a href="{item.get('url','#')}" target="_blank"
     style='color:#90caf9;font-size:0.8rem'>Læs mere →</a>
</div>
""", unsafe_allow_html=True)

if len(filtered) == 0:
    st.info("Ingen nyheder matcher de valgte filtre.")