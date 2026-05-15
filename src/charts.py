# src/charts.py — Plotly-visualiseringer
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.market_data import add_technical_indicators


# ── Farvepalet ────────────────────────────────────────────────────────────────
COLORS = {
    "green":      "#00c853",
    "red":        "#d50000",
    "blue":       "#2196f3",
    "yellow":     "#ffab00",
    "gray":       "#9e9e9e",
    "bg":         "#0e1117",
    "surface":    "#1e2130",
    "text":       "#fafafa",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor =COLORS["surface"],
    font=dict(color=COLORS["text"], family="Inter, Arial, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def _base_layout(**kwargs) -> dict:
    layout = PLOTLY_LAYOUT.copy()
    layout.update(kwargs)
    return layout


def plot_candlestick(df: pd.DataFrame, ticker: str, show_sma: bool = True) -> go.Figure:
    """Interaktivt candlestick-chart med volumen og SMAs."""
    if df.empty:
        return _empty_figure("Ingen data tilgængelig")

    df = add_technical_indicators(df)
    close = df["Close"].squeeze()
    colors = [
        COLORS["green"] if c >= o else COLORS["red"]
        for c, o in zip(df["Close"].squeeze(), df["Open"].squeeze())
    ]

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open =df["Open"].squeeze(),
        high =df["High"].squeeze(),
        low  =df["Low"].squeeze(),
        close=close,
        name =ticker,
        increasing_line_color=COLORS["green"],
        decreasing_line_color=COLORS["red"],
    ))

    # SMAs
    if show_sma:
        sma_colors = {"SMA20": "#ffab00", "SMA50": "#2196f3", "SMA200": "#e040fb"}
        for col, color in sma_colors.items():
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col].squeeze(),
                    mode="lines", name=col,
                    line=dict(color=color, width=1.2),
                ))

    fig.update_layout(
        **_base_layout(
            title=f"{ticker} — Kursgraf",
            xaxis_rangeslider_visible=False,
            height=420,
        )
    )
    fig.update_xaxes(gridcolor="#2a2d3e")
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def plot_volume_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Volumenbar-chart med farve baseret på op/ned-dag."""
    if df.empty or "Volume" not in df.columns:
        return _empty_figure("Ingen volumendata")

    close = df["Close"].squeeze()
    colors = [
        COLORS["green"] if c >= o else COLORS["red"]
        for c, o in zip(close, df["Open"].squeeze())
    ]
    fig = go.Figure(go.Bar(
        x=df.index,
        y=df["Volume"].squeeze(),
        marker_color=colors,
        name="Volumen",
    ))
    fig.update_layout(**_base_layout(title=f"{ticker} — Volumen", height=200))
    fig.update_xaxes(gridcolor="#2a2d3e")
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def plot_rsi(df: pd.DataFrame) -> go.Figure:
    """RSI-chart med overkøbt/oversolgt zoner."""
    from src.market_data import calculate_rsi
    if df.empty or "Close" not in df.columns:
        return _empty_figure("Ingen RSI-data")

    close = df["Close"].squeeze()
    rsi   = calculate_rsi(close)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        mode="lines", name="RSI",
        line=dict(color=COLORS["blue"], width=2),
    ))
    # Zoner
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS["red"],  opacity=0.1, line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor=COLORS["green"], opacity=0.1, line_width=0)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"],   line_width=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"], line_width=1)

    fig.update_layout(**_base_layout(
        title="RSI (14 dage) — over 70: overkøbt, under 30: oversolgt",
        height=200, yaxis=dict(range=[0, 100]),
    ))
    fig.update_xaxes(gridcolor="#2a2d3e")
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def plot_score_gauge(score: int, title: str) -> go.Figure:
    """Gauge-chart for Buy/Sell/Attention score (0–100)."""
    color = COLORS["green"] if score >= 55 else COLORS["red"] if score < 35 else COLORS["yellow"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"color": COLORS["text"]}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLORS["text"]},
            "bar":  {"color": color},
            "bgcolor": COLORS["surface"],
            "steps": [
                {"range": [0,  35], "color": "#3d1a1a"},
                {"range": [35, 55], "color": "#2a2a1a"},
                {"range": [55, 100],"color": "#1a3d1a"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.75,
                "value": score,
            },
        },
        number={"font": {"color": COLORS["text"]}},
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig


def plot_top_movers(df: pd.DataFrame) -> go.Figure:
    """Vandret bar-chart over aktier sorteret efter daglig ændring."""
    if df.empty:
        return _empty_figure("Ingen data")

    df = df.dropna(subset=["Ændring (%)"]).copy()
    df = df.sort_values("Ændring (%)")
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in df["Ændring (%)"]]

    fig = go.Figure(go.Bar(
        x=df["Ændring (%)"],
        y=df["Ticker"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in df["Ændring (%)"]],
        textposition="outside",
    ))
    fig.update_layout(**_base_layout(
        title="Top bevægelser (dag %)", height=max(250, len(df) * 32),
        xaxis_title="Ændring (%)",
    ))
    fig.update_xaxes(gridcolor="#2a2d3e", zeroline=True, zerolinecolor=COLORS["gray"])
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def plot_sector_heatmap(sector_data: dict) -> go.Figure:
    """
    Heatmap over sektor-performance.
    sector_data: {sektor: avg_change_pct}
    """
    if not sector_data:
        return _empty_figure("Ingen sektordata")

    sectors = list(sector_data.keys())
    values  = [sector_data[s] for s in sectors]
    colors  = [COLORS["green"] if v >= 0 else COLORS["red"] for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=sectors,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in values],
        textposition="auto",
    ))
    fig.update_layout(**_base_layout(
        title="Sektor-performance (dag %)", height=380,
    ))
    fig.update_xaxes(gridcolor="#2a2d3e", zeroline=True, zerolinecolor=COLORS["gray"])
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def plot_sentiment_distribution(news_list: list) -> go.Figure:
    """Pie-chart over sentiment-fordeling i nyheder."""
    from collections import Counter
    labels_map = {
        "Meget positiv": COLORS["green"],
        "Positiv":       "#69f0ae",
        "Neutral":       COLORS["gray"],
        "Negativ":       "#ff5252",
        "Meget negativ": COLORS["red"],
    }
    counts = Counter(
        item.get("sentiment", {}).get("label", "Neutral")
        for item in news_list
    )
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [labels_map.get(l, COLORS["gray"]) for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors),
        textfont=dict(color="white"),
        hole=0.35,
    ))
    fig.update_layout(**_base_layout(title="Sentimentfordeling (nyheder)", height=300))
    return fig


def plot_most_mentioned(news_list: list, top_n: int = 10) -> go.Figure:
    """Bar-chart over de mest omtalte tickers i nyheder."""
    from collections import Counter
    all_tickers = [
        t for item in news_list
        for t in item.get("affected_tickers", [])
    ]
    if not all_tickers:
        return _empty_figure("Ingen ticker-data")

    counts  = Counter(all_tickers).most_common(top_n)
    tickers = [c[0] for c in counts]
    values  = [c[1] for c in counts]

    fig = go.Figure(go.Bar(
        x=tickers, y=values,
        marker_color=COLORS["blue"],
        text=values, textposition="outside",
    ))
    fig.update_layout(**_base_layout(
        title="Mest omtalte aktier i nyheder", height=300,
        yaxis_title="Antal omtaler",
    ))
    fig.update_yaxes(gridcolor="#2a2d3e")
    return fig


def _empty_figure(msg: str) -> go.Figure:
    """Tom figur med besked."""
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=COLORS["gray"], size=14),
    )
    fig.update_layout(**_base_layout(height=250))
    return fig