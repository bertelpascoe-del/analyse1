<<<<<<< Updated upstream
# 📈 Aktie- & Nyhedsdashboard

Et Streamlit-dashboard til analyse af aktiemarkedet — **ikke finansiel rådgivning**.

## Funktioner

- **Markedsoverblik** — priser, daglig ændring, volumen, top-vindere og -tabere
- **Aktiescreener** — filtrer og sorter aktier på tværs af sektorer og scores
- **Nyhedscenter** — nyheder fra RSS-feeds med sentiment og ticker-kobling
- **Aktie-profil** — kursgraf, RSI, SMA, scoring og nyheder for én aktie
- **Sektoranalyse** — heatmap og nyheder aggregeret per sektor

## Hurtig start

```bash
# 1. Klon repo
git clone https://github.com/DIT-BRUGERNAVN/stock-dashboard.git
cd stock-dashboard

# 2. Installér afhængigheder
pip install -r requirements.txt

# 3. (Valgfrit) Opret .env med API-nøgler
cp .env.example .env
# Rediger .env med dine nøgler

# 4. Start appen
streamlit run app.py
```

Appen virker **uden API-nøgler** via yfinance og gratis RSS-feeds.

## API-nøgler (valgfrit)

Opret filen `.streamlit/secrets.toml`:

```toml
NEWS_API_KEY      = "din_nøgle"
FINNHUB_API_KEY   = "din_nøgle"
ALPHA_VANTAGE_KEY = "din_nøgle"
FMP_API_KEY       = "din_nøgle"
```

Appen bruger automatisk disse nøgler, hvis de er til stede —
og falder tilbage til gratis kilder, hvis de mangler.

## Deployment på Streamlit Community Cloud

1. Push koden til GitHub (public repo)
2. Gå til [share.streamlit.io](https://share.streamlit.io)
3. Klik **New app** → vælg dit repo → `app.py`
4. Under **Advanced settings → Secrets**, indsæt dit `secrets.toml`-indhold
5. Klik **Deploy**

## Projektstruktur

```
stock-dashboard/
├── app.py                   # Forside
├── config.py                # Konfiguration
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── tickers.csv          # Ticker-liste med sektor
├── src/
│   ├── market_data.py       # yfinance-integration
│   ├── news_fetcher.py      # RSS + valgfrie API'er
│   ├── sentiment.py         # VADER + finansielle boosters
│   ├── stock_mapper.py      # Nyhed → ticker-kobling
│   ├── scoring.py           # Buy/Sell/Attention score
│   ├── charts.py            # Plotly-visualiseringer
│   └── utils.py             # Hjælpefunktioner
└── pages/
    ├── 1_Stock_Screener.py
    ├── 2_News_Center.py
    ├── 3_Stock_Profile.py
    ├── 4_Sector_Analysis.py
    └── 5_Methodology.py
```

## Disclaimer

> Dette dashboard er udelukkende til informations- og analyseformål
=======
# 📈 Aktie- & Nyhedsdashboard

Et Streamlit-dashboard til analyse af aktiemarkedet — **ikke finansiel rådgivning**.

## Funktioner

- **Markedsoverblik** — priser, daglig ændring, volumen, top-vindere og -tabere
- **Aktiescreener** — filtrer og sorter aktier på tværs af sektorer og scores
- **Nyhedscenter** — nyheder fra RSS-feeds med sentiment og ticker-kobling
- **Aktie-profil** — kursgraf, RSI, SMA, scoring og nyheder for én aktie
- **Sektoranalyse** — heatmap og nyheder aggregeret per sektor

## Hurtig start

```bash
# 1. Klon repo
git clone https://github.com/DIT-BRUGERNAVN/stock-dashboard.git
cd stock-dashboard

# 2. Installér afhængigheder
pip install -r requirements.txt

# 3. (Valgfrit) Opret .env med API-nøgler
cp .env.example .env
# Rediger .env med dine nøgler

# 4. Start appen
streamlit run app.py
```

Appen virker **uden API-nøgler** via yfinance og gratis RSS-feeds.

## API-nøgler (valgfrit)

Opret filen `.streamlit/secrets.toml`:

```toml
NEWS_API_KEY      = "din_nøgle"
FINNHUB_API_KEY   = "din_nøgle"
ALPHA_VANTAGE_KEY = "din_nøgle"
FMP_API_KEY       = "din_nøgle"
```

Appen bruger automatisk disse nøgler, hvis de er til stede —
og falder tilbage til gratis kilder, hvis de mangler.

## Deployment på Streamlit Community Cloud

1. Push koden til GitHub (public repo)
2. Gå til [share.streamlit.io](https://share.streamlit.io)
3. Klik **New app** → vælg dit repo → `app.py`
4. Under **Advanced settings → Secrets**, indsæt dit `secrets.toml`-indhold
5. Klik **Deploy**

## Projektstruktur

```
stock-dashboard/
├── app.py                   # Forside
├── config.py                # Konfiguration
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── tickers.csv          # Ticker-liste med sektor
├── src/
│   ├── market_data.py       # yfinance-integration
│   ├── news_fetcher.py      # RSS + valgfrie API'er
│   ├── sentiment.py         # VADER + finansielle boosters
│   ├── stock_mapper.py      # Nyhed → ticker-kobling
│   ├── scoring.py           # Buy/Sell/Attention score
│   ├── charts.py            # Plotly-visualiseringer
│   └── utils.py             # Hjælpefunktioner
└── pages/
    ├── 1_Stock_Screener.py
    ├── 2_News_Center.py
    ├── 3_Stock_Profile.py
    ├── 4_Sector_Analysis.py
    └── 5_Methodology.py
```

## Disclaimer

> Dette dashboard er udelukkende til informations- og analyseformål
>>>>>>> Stashed changes
> og udgør **ikke** finansiel rådgivning.