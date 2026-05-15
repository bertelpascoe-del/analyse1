# src/macro_analyzer.py

import pandas as pd


MACRO_THEMES = {
    "Renter og centralbanker": {
        "keywords": [
            "fed", "federal reserve", "ecb", "central bank", "interest rate",
            "rate hike", "rate cut", "higher for longer", "monetary policy",
            "yield", "treasury yields", "bond yields"
        ],
        "positive_sectors": ["Financials"],
        "negative_sectors": ["Technology", "Real Estate", "Consumer Discretionary"],
        "impact": "Høj",
    },
    "Inflation": {
        "keywords": [
            "inflation", "cpi", "ppi", "consumer prices", "producer prices",
            "price pressures", "core inflation"
        ],
        "positive_sectors": ["Energy", "Consumer Staples"],
        "negative_sectors": ["Consumer Discretionary", "Technology", "Real Estate"],
        "impact": "Høj",
    },
    "Arbejdsløshed og vækst": {
        "keywords": [
            "jobs report", "unemployment", "nonfarm payrolls", "labor market",
            "wage growth", "gdp", "economic growth", "recession", "slowdown"
        ],
        "positive_sectors": ["Industrials", "Consumer Discretionary", "Financials"],
        "negative_sectors": ["Consumer Staples", "Utilities"],
        "impact": "Mellem",
    },
    "Olie og energi": {
        "keywords": [
            "oil", "crude", "brent", "wti", "opec", "energy prices",
            "gas prices", "natural gas"
        ],
        "positive_sectors": ["Energy"],
        "negative_sectors": ["Consumer Discretionary", "Industrials"],
        "impact": "Mellem",
    },
    "AI og teknologi": {
        "keywords": [
            "artificial intelligence", "ai", "machine learning", "data center",
            "cloud computing", "gpu", "chips", "semiconductor"
        ],
        "positive_sectors": ["Technology", "Communication Services"],
        "negative_sectors": [],
        "impact": "Høj",
    },
    "Semiconductors": {
        "keywords": [
            "semiconductor", "chip", "chips", "gpu", "foundry",
            "tsmc", "asml", "nvidia", "amd", "intel"
        ],
        "positive_sectors": ["Technology"],
        "negative_sectors": [],
        "impact": "Høj",
    },
    "Bank og kredit": {
        "keywords": [
            "bank", "banks", "credit", "loan losses", "deposit",
            "commercial real estate", "capital requirements", "liquidity"
        ],
        "positive_sectors": ["Financials"],
        "negative_sectors": ["Real Estate"],
        "impact": "Mellem",
    },
    "Forbrug og detailhandel": {
        "keywords": [
            "consumer spending", "retail sales", "shopping", "e-commerce",
            "consumer confidence", "household spending"
        ],
        "positive_sectors": ["Consumer Discretionary", "Consumer Staples"],
        "negative_sectors": [],
        "impact": "Mellem",
    },
    "Sundhed og pharma": {
        "keywords": [
            "drug approval", "fda", "clinical trial", "pharma",
            "biotech", "healthcare", "medicare", "weight loss drug"
        ],
        "positive_sectors": ["Healthcare"],
        "negative_sectors": [],
        "impact": "Mellem",
    },
    "Geopolitik og forsyningskæder": {
        "keywords": [
            "war", "geopolitical", "sanctions", "tariff", "trade war",
            "supply chain", "china tensions", "export controls"
        ],
        "positive_sectors": ["Energy", "Industrials"],
        "negative_sectors": ["Technology", "Consumer Discretionary"],
        "impact": "Høj",
    },
}


SECTOR_TO_TICKERS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "AMD", "INTC", "QCOM", "AVGO", "ASML", "TSM", "CRM", "ORCL", "ADBE"],
    "Financials": ["JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "AXP"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "BP", "SHEL"],
    "Healthcare": ["LLY", "JNJ", "PFE", "MRK", "ABBV", "UNH", "NVO"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "LOW", "NKE", "SBUX", "MCD"],
    "Consumer Staples": ["WMT", "COST", "KO", "PEP", "PG", "MDLZ"],
    "Industrials": ["BA", "CAT", "GE", "LMT", "UPS", "HON"],
    "Real Estate": ["AMT", "PLD", "SPG", "O"],
    "Communication Services": ["META", "GOOGL", "NFLX", "DIS", "T", "VZ"],
    "Materials": ["NEM", "FCX", "LIN", "APD"],
}


def _text_from_news_item(item):
    title = item.get("title", "")
    summary = item.get("summary", "")
    raw_text = item.get("raw_text", "")
    return f"{title} {summary} {raw_text}".lower()


def detect_macro_themes(news_item):
    """
    Finder makrotemaer i én nyhed.
    Returnerer liste af temaer med positivt/negativt påvirkede sektorer.
    """
    text = _text_from_news_item(news_item)
    themes_found = []

    for theme_name, theme_data in MACRO_THEMES.items():
        matched_keywords = [
            kw for kw in theme_data["keywords"]
            if kw.lower() in text
        ]

        if matched_keywords:
            themes_found.append(
                {
                    "theme": theme_name,
                    "matched_keywords": matched_keywords,
                    "positive_sectors": theme_data["positive_sectors"],
                    "negative_sectors": theme_data["negative_sectors"],
                    "impact": theme_data["impact"],
                }
            )

    return themes_found


