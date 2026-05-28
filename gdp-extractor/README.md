# 📊 GDP Data Extractor

> Interactive GDP explorer powered by the **World Bank Open Data API** — no API key needed.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![World Bank API](https://img.shields.io/badge/Data-World%20Bank%20API-009FDA)](https://data.worldbank.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- 🌍 **40+ countries** — search and select multiple at once
- 📅 **1960–2023** — full historical range via World Bank API
- 📈 **3 chart types** — Line, Bar, Area (with optional log scale)
- 💾 **CSV export** — one-click download of the raw wide-format table
- ⚡ **Response caching** — repeated queries are served instantly (1 hr TTL)
- 🔢 **Metric cards** — latest GDP for each selected country at a glance

---

## Quick start

```bash
# 1. clone
git clone https://github.com/Heliodroid/GDP-data-extractor.git
cd gdp-extractor

# 2. install deps
pip install -r requirements.txt

# 3. run
streamlit run app.py
```

App opens at `http://localhost:8501`.

---

## Data source

All data is fetched live from the **World Bank Open Data API**:

```
https://api.worldbank.org/v2/country/{code}/indicator/NY.GDP.MKTP.CD
```

- **Indicator**: `NY.GDP.MKTP.CD` — GDP, current USD
- **No authentication required**
- **Rate limits**: generous for normal use; responses are cached for 1 hour via `@st.cache_data`

> **Note**: World Bank data for the most recent 1–2 years may be incomplete as national accounts take time to compile.

---

## Project structure

```
gdp-extractor/
├── app.py              # main Streamlit app
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

---

## Deployment (Streamlit Community Cloud)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set **Main file path** to `app.py`
4. Deploy — done

No secrets or env vars needed.

---

## License

[MIT](LICENSE) — free to use, fork, and extend.
