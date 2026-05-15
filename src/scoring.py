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
        "Positiv": SCORING_WEIGHTS["sentiment_positive"],
        "Neutral": SCORING_WEIGHTS["sentiment_neutral"],
        "Negativ": SCORING_WEIGHTS["sentiment_negative"],
        "Meget negativ": SCORING_WEIGHTS["sentiment_very_negative"],
    }

    scores = [
        label_map.get(item.get("sentiment", {}).get("label", "Neutral"), 0)
        for item in news_for_ticker
    ]

    if not scores:
        return 0

    return int(sum(scores) / len(scores))


def _volume_score(volume: float, avg_volume: float) -> int:
    """
    Score baseret på volumen ift. gennemsnit.
    """
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
    """
    Score baseret på kursbevægelse.
    """
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
    """
    Score baseret på antal nyhedsomtaler.
    """
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

    Returnerer:
      - buy_score: 0–100, høj = stor købsinteresse
      - sell_score: 0–100, høj = stort salgspres
      - attention_score: 0–100, høj = meget omtalt/usædvanlig
      - news_impact: 0–100, høj = stærk nyhedspåvirkning
      - components: detaljer om delscores
    """
    change_pct = ticker_info.get("change_pct", 0) or 0
    volume = ticker_info.get("volume", 0) or 0
    avg_volume = ticker_info.get("avg_volume", 1) or 1
    news_count = len(news_for_ticker)

    sent = _news_sentiment_score(news_for_ticker)
    vol = _volume_score(volume, avg_volume)
    mom = _momentum_score(change_pct)
    ment = _mention_score(news_count)

    # ── Buy Interest Score ────────────────────────────────────────────────────
    buy_raw = (
        max(sent, 0)
        + vol
        + max(mom, 0)
        + ment
    )
    buy_score = min(100, max(0, buy_raw + 30))

    # ── Sell Pressure Score ───────────────────────────────────────────────────
    sell_raw = (
        abs(min(sent, 0))
        + vol
        + abs(min(mom, 0))
        + ment
    )
    sell_score = min(100, max(0, sell_raw + 15))

    # ── Attention Score ───────────────────────────────────────────────────────
    attention_raw = vol + ment + abs(mom)
    attention_score = min(100, max(0, attention_raw + 20))

    # ── News Impact Score ─────────────────────────────────────────────────────
    if news_for_ticker:
        impact_map = {
            "Høj": 35,
            "Mellem": 20,
            "Lav": 8,
        }

        impact_vals = [
            impact_map.get(
                item.get("sentiment", {}).get("impact", "Lav"),
                5,
            )
            for item in news_for_ticker
        ]

        news_impact = min(100, int(sum(impact_vals) / len(impact_vals) * 2))
    else:
        news_impact = 0

    def _buy_label(score: int) -> str:
        if score >= 75:
            return "🟢 Høj købsinteresse"
        if score >= 55:
            return "🟩 Moderat købsinteresse"
        if score >= 40:
            return "⬜ Neutral interesse"
        if score >= 25:
            return "🟥 Muligt salgspres"
        return "🔴 Stærkt salgspres"

    return {
        "buy_score": buy_score,
        "sell_score": sell_score,
        "attention_score": attention_score,
        "news_impact": news_impact,
        "label": _buy_label(buy_score),
        "components": {
            "sentiment_contribution": sent,
            "volume_contribution": vol,
            "momentum_contribution": mom,
            "mention_contribution": ment,
            "news_count": news_count,
            "change_pct": change_pct,
            "vol_ratio": round(volume / avg_volume, 2) if avg_volume else 0,
        },
    }


def score_label_to_interest(buy_score: int, sell_score: int) -> str:
    """
    Returnér et enkelt interesselabel baseret på både købsinteresse og salgspres.
    """
    diff = buy_score - sell_score

    if diff > 20:
        return "Høj købsinteresse"
    elif diff < -20:
        return "Muligt salgspres"
    elif buy_score > 60 and sell_score > 60:
        return "Høj usikkerhed"
    else:
        return "Neutral interesse"


def calculate_research_candidate_score(row, scores: dict) -> dict:
    """
    Beregner en research-score fra 0–100.

    Dette er ikke en købsanbefaling.
    Scoren bruges kun til at finde aktier, som kan være værd at undersøge nærmere.
    """

    try:
        change_pct = float(row.get("Ændring (%)", 0) or 0)
    except Exception:
        change_pct = 0

    try:
        vol_avg = float(row.get("Vol/Avg", 1) or 1)
    except Exception:
        vol_avg = 1

    buy_score = scores.get("buy_score", 0)
    sell_score = scores.get("sell_score", 0)
    attention_score = scores.get("attention_score", 0)
    news_impact = scores.get("news_impact", 0)

    research_score = 0

    # Købsinteresse, max 35 point
    research_score += min(buy_score * 0.35, 35)

    # Opmærksomhed, max 15 point
    research_score += min(attention_score * 0.15, 15)

    # Nyhedspåvirkning, max 10 point
    research_score += min(news_impact * 0.10, 10)

    # Momentum
    if change_pct > 5:
        research_score += 20
    elif change_pct > 2:
        research_score += 14
    elif change_pct > 0:
        research_score += 8
    elif change_pct < -5:
        research_score -= 15
    elif change_pct < -2:
        research_score -= 8

    # Volumen relativt til gennemsnit
    if vol_avg >= 3:
        research_score += 15
    elif vol_avg >= 2:
        research_score += 10
    elif vol_avg >= 1.5:
        research_score += 6

    # Straf for højt salgspres
    research_score -= min(sell_score * 0.25, 25)

    # Begræns til 0–100
    research_score = max(0, min(100, round(research_score, 1)))

    if research_score >= 75:
        label = "Stærk research-kandidat"
    elif research_score >= 60:
        label = "Interessant momentum-kandidat"
    elif research_score >= 45:
        label = "Neutral/overvåg"
    elif research_score >= 30:
        label = "Svag kandidat"
    else:
        label = "Lav prioritet"

    return {
        "research_score": research_score,
        "research_label": label,
    }
