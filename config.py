# config.py — Centrale konfigurationsindstillinger

# ── Standardliste af tickers til markedsoverblik ──────────────────────────────
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "JPM", "V", "JNJ", "XOM", "WMT", "BAC", "LLY", "AMD",
]

# ── RSS-nyhedsfeeds ──────────────────────────────────────────────────────────
RSS_FEEDS = [
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
    },
    {
        "name": "CNBC Top News",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
    },
    {
        "name": "Seeking Alpha",
        "url": "https://seekingalpha.com/market_currents.xml",
    },
    {
        "name": "Investopedia",
        "url": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
    },
]

# ── Sektorer og tilhørende tickers ───────────────────────────────────────────
SECTOR_TICKERS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMD", "INTC", "QCOM", "ASML", "ARM"],
    "Financials": ["JPM", "BAC", "GS", "MS", "V", "MA"],
    "Healthcare": ["JNJ", "PFE", "MRK", "UNH", "ABBV", "LLY"],
    "Energy": ["XOM", "CVX", "COP", "SLB"],
    "Consumer Staples": ["WMT", "COST", "MCD", "PG", "KO", "PEP"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD"],
    "Communication Services": ["META", "DIS", "NFLX", "T", "VZ"],
    "Industrials": ["BA", "CAT", "GE", "LMT"],
    "Real Estate": ["AMT"],
    "Materials": ["NEM", "FCX"],
}

# ── Virksomhedsnavne → ticker ────────────────────────────────────────────────
COMPANY_ALIASES = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "amd": "AMD",
    "intel": "INTC",
    "qualcomm": "QCOM",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "visa": "V",
    "mastercard": "MA",
    "johnson & johnson": "JNJ",
    "pfizer": "PFE",
    "merck": "MRK",
    "exxon": "XOM",
    "chevron": "CVX",
    "walmart": "WMT",
    "costco": "COST",
    "mcdonald": "MCD",
    "coca-cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "boeing": "BA",
    "caterpillar": "CAT",
    "disney": "DIS",
    "netflix": "NFLX",
    "novo nordisk": "NOVO-B.CO",
    "maersk": "MAERSK-B.CO",
    "orsted": "ORSTED.CO",
    "openai": None,
    "anthropic": None,
}

# ── Sektorudløsere ───────────────────────────────────────────────────────────
SECTOR_TRIGGERS = {
    "semiconductor": ["NVDA", "AMD", "INTC", "QCOM", "ASML", "TSM", "ARM"],
    "ai": ["NVDA", "MSFT", "GOOGL", "META", "AMD", "AMZN"],
    "oil": ["XOM", "CVX", "COP", "SLB", "BP"],
    "bank": ["JPM", "BAC", "GS", "MS", "WFC"],
    "interest rate": ["JPM", "BAC", "GS", "AMT", "MSFT", "GOOGL"],
    "fed": ["JPM", "BAC", "GS", "V", "MA", "AMT"],
    "inflation": ["KO", "PEP", "WMT", "PG", "JPM", "BAC"],
    "electric vehicle": ["TSLA", "GM", "F", "RIVN"],
    "pharma": ["JNJ", "PFE", "MRK", "ABBV", "LLY"],
    "streaming": ["NFLX", "DIS", "AMZN"],
    "cloud": ["MSFT", "AMZN", "GOOGL"],
    "crypto": ["COIN", "MSTR", "SQ"],
}

# ── Scoringmodel-vægte ───────────────────────────────────────────────────────
SCORING_WEIGHTS = {
    "sentiment_very_positive": 25,
    "sentiment_positive": 15,
    "sentiment_neutral": 0,
    "sentiment_negative": -15,
    "sentiment_very_negative": -25,

    "volume_3x": 25,
    "volume_2x": 15,
    "volume_1_5x": 10,

    "momentum_strong_up": 20,
    "momentum_up": 10,
    "momentum_down": -10,
    "momentum_strong_down": -20,

    "mention_many": 20,
    "mention_some": 10,
    "mention_few": 0,
}

# ── Cache TTL, sekunder ──────────────────────────────────────────────────────
CACHE_TTL_MARKET = 300
CACHE_TTL_NEWS = 600

# ── Disclaimer ───────────────────────────────────────────────────────────────
DISCLAIMER = (
    "⚠️ Disclaimer: Dette dashboard er udelukkende til informations- og "
    "analyseformål og udgør ikke finansiel rådgivning. Historiske data og "
    "analyser er ingen garanti for fremtidige resultater. Tal altid med en "
    "certificeret finansiel rådgiver, inden du træffer investeringsbeslutninger."
)
