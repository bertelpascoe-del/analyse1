# pages/5_Methodology.py — Metode, datakilder og disclaimer
import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DISCLAIMER

st.set_page_config(page_title="Metode & Disclaimer", page_icon="📖", layout="wide")

st.title("📖 Metode & Disclaimer")
st.error(DISCLAIMER)

st.markdown("""
---
## Datakilder

| Kilde | Hvad | API-nøgle? |
|-------|------|------------|
| **yfinance** | Markedsdata, kurser, nøgletal, nyheder | Nej — gratis |
| **RSS-feeds** | Markedsnyheder (Reuters, CNBC, MarketWatch) | Nej — gratis |
| **NewsAPI** | Udvidede nyhedsresultater | Ja (valgfrit) |
| **Finnhub** | Nyheder og finansielle data | Ja (valgfrit) |
| **VADER Sentiment** | Sentiment-analyse | Nej — lokal |

---
## Scoringmodel

Alle scores beregnes på en skala fra **0–100** og er udelukkende vejledende.

### Buy Interest Score
Estimerer, hvor stor markedsinteressen er fra købesiden:

| Faktor | Bidrag |
|--------|--------|
| Meget positiv nyhedssentiment | +25 |
| Positiv nyhedssentiment | +15 |
| Neutral sentiment | 0 |
| Negativ sentiment | −15 |
| Meget negativ sentiment | −25 |
| Volumen > 3x gennemsnit | +25 |
| Volumen > 2x gennemsnit | +15 |
| Volumen > 1,5x gennemsnit | +10 |
| Kurs op > 5% | +20 |
| Kurs op 2–5% | +10 |
| Kurs ned 2–5% | −10 |
| Kurs ned > 5% | −20 |
| Mange nyhedsomtaler (≥5) | +20 |
| Få nyhedsomtaler (≥2) | +10 |

**Baseline:** +30 (neutral udgangspunkt).

### Sell Pressure Score
Estimerer, om der er salgspres på en aktie — baseret på negative signaler + høj volumen
(høj volumen på en faldende dag kan indikere salg).

### Attention Score
Kombinerer volumen, omtale og kursbevægelse — uanset retning.
En høj score betyder, at aktien tiltrækker usædvanligt meget opmærksomhed.

### News Impact Score
Beregnet ud fra den gennemsnitlige påvirkningsgrad af relaterede nyheder
(Høj = 35p, Mellem = 20p, Lav = 8p).

---
## Sentimentanalyse

Appen bruger **VADER** (Valence Aware Dictionary and sEntiment Reasoner) som base,
kombineret med en brugerdefineret ordliste af **finansielle nøgleord**:

- `"beats expectations"` → +0.40
- `"sec investigation"` → −0.45
- `"rate cut"` → +0.20 (generelt)
- `"interest rate hike"` → +0.15 for Financials, −0.15 for Technology

VADER er optimeret til sociale medier og korte tekster — den er ikke perfekt til finansielle
artikler, men giver et rimeligt startpunkt for en MVP.

**Begrænsninger:**
- Ironi og sarkasme fanges ikke
- Kontekstuelle nuancer (fx "layoffs" kan være positivt) er kun delvist håndteret
- Sentiment på ikke-engelske tekster er upålidelig

---
## Kobling af nyheder til aktier

Appen bruger tre metoder:

1. **Direkte ticker-matching** — finder `$AAPL` eller `NVDA` i artiklens tekst
2. **Virksomhedsnavn-aliaser** — kobler "Apple" → `AAPL`, "Novo Nordisk" → `NOVO-B.CO` osv.
3. **Sektor-triggers** — nøgleord som `"semiconductor"`, `"interest rate"`, `"oil"` 
   udløser en liste af typisk berørte aktier

---
## Tekniske begrænsninger

- **yfinance** er ikke officielt supporteret af Yahoo Finance og kan fejle
- **RSS-feeds** ændrer struktur over tid — nogle feeds kan holde op med at virke
- **Gratis API-nøgler** (Finnhub, NewsAPI) har begrænsede kald per dag
- Sentimentmodellen er en simpel heuristik — **ikke en finansiel model**
- Data caches i **5–10 minutter** for at undgå overbelastning af API'er
- Appen har **ingen historisk sentimentdatabase** — alt beregnes i realtid

---
## Vigtig disclaimer

> **Dette dashboard er udelukkende til informations- og analyseformål.**
> Det udgør ikke finansiel rådgivning, anbefalinger om køb eller salg,
> eller nogen form for investeringsrådgivning.
>
> Historiske data, scores og sentimentanalyser er **ingen garanti** for
> fremtidige prisbevægelser eller afkast.
>
> Konsultér altid en **autoriseret finansiel rådgiver** inden du træffer
> investeringsbeslutninger.
""")