# pages/3_Stock_Profile.py — Detaljeret aktieprofilside
import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import DISCLAIMER
from src.market_data import get_ticker_info, get_stock_history, get_ticker_news
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.scoring import calculate_scores
from src.charts import (
    plot_candlestick, plot_volume_chart, plot_rsi, plot_score_gauge
)
from src.utils import format_number, format_percent

st.set_page_config(page_title="Aktieproil", page_icon="📊", layout="wide")
st.title("📊 Aktie-profil")
st.caption(DISCLAIMER)

# ── Ticker-input ─────────────────────────────────────────────────────────────
col_input, col_period = st.columns([2, 1])
with col_input:
    ticker = st.text_input(
        "Ticker-symbol", value="AAPL", placeholder="fx NVDA, MSFT, NOVO-B.CO"
    ).upper().strip()
with col_period:
    period = st.selectbox(
        "Periode",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=1,
    )

if not ticker:
    st.info("Indtast et ticker-symbol for at se aktie-profilen.")
    st.stop()

# ── Hent data ─────────────────────────────────────────────────────────────────
with st.spinner(f"Henter data for {ticker}…"):
    info  = get_ticker_info(ticker)
    hist  = get_stock_history(ticker, period=period)
    yfnews = get_ticker_news(ticker, max_items=10)

# ── Fejlhåndtering ────────────────────────────────────────────────────────────
if "error" in info and not info.get("price"):
    st.error(f"Kunne ikke hente data for '{ticker}'. Tjek ticker-symbolet.")
    st.stop()

# ── Nyheder med sentiment ─────────────────────────────────────────────────────
tickers_df = load_tickers_df()
for item in yfnews:
    item["raw_text"] = item.get("title", "") + " " + item.get("summary", "")
    item["sentiment"] = analyze_sentiment(item["raw_text"], info.get("sector"))
    item["affected_tickers"] = [ticker]

# Tilføj generelle nyheder
all_news = fetch_all_news()
for item in all_news:
    item["sentiment"] = analyze_sentiment(item.get("raw_text", ""), info.get("sector"))
all_news = enrich_news_with_stocks(all_news, tickers_df)
related_news = [n for n in all_news if ticker in n.get("affected_tickers", [])]

combined_news = (yfnews + related_news)[:15]

# ── Scoring ───────────────────────────────────────────────────────────────────
scores = calculate_scores(info, combined_news)

# ── Header ───────────────────────────────────────────────────────────────────
change    = info.get("change_pct", 0) or 0
price     = info.get("price")
change_c  = "#00c853" if change >= 0 else "#d50000"

st.markdown(f"""
## {info.get('name', ticker)} ({ticker})
<span style='font-size:2rem; font-weight:bold'>${price:.2f}</span> &nbsp;
<span style='color:{change_c}; font-size:1.2rem'>{format_percent(change)}</span> &nbsp;
<span style='color:#9e9e9e'>{info.get('sector','')} · {info.get('country','')}</span>
""", unsafe_allow_html=True)

# ── Nøgletal ──────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Market Cap",    format_number(info.get("market_cap")))
c2.metric("Volumen",       format_number(info.get("volume")))
c3.metric("Gns. Volumen",  format_number(info.get("avg_volume")))
c4.metric("52W High",      f"${info.get('week_52_high'):.2f}" if info.get("week_52_high") else "N/A")
c5.metric("52W Low",       f"${info.get('week_52_low'):.2f}"  if info.get("week_52_low")  else "N/A")
c6.metric("Beta",          f"{info.get('beta'):.2f}"          if info.get("beta")          else "N/A")

# ── Kursgraf ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Kursgraf")
if not hist.empty:
    show_sma = st.checkbox("Vis SMA (20/50/200)", value=True)
    st.plotly_chart(plot_candlestick(hist, ticker, show_sma), use_container_width=True)
    st.plotly_chart(plot_volume_chart(hist, ticker),           use_container_width=True)
    st.plotly_chart(plot_rsi(hist),                            use_container_width=True)
else:
    st.warning("Historiske kursdata ikke tilgængelige.")

# ── Score-gauges ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Interesseanalyse")
st.markdown(f"**Status:** {scores['label']}")

g1, g2, g3, g4 = st.columns(4)
with g1:
    st.plotly_chart(
        plot_score_gauge(scores["buy_score"], "Købsinteresse"),
        use_container_width=True,
    )
with g2:
    st.plotly_chart(
        plot_score_gauge(scores["sell_score"], "Salgspres"),
        use_container_width=True,
    )
with g3:
    st.plotly_chart(
        plot_score_gauge(scores["attention_score"], "Opmærksomhed"),
        use_container_width=True,
    )
with g4:
    st.plotly_chart(
        plot_score_gauge(scores["news_impact"], "Nyhedsimpact"),
        use_container_width=True,
    )

# Score-komponenter
with st.expander("📐 Se score-detaljer"):
    comp = scores.get("components", {})
    st.json({
        "Sentiment-bidrag":  comp.get("sentiment_contribution"),
        "Volumen-bidrag":    comp.get("volume_contribution"),
        "Momentum-bidrag":   comp.get("momentum_contribution"),
        "Omtale-bidrag":     comp.get("mention_contribution"),
        "Antal nyheder":     comp.get("news_count"),
        "Vol/Avg ratio":     comp.get("vol_ratio"),
        "Kursændring (%)":   comp.get("change_pct"),
    })

# ── Seneste nyheder ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📰 Nyheder om {ticker}")

if combined_news:
    for item in combined_news[:8]:
        sent  = item.get("sentiment", {})
        label = sent.get("label", "Neutral")
        color = (
            "#00c853" if "positiv" in label.lower()
            else "#d50000" if "negativ" in label.lower()
            else "#9e9e9e"
        )
        st.markdown(
            f"**[{item.get('title','')}]({item.get('url','#')})**  \n"
            f"<small style='color:#9e9e9e'>"
            f"{item.get('source','')} · {item.get('published','')} · "
            f"<span style='color:{color}'>{label}</span> · "
            f"{sent.get('explanation','')[:120]}"
            f"</small>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
else:
    st.info("Ingen relaterede nyheder fundet.")

# ── Virksomhedsbeskrivelse ────────────────────────────────────────────────────
if info.get("description"):
    with st.expander("ℹ️ Om virksomheden"):
        st.write(info["description"])