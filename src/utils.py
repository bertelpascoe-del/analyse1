from datetime import datetime, time
import pytz


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
