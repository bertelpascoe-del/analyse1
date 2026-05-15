# src/utils.py

from datetime import datetime, time
import pytz


def format_number(value):
    """
    Formaterer store tal pænt.
    Eksempel: 1500000 -> 1.50M
    """
    try:
        if value is None:
            return "N/A"

        value = float(value)

        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.2f}K"
        else:
            return f"{value:.0f}"

    except Exception:
        return "N/A"


def format_percent(value):
    """
    Formaterer procenttal.
    Eksempel: 2.345 -> +2.35%
    """
    try:
        if value is None:
            return "N/A"

        value = float(value)
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.2f}%"

    except Exception:
        return "N/A"


def color_for_change(value):
    """
    Returnerer farve baseret på positiv/negativ ændring.
    """
    try:
        value = float(value)

        if value > 0:
            return "#00c853"
        elif value < 0:
            return "#d50000"
        else:
            return "#9e9e9e"

    except Exception:
        return "#9e9e9e"


def get_market_status():
    """
    Simpel markedsstatus for USA-markedet.
    Tager højde for lokal New York-tid og weekend,
    men ikke helligdage.
    """
    tz = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    current_time = now.time()
    weekday = now.weekday()

    market_open = time(9, 30)
    market_close = time(16, 0)
    pre_market_open = time(4, 0)
    after_hours_close = time(20, 0)

    if weekday >= 5:
        return {
            "status": "Lukket",
            "color": "#d50000",
            "local_time": now.strftime("%H:%M"),
        }

    if market_open <= current_time <= market_close:
        return {
            "status": "Åbent",
            "color": "#00c853",
            "local_time": now.strftime("%H:%M"),
        }

    if pre_market_open <= current_time < market_open:
        return {
            "status": "Pre-market",
            "color": "#ffab00",
            "local_time": now.strftime("%H:%M"),
        }

    if market_close < current_time <= after_hours_close:
        return {
            "status": "After-hours",
            "color": "#ffab00",
            "local_time": now.strftime("%H:%M"),
        }

    return {
        "status": "Lukket",
        "color": "#d50000",
        "local_time": now.strftime("%H:%M"),
    }


GLOBAL_MARKETS = [
    {
        "name": "USA - NYSE/Nasdaq",
        "timezone": "America/New_York",
        "open": time(9, 30),
        "close": time(16, 0),
        "pre_open": time(4, 0),
        "after_close": time(20, 0),
        "emoji": "🇺🇸",
    },
    {
        "name": "Danmark - Nasdaq Copenhagen",
        "timezone": "Europe/Copenhagen",
        "open": time(9, 0),
        "close": time(17, 0),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇩🇰",
    },
    {
        "name": "Tyskland - Xetra",
        "timezone": "Europe/Berlin",
        "open": time(9, 0),
        "close": time(17, 30),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇩🇪",
    },
    {
        "name": "Storbritannien - LSE",
        "timezone": "Europe/London",
        "open": time(8, 0),
        "close": time(16, 30),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇬🇧",
    },
    {
        "name": "Japan - Tokyo Stock Exchange",
        "timezone": "Asia/Tokyo",
        "open": time(9, 0),
        "close": time(15, 30),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇯🇵",
    },
    {
        "name": "Hong Kong - HKEX",
        "timezone": "Asia/Hong_Kong",
        "open": time(9, 30),
        "close": time(16, 0),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇭🇰",
    },
    {
        "name": "Kina - Shanghai",
        "timezone": "Asia/Shanghai",
        "open": time(9, 30),
        "close": time(15, 0),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇨🇳",
    },
    {
        "name": "Australien - ASX",
        "timezone": "Australia/Sydney",
        "open": time(10, 0),
        "close": time(16, 0),
        "pre_open": None,
        "after_close": None,
        "emoji": "🇦🇺",
    },
]


def get_global_market_status():
    """
    Returnerer markedsstatus for større globale aktiemarkeder.

    Bemærk:
    Denne simple version tager højde for lokal tid og weekender,
    men ikke helligdage eller særlige lukkedage.
    """

    markets_status = []

    for market in GLOBAL_MARKETS:
        tz = pytz.timezone(market["timezone"])
        now = datetime.now(tz)
        current_time = now.time()
        weekday = now.weekday()

        is_weekend = weekday >= 5

        if is_weekend:
            status = "Lukket"
            status_type = "closed"
            color = "#d50000"

        elif market["open"] <= current_time <= market["close"]:
            status = "Åbent"
            status_type = "open"
            color = "#00c853"

        elif (
            market["pre_open"] is not None
            and market["pre_open"] <= current_time < market["open"]
        ):
            status = "Pre-market"
            status_type = "pre_market"
            color = "#ffab00"

        elif (
            market["after_close"] is not None
            and market["close"] < current_time <= market["after_close"]
        ):
            status = "After-hours"
            status_type = "after_hours"
            color = "#ffab00"

        else:
            status = "Lukket"
            status_type = "closed"
            color = "#d50000"

        markets_status.append(
            {
                "name": market["name"],
                "emoji": market["emoji"],
                "status": status,
                "status_type": status_type,
                "color": color,
                "local_time": now.strftime("%H:%M"),
                "timezone": market["timezone"],
                "open": market["open"].strftime("%H:%M"),
                "close": market["close"].strftime("%H:%M"),
            }
        )

    return markets_status

def sentiment_label_to_emoji(label):
    """
    Konverterer sentiment-label til emoji.
    Bruges fx i News Center.
    """

    if label is None:
        return "⚪"

    label = str(label).lower()

    if "meget positiv" in label:
        return "🟢🚀"
    elif "positiv" in label:
        return "🟢"
    elif "meget negativ" in label:
        return "🔴⚠️"
    elif "negativ" in label:
        return "🔴"
    elif "neutral" in label:
        return "⚪"
    else:
        return "⚪"