def enrich_news_with_macro(news_items):
    """
    Tilføjer makrotemaer og sektorimpact til nyheder.
    """
    enriched = []

    for item in news_items:
        new_item = item.copy()
        macro_themes = detect_macro_themes(new_item)

        positive_sectors = set()
        negative_sectors = set()
        affected_sectors = set()
        macro_tickers = set()

        for theme in macro_themes:
            for sector in theme["positive_sectors"]:
                positive_sectors.add(sector)
                affected_sectors.add(sector)

                for ticker in SECTOR_TO_TICKERS.get(sector, []):
                    macro_tickers.add(ticker)

            for sector in theme["negative_sectors"]:
                negative_sectors.add(sector)
                affected_sectors.add(sector)

                for ticker in SECTOR_TO_TICKERS.get(sector, []):
                    macro_tickers.add(ticker)

        existing_tickers = set(new_item.get("affected_tickers", []))
        combined_tickers = sorted(existing_tickers.union(macro_tickers))

        new_item["macro_themes"] = macro_themes
        new_item["positive_sectors"] = sorted(list(positive_sectors))
        new_item["negative_sectors"] = sorted(list(negative_sectors))
        new_item["affected_sectors"] = sorted(list(affected_sectors))
        new_item["affected_tickers"] = combined_tickers

        enriched.append(new_item)

    return enriched


def sentiment_to_number(label):
    """
    Konverterer sentiment-label til numerisk score.
    """
    if not label:
        return 0

    label = str(label).lower()

    if "meget positiv" in label:
        return 2
    elif "positiv" in label:
        return 1
    elif "meget negativ" in label:
        return -2
    elif "negativ" in label:
        return -1
    else:
        return 0


def impact_to_weight(impact):
    """
    Konverterer impact-label til vægt.
    """
    if not impact:
        return 1

    impact = str(impact).lower()

    if "høj" in impact:
        return 3
    elif "mellem" in impact:
        return 2
    else:
        return 1


def calculate_sector_trends(news_items):
    """
    Beregner sektortrend ud fra nyheder, sentiment og makrotemaer.

    Positiv score = sektoren får positivt nyhedsflow.
    Negativ score = sektoren er under pres.
    """
    sector_scores = {}

    for item in news_items:
        sentiment = item.get("sentiment", {})
        sentiment_label = sentiment.get("label", "Neutral")
        base_sentiment = sentiment_to_number(sentiment_label)
        news_impact = impact_to_weight(sentiment.get("impact", "Lav"))

        positive_sectors = item.get("positive_sectors", [])
        negative_sectors = item.get("negative_sectors", [])
        affected_sectors = item.get("affected_sectors", [])

        for sector in affected_sectors:
            if sector not in sector_scores:
                sector_scores[sector] = {
                    "Sector": sector,
                    "Score": 0,
                    "Positive News": 0,
                    "Negative News": 0,
                    "Neutral News": 0,
                    "Total News": 0,
                    "Themes": set(),
                }

            sector_scores[sector]["Total News"] += 1

            for theme in item.get("macro_themes", []):
                sector_scores[sector]["Themes"].add(theme["theme"])

            directional_score = base_sentiment * news_impact

            if sector in positive_sectors:
                directional_score += 2 * news_impact

            if sector in negative_sectors:
                directional_score -= 2 * news_impact

            sector_scores[sector]["Score"] += directional_score

            if directional_score > 0:
                sector_scores[sector]["Positive News"] += 1
            elif directional_score < 0:
                sector_scores[sector]["Negative News"] += 1
            else:
                sector_scores[sector]["Neutral News"] += 1

    rows = []

    for sector, data in sector_scores.items():
        total = max(data["Total News"], 1)
        normalized_score = round(data["Score"] / total, 2)

        if normalized_score >= 2:
            trend = "🟢 På vej frem"
        elif normalized_score >= 0.5:
            trend = "🟩 Positivt momentum"
        elif normalized_score <= -2:
            trend = "🔴 Under pres"
        elif normalized_score <= -0.5:
            trend = "🟥 Svagt momentum"
        else:
            trend = "⬜ Neutral"

        rows.append(
            {
                "Sektor": sector,
                "Trend-score": normalized_score,
                "Trend": trend,
                "Positive nyheder": data["Positive News"],
                "Negative nyheder": data["Negative News"],
                "Neutrale nyheder": data["Neutral News"],
                "Antal nyheder": data["Total News"],
                "Temaer": ", ".join(sorted(list(data["Themes"]))),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Sektor",
                "Trend-score",
                "Trend",
                "Positive nyheder",
                "Negative nyheder",
                "Neutrale nyheder",
                "Antal nyheder",
                "Temaer",
            ]
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("Trend-score", ascending=False)

    return df


def get_macro_theme_summary(news_items):
    """
    Opsummerer hvilke makrotemaer der fylder mest i nyhedsflowet.
    """
    theme_counts = {}

    for item in news_items:
        for theme in item.get("macro_themes", []):
            theme_name = theme["theme"]

            if theme_name not in theme_counts:
                theme_counts[theme_name] = {
                    "Tema": theme_name,
                    "Antal nyheder": 0,
                    "Impact": theme["impact"],
                    "Nøgleord": set(),
                }

            theme_counts[theme_name]["Antal nyheder"] += 1

            for kw in theme.get("matched_keywords", []):
                theme_counts[theme_name]["Nøgleord"].add(kw)

    rows = []

    for theme_name, data in theme_counts.items():
        rows.append(
            {
                "Tema": data["Tema"],
                "Antal nyheder": data["Antal nyheder"],
                "Impact": data["Impact"],
                "Nøgleord": ", ".join(sorted(list(data["Nøgleord"]))[:8]),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["Tema", "Antal nyheder", "Impact", "Nøgleord"]
        )

    return pd.DataFrame(rows).sort_values("Antal nyheder", ascending=False)
