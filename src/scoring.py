# src/scoring.py — Transparent scoringmodel 0–100
from config import SCORING_WEIGHTS


def _news_sentiment_score(news_for_ticker: list) -> int:
    """
    Beregn gennemsnitlig sentiment-score for aktiens nyheder.
    Returnér bidrag til total-score.
    """
    if not news_for_ticker:
        return 0

    label_map = {
        "Meget positiv": SCORING_WEIGHTS["sentiment_very_positive"],
        "Positiv":        SCORING_WEIGHTS["sentiment_positive"],
        "Neutral":        SCORING_WEIGHTS["sentiment_neutral"],
        "Negativ":        SCORING_WEIGHTS["sentiment_negative"],
        "Meget negativ":  SCORING_WEIGHTS["sentiment_very_negative"],
    }

    scores = [
        label_map.get(item.get("sentiment", {}).get("label", "Neutral"), 0)
        for item in news_for_ticker
    ]
    if not scores:
        return 0
    return int(sum(scores) / len(scores))


def _volume_score(volume: float, avg_volume: float) -> int:
    """Score baseret på volumen ift. gennemsnit."""
    if not volume or not avg_volume or avg_volume == 0:
        return 0
    ratio = volume / avg_volume
    if ratio >= 3.0:
        return SCORING_WEIGHTS["volume_3x"]
    elif ratio >= 2.0:
        return SCORING_WEIGHTS["volume_2x"]
    elif ratio >= 1.5:
        return SCORING_WEIGHTS["volume_1_5x"]
    return 0


def _momentum_score(change_pct: float) -> int:
    """Score baseret på kursbevægelse."""
    if change_pct is None:
        return 0
    if change_pct >= 5.0:
        return SCORING_WEIGHTS["momentum_strong_up"]
    elif change_pct >= 2.0:
        return SCORING_WEIGHTS["momentum_up"]
    elif change_pct <= -5.0:
        return SCORING_WEIGHTS["momentum_strong_down"]
    elif change_pct <= -2.0:
        return SCORING_WEIGHTS["momentum_down"]
    return 0


def _mention_score(news_count: int) -> int:
    """Score baseret på antal nyhedsomtaler."""
    if news_count >= 5:
        return SCORING_WEIGHTS["mention_many"]
    elif news_count >= 2:
        return SCORING_WEIGHTS["mention_some"]
    return SCORING_WEIGHTS["mention_few"]


def calculate_scores(
    ticker_info: dict,
    news_for_ticker: list,
) -> dict:
    """
    Beregn alle scores for én aktie.
    Returnér dict med:
      - buy_score:       0–100 (høj = stor købsinteresse)
      - sell_score:      0–100 (høj = stort salgspres)
      - attention_score: 0–100 (høj = meget omtalt/usædvanlig)
      - news_impact:     0–100 (høj = stærk nyhedspåvirkning)
      - components:      detaljer om delscores
    """
    change_pct = ticker_info.get("change_pct", 0) or 0
    volume     = ticker_info.get("volume",     0) or 0
    avg_volume = ticker_info.get("avg_volume", 1) or 1
    news_count = len(news_for_ticker)

    sent  = _news_sentiment_score(news_for_ticker)
    vol   = _volume_score(volume, avg_volume)
    mom   = _momentum_score(change_pct)
    ment  = _mention_score(news_count)

    # ── Buy Interest Score ────────────────────────────────────────────────────
    # Høj score → positiv stemning + stigende volumen + positiv kurs
    buy_raw = (
        max(sent, 0)      +   # Kun positiv sentiment
        vol               +   # Høj volumen = interesse
        max(mom, 0)       +   # Kun positiv momentum
        ment                  # Omtale = interesse
    )
    buy_score = min(100, max(0, buy_raw + 30))   # Baseline 30

    # ── Sell Pressure Score ───────────────────────────────────────────────────
    sell_raw = (
        abs(min(sent, 0)) +   # Kun negativ sentiment
        vol               +   # Høj volumen kan indikere salg
        abs(min(mom, 0))  +   # Kun negativ momentum
        ment                  # Omtale øger usikkerhed
    )
    sell_score = min(100, max(0, sell_raw + 15))  # Lavere baseline

    # ── Attention Score ───────────────────────────────────────────────────────
    # Kombinerer volumen og omtale uanset retning
    attention_raw = vol + ment + abs(mom)
    attention_score = min(100, max(0, attention_raw + 20))

    # ── News Impact Score ─────────────────────────────────────────────────────
    if news_for_ticker:
        impact_map = {"Høj": 35, "Mellem": 20, "Lav": 8}
        impact_vals = [
            impact_map.get(
                item.get("sentiment", {}).get("impact", "Lav"), 5
            )
            for item in news_for_ticker
        ]
        news_impact = min(100, int(sum(impact_vals) / len(impact_vals) * 2))
    else:
        news_impact = 0

    # ── Verbal label ──────────────────────────────────────────────────────────
    def _buy_label(s: int) -> str:
        if s >= 75:  return "🟢 Høj købsinteresse"
        if s >= 55:  return "🟩 Moderat købsinteresse"
        if s >= 40:  return "⬜ Neutral interesse"
        if s >= 25:  return "🟥 Muligt salgspres"
        return "🔴 Stærkt salgspres"

    return {
        "buy_score":       buy_score,
        "sell_score":      sell_score,
        "attention_score": attention_score,
        "news_impact":     news_impact,
        "label":           _buy_label(buy_score),
        "components": {
            "sentiment_contribution": sent,
            "volume_contribution":    vol,
            "momentum_contribution":  mom,
            "mention_contribution":   ment,
            "news_count":             news_count,
            "change_pct":             change_pct,
            "vol_ratio":              round(volume / avg_volume, 2) if avg_volume else 0,
        },
    }


def score_label_to_interest(buy_score: int, sell_score: int) -> str:
    """Returnér et enkelt interesselabel baseret på begge scores."""
    diff = buy_score - sell_score
    if diff > 20:
        return "Høj købsinteresse"
    elif diff < -20:
        return "Muligt salgspres"
    elif buy_score > 60 and sell_score > 60:
        return "Høj usikkerhed"
    else:
        return "Neutral interesse"