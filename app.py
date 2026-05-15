# app.py — Forside / Markedsoverblik

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import DEFAULT_WATCHLIST, DISCLAIMER
from src.market_data import get_market_overview, get_top_movers, get_intraday_top_movers
from src.news_fetcher import fetch_all_news
from src.sentiment import analyze_sentiment
from src.stock_mapper import enrich_news_with_stocks, load_tickers_df
from src.scoring import calculate_scores, calculate_research_candidate_score
from src.charts import (
    plot_top_movers,
    plot_sentiment_distribution,
    plot_most_mentioned,
)
from src.utils import format_number, format_percent, color_for_change, get_market_status, get_global_market_status

# ── Side-konfiguration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📈 Aktie Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS-styling ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
  [data-testid="stMetricValue"] {
      font-size: 1.3rem !important;
  }

  .news-card {
      background: #1e2130;
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 10px;
      border-left: 4px solid #2196f3;
  }

  .positive {
      border-left-color: #00c853 !important;
  }

  .negative {
      border-left-color: #d50000 !important;
  }

  .neutral {
      border-left-color: #9e9e9e !important;
  }

  .ticker-badge {
      background: #2a2d3e;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 0.75rem;
      margin-right: 4px;
      color: #90caf9;
      display: inline-block;
  }
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Aktie Dashboard")
    st.markdown("---")

    market_status = get_market_status()

    st.markdown(
        f"**Markedsstatus:** "
        f"<span style='color:{market_status['color']}'>{market_status['status']}</span>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if st.button("🔄 Opdater data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🌍 Globale markeder")

    global_markets = get_global_market_status()

    for market in global_markets:
        st.markdown(
            f"""
            <div style="
                padding: 8px 10px;
                margin-bottom: 6px;
                border-radius: 8px;
                background-color: #1e2130;
                border-left: 4px solid {market['color']};
            ">
                <div style="font-weight: 600;">
                    {market['emoji']} {market['name']}
                </div>
                <div style="font-size: 0.85rem; color: #cccccc;">
                    Status:
                    <span style="color:{market['color']}; font-weight: 700;">
                        {market['status']}
                    </span>
                    · Lokal tid: {market['local_time']}
                </div>
                <div style="font-size: 0.75rem; color: #999999;">
                    Åbningstid: {market['open']} - {market['close']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(DISCLAIMER)


# ── Overskrift ────────────────────────────────────────────────────────────────
st.title("📈 Aktie- & Nyhedsdashboard")
st.caption("Realtidsanalyse af aktiemarkedet — ikke finansiel rådgivning.")


# ── Indlæs data ───────────────────────────────────────────────────────────────
with st.spinner("Henter markedsdata…"):
    overview = get_market_overview(DEFAULT_WATCHLIST)

with st.spinner("Henter nyheder…"):
    raw_news = fetch_all_news()
    tickers_df = load_tickers_df()

    for item in raw_news:
        item["sentiment"] = analyze_sentiment(item.get("raw_text", ""))

    news = enrich_news_with_stocks(raw_news, tickers_df)


# ── KPI-metrics ───────────────────────────────────────────────────────────────
st.subheader("Markedsoverblik")

if not overview.empty:
    avg_change = overview["Ændring (%)"].mean()

    mood = (
        "🟢 Bullish"
        if avg_change > 0.5
        else "🔴 Bearish"
        if avg_change < -0.5
        else "⬜ Neutral"
    )

    pos_count = int((overview["Ændring (%)"] > 0).sum())
    neg_count = int((overview["Ændring (%)"] < 0).sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Markedsstemning", mood)
    col2.metric("Gns. daglig ændring", format_percent(avg_change))
    col3.metric("Stigende aktier", f"{pos_count} / {len(overview)}")
    col4.metric("Nyheder hentet", len(news))

else:
    st.warning("Markedsdata ikke tilgængelig.")


# ── Top movers ────────────────────────────────────────────────────────────────
st.markdown("---")

col_g, col_l, col_v = st.columns(3)

movers = get_top_movers(DEFAULT_WATCHLIST) if not overview.empty else {}

with col_g:
    st.subheader("🟢 Top vindere")

    for stock in movers.get("gainers", []):
        pct = stock.get("Ændring (%)", 0) or 0

        st.markdown(
            f"**{stock['Ticker']}** &nbsp; "
            f"<span style='color:#00c853'>{format_percent(pct)}</span>",
            unsafe_allow_html=True,
        )

with col_l:
    st.subheader("🔴 Top tabere")

    for stock in movers.get("losers", []):
        pct = stock.get("Ændring (%)", 0) or 0

        st.markdown(
            f"**{stock['Ticker']}** &nbsp; "
            f"<span style='color:#d50000'>{format_percent(pct)}</span>",
            unsafe_allow_html=True,
        )

with col_v:
    st.subheader("📊 Høj volumen")

    for stock in movers.get("high_volume", []):
        ratio = stock.get("Vol/Avg", 0) or 0

        st.markdown(
            f"**{stock['Ticker']}** &nbsp; "
            f"<span style='color:#ffab00'>{ratio:.1f}x gennemsnit</span>",
            unsafe_allow_html=True,
        )


# ── Top-movers graf ───────────────────────────────────────────────────────────
if not overview.empty:
    top10 = overview.nlargest(5, "Ændring (%)")
    bot10 = overview.nsmallest(5, "Ændring (%)")

    combined = pd.concat([top10, bot10]).drop_duplicates("Ticker")

    st.plotly_chart(plot_top_movers(combined), use_container_width=True)

# ── Intraday top movers ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚡ Top movers de seneste 2 timer")

with st.spinner("Henter intraday-data for de seneste 2 timer…"):
    intraday_movers = get_intraday_top_movers(
        DEFAULT_WATCHLIST,
        lookback_hours=2,
        interval="5m",
        top_n=5,
    )

col_intraday_gainers, col_intraday_losers = st.columns(2)

with col_intraday_gainers:
    st.markdown("### 🟢 Største stigninger")

    gainers_2h = intraday_movers.get("gainers")

    if gainers_2h is not None and not gainers_2h.empty:
        display_gainers = gainers_2h.copy()
        display_gainers["Pris nu"] = display_gainers["Pris nu"].map(lambda x: f"${x:.2f}")
        display_gainers["Pris før"] = display_gainers["Pris før"].map(lambda x: f"${x:.2f}")
        display_gainers["Ændring (%)"] = display_gainers["Ændring (%)"].map(lambda x: f"{x:+.2f}%")

        st.dataframe(
            display_gainers[
                ["Ticker", "Pris før", "Pris nu", "Ændring (%)", "Starttid", "Seneste tid"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Ingen intraday-data fundet for top gainers.")

with col_intraday_losers:
    st.markdown("### 🔴 Største fald")

    losers_2h = intraday_movers.get("losers")

    if losers_2h is not None and not losers_2h.empty:
        display_losers = losers_2h.copy()
        display_losers["Pris nu"] = display_losers["Pris nu"].map(lambda x: f"${x:.2f}")
        display_losers["Pris før"] = display_losers["Pris før"].map(lambda x: f"${x:.2f}")
        display_losers["Ændring (%)"] = display_losers["Ændring (%)"].map(lambda x: f"{x:+.2f}%")

        st.dataframe(
            display_losers[
                ["Ticker", "Pris før", "Pris nu", "Ændring (%)", "Starttid", "Seneste tid"]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Ingen intraday-data fundet for top losers.")

st.caption(
    "Intraday-data kan være forsinket og afhænger af markedets åbningstid. "
    "Dette er ikke finansiel rådgivning."
)
# ── Scoring-tabel ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Interesseanalyse")

if not overview.empty:
    score_rows = []

    for _, row in overview.iterrows():
        ticker = row["Ticker"]

        ticker_info = {
            "change_pct": row.get("Ændring (%)"),
            "volume": row.get("Volumen"),
            "avg_volume": (
                row.get("Volumen") / row.get("Vol/Avg", 1)
                if row.get("Vol/Avg") and row.get("Vol/Avg") != 0
                else None
            ),
        }

        rel_news = [
            n for n in news if ticker in n.get("affected_tickers", [])
        ]

        scores = calculate_scores(ticker_info, rel_news)

        score_rows.append(
            {
                "Ticker": ticker,
                "Navn": row.get("Navn", ticker),
                "Pris": (
                    f"${row.get('Pris (USD)', 0):.2f}"
                    if row.get("Pris (USD)")
                    else "N/A"
                ),
                "Dag %": format_percent(row.get("Ændring (%)")),
                "Købsinteresse": scores["buy_score"],
                "Salgspres": scores["sell_score"],
                "Opmærksomhed": scores["attention_score"],
                "Status": scores["label"],
            }
        )

    score_df = pd.DataFrame(score_rows)

    st.dataframe(
        score_df.style.background_gradient(
            subset=["Købsinteresse"],
            cmap="Greens",
        ).background_gradient(
            subset=["Salgspres"],
            cmap="Reds",
        ),
        use_container_width=True,
        hide_index=True,
    )


# ── Nyheder ───────────────────────────────────────────────────────────────────
st.markdown("---")

col_news, col_charts = st.columns([3, 2])

with col_news:
    st.subheader("📰 Seneste nyheder")

    for item in news[:8]:
        sent = item.get("sentiment", {})
        label = sent.get("label", "Neutral")

        css = (
            "positive"
            if "positiv" in label.lower()
            else "negative"
            if "negativ" in label.lower()
            else "neutral"
        )

        tickers_html = " ".join(
            f"<span class='ticker-badge'>{t}</span>"
            for t in item.get("affected_tickers", [])[:4]
        )

        impact = sent.get("impact", "Lav")

        st.markdown(
            f"""
<div class='news-card {css}'>
  <b>{item.get('title', '')}</b><br>
  <small style='color:#9e9e9e'>
    {item.get('source', '')} · {item.get('published', '')} ·
    Sentiment: <b>{label}</b> · Påvirkning: <b>{impact}</b>
  </small><br>
  {tickers_html}
  <br>
  <small>{item.get('summary', '')[:160]}…</small><br>
  <a href="{item.get('url', '#')}" target="_blank"
     style='color:#90caf9;font-size:0.8rem'>Læs mere →</a>
</div>
""",
            unsafe_allow_html=True,
        )


with col_charts:
    st.subheader("📊 Sentimentfordeling")

    if news:
        st.plotly_chart(
            plot_sentiment_distribution(news),
            use_container_width=True,
        )

        st.plotly_chart(
            plot_most_mentioned(news),
            use_container_width=True,
        )
    else:
        st.info("Ingen nyheder fundet endnu.")
