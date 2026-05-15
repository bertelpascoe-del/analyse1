# src/utils.py — Hjælpefunktioner
from datetime import datetime, time
import pytz
import re


def format_number(n, decimals: int = 2) -> str:
    """Formatér et tal til læsevenlig streng, fx 1234567 → '1.23M'."""
    if n is None:
        return "N/A"
    try:
        n = float(n)
        if abs(n) >= 1_000_000_000:
            return f"{n / 1_000_000_000:.{decimals}f}B"
        elif abs(n) >= 1_000_000:
            return f"{n / 1_000_000:.{decimals}f}M"
        elif abs(n) >= 1_000:
            return f"{n / 1_000:.{decimals}f}K"
        else:
            return f"{n:.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"


def format_percent(n, show_sign: bool = True) -> str:
    """Formatér procent med fortegn, fx 0.032 → '+3.20%'."""
    if n is None:
        return "N/A"
    try:
        n = float(n)
        sign = "+" if n > 0 and show_sign else ""
        return f"{sign}{n:.2f}%"
    except (ValueError, TypeError):
        return "N/A"


def color_for_change(value: float) -> str:
    """Returnér CSS-farve baseret på positiv/negativ ændring."""
    try:
        if float(value) > 0:
            return "#00c853"
        elif float(value) < 0:
            return "#d50000"
        else:
            return "#9e9e9e"
    except (ValueError, TypeError):
        return "#9e9e9e"


def get_market_status() -> dict:
    """
    Returnér status for det amerikanske aktiemarked (NYSE/NASDAQ).
    Åbningstider: hverdage 09:30–16:00 ET.
    """
    et = pytz.timezone("America/New_York")
    now_et = datetime.now(et)
    weekday = now_et.weekday()   # 0=man, 6=søn
    current_time = now_et.time()

    market_open  = time(9, 30)
    market_close = time(16, 0)
    pre_open     = time(4, 0)
    after_close  = time(20, 0)

    if weekday >= 5:
        return {"status": "Lukket (weekend)", "color": "#9e9e9e", "open": False}
    elif market_open <= current_time <= market_close:
        return {"status": "🟢 Marked åbent", "color": "#00c853", "open": True}
    elif pre_open <= current_time < market_open:
        return {"status": "🟡 Pre-market", "color": "#ffab00", "open": False}
    elif market_close < current_time <= after_close:
        return {"status": "🟡 After-hours", "color": "#ffab00", "open": False}
    else:
        return {"status": "🔴 Marked lukket", "color": "#d50000", "open": False}


def safe_get(d: dict, *keys, default=None):
    """Sikker nested dict-opslag uden KeyError."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def extract_tickers_from_text(text: str) -> list:
    """Find ticker-symboler i en tekst, fx '$AAPL' eller 'NVDA'."""
    # $TICKER eller store bogstaver 1-5 tegn
    dollar_tickers = re.findall(r'\$([A-Z]{1,5})', text)
    word_tickers   = re.findall(r'\b([A-Z]{2,5})\b', text)
    combined = list(set(dollar_tickers + word_tickers))
    # Filtrer almindelige ord fra
    stopwords = {
        "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU",
        "ALL", "CAN", "HER", "WAS", "ONE", "OUR", "OUT",
        "DAY", "GET", "HAS", "HIM", "HIS", "HOW", "ITS",
        "NEW", "NOW", "OLD", "SEE", "TWO", "WHO", "DID",
        "US", "AM", "PM", "ET", "CEO", "CFO", "IPO", "ETF",
        "NYSE", "NASDAQ", "SEC", "FED", "GDP", "CPI", "EPS",
    }
    return [t for t in combined if t not in stopwords and len(t) >= 2]


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Afkort tekst og tilføj '…'."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def sentiment_label_to_emoji(label: str) -> str:
    mapping = {
        "Meget positiv": "🟢",
        "Positiv":        "🟩",
        "Neutral":        "⬜",
        "Negativ":        "🟥",
        "Meget negativ":  "🔴",
    }
    return mapping.get(label, "⬜")