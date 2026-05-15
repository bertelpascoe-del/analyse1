# src/sentiment.py — Finansielt-bevidst sentimentanalyse via VADER
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Finansielle nøgleord med manuelle score-justeringer
FINANCIAL_BOOSTS = {
    # Stærkt positive
    "beats expectations":   +0.4,
    "beat expectations":    +0.4,
    "earnings beat":        +0.4,
    "record revenue":       +0.35,
    "raised guidance":      +0.35,
    "dividend increase":    +0.3,
    "buyback":              +0.25,
    "upgraded":             +0.25,
    "strong growth":        +0.25,
    "partnership":          +0.15,
    "acquisition":          +0.10,

    # Positive
    "profit rise":          +0.2,
    "revenue growth":       +0.2,
    "market share":         +0.1,

    # Neutrale / kontekst-afhængige
    "layoffs":              -0.05,   # Kan være positivt (effektivisering)
    "merger":                0.0,
    "restructuring":        -0.05,

    # Negative
    "misses expectations":  -0.4,
    "missed expectations":  -0.4,
    "earnings miss":        -0.4,
    "revenue miss":         -0.35,
    "lowered guidance":     -0.35,
    "downgraded":           -0.25,
    "sec investigation":    -0.45,
    "fraud":                -0.5,
    "bankruptcy":           -0.55,
    "recall":               -0.3,
    "data breach":          -0.3,
    "lawsuit":              -0.2,
    "fine":                 -0.15,
    "tariff":               -0.15,
    "supply chain":         -0.1,

    # Makro-nøgleord
    "interest rate hike":   -0.2,
    "rate cut":             +0.2,
    "inflation":            -0.1,
    "recession":            -0.35,
}

# Sektorspecifikke justeringer: (nøgleord, sektor_der_påvirkes, retning)
SECTOR_CONTEXT = {
    "oil price increase": {
        "Energy":            +0.3,
        "Industrials":      -0.1,
        "Consumer Staples": -0.1,
    },
    "interest rate hike": {
        "Financials":        +0.15,
        "Technology":       -0.15,
        "Real Estate":      -0.25,
    },
    "rate cut": {
        "Financials":       -0.1,
        "Technology":       +0.15,
        "Real Estate":      +0.2,
    },
    "layoffs": {
        "Technology":       +0.1,   # Markedet ser ofte positivt på effektivisering
    },
}


class SentimentAnalyzer:
    """Finansielt-bevidst sentimentanalyse."""

    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()

    def analyze(self, text: str, sector: str = None) -> dict:
        """
        Analyser tekst og returnér:
          - score:       float fra -1 (meget negativ) til +1 (meget positiv)
          - label:       str, fx 'Positiv'
          - explanation: str, kortforklaring
          - triggers:    list af fundne finansielle nøgleord
        """
        if not text or not isinstance(text, str):
            return self._neutral_result()

        text_lower = text.lower()

        # Basis VADER-score
        vader_scores = self._vader.polarity_scores(text)
        base_score   = vader_scores["compound"]   # [-1, 1]

        # Finansielle boosters
        boost    = 0.0
        triggers = []
        for keyword, adjustment in FINANCIAL_BOOSTS.items():
            if keyword in text_lower:
                boost += adjustment
                triggers.append(keyword)

        # Sektorjustering
        sector_note = ""
        if sector:
            for kw, sector_map in SECTOR_CONTEXT.items():
                if kw in text_lower and sector in sector_map:
                    extra = sector_map[sector]
                    boost += extra
                    sector_note = (
                        f" Særligt for sektoren '{sector}': "
                        f"{'positiv' if extra > 0 else 'negativ'} effekt."
                    )

        # Kombineret score (clamp til [-1, 1])
        final_score = max(-1.0, min(1.0, base_score + boost))

        label       = self._score_to_label(final_score)
        explanation = self._build_explanation(
            base_score, boost, triggers, sector_note, label
        )

        return {
            "score":       round(final_score, 3),
            "label":       label,
            "explanation": explanation,
            "triggers":    triggers,
            "impact":      self._impact_level(abs(final_score)),
        }

    # ── Private hjælpemetoder ─────────────────────────────────────────────────

    def _score_to_label(self, score: float) -> str:
        if score >= 0.35:
            return "Meget positiv"
        elif score >= 0.10:
            return "Positiv"
        elif score <= -0.35:
            return "Meget negativ"
        elif score <= -0.10:
            return "Negativ"
        else:
            return "Neutral"

    def _impact_level(self, abs_score: float) -> str:
        if abs_score >= 0.45:
            return "Høj"
        elif abs_score >= 0.20:
            return "Mellem"
        else:
            return "Lav"

    def _build_explanation(
        self, base: float, boost: float, triggers: list,
        sector_note: str, label: str
    ) -> str:
        parts = [f"Samlet vurdering: **{label}**."]
        if triggers:
            kw = ", ".join(f"*{t}*" for t in triggers[:3])
            parts.append(f"Finansielle signaler fundet: {kw}.")
        if abs(boost) > 0.05:
            retning = "opjusteret" if boost > 0 else "nedjusteret"
            parts.append(
                f"Basis tekstscore {retning} med {abs(boost):.2f} "
                f"pga. finansielle nøgleord."
            )
        if sector_note:
            parts.append(sector_note)
        return " ".join(parts)

    def _neutral_result(self) -> dict:
        return {
            "score":       0.0,
            "label":       "Neutral",
            "explanation": "Ingen tekst at analysere.",
            "triggers":    [],
            "impact":      "Lav",
        }


# Singleton-instans
_analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str, sector: str = None) -> dict:
    """Public API — analyser sentiment for en tekst."""
    return _analyzer.analyze(text, sector)