import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(
    page_title="GDP Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── constants ──────────────────────────────────────────────────────────────────
WB_BASE = "https://api.worldbank.org/v2"
INDICATOR = "NY.GDP.MKTP.CD"   # GDP current USD

COUNTRIES = {
    "World": "1W", "India": "IN", "United States": "US", "China": "CN",
    "Germany": "DE", "Japan": "JP", "United Kingdom": "GB", "France": "FR",
    "Brazil": "BR", "Canada": "CA", "Italy": "IT", "South Korea": "KR",
    "Australia": "AU", "Russia": "RU", "Mexico": "MX", "Indonesia": "ID",
    "Netherlands": "NL", "Saudi Arabia": "SA", "Turkey": "TR",
    "Switzerland": "CH", "Poland": "PL", "Argentina": "AR", "Sweden": "SE",
    "Belgium": "BE", "Thailand": "TH", "Nigeria": "NG", "South Africa": "ZA",
    "Singapore": "SG", "Malaysia": "MY", "Egypt": "EG", "Vietnam": "VN",
    "Chile": "CL", "Colombia": "CO", "Pakistan": "PK", "Bangladesh": "BD",
    "Kenya": "KE", "Ethiopia": "ET", "Ghana": "GH", "Morocco": "MA",
    "Ukraine": "UA", "Kazakhstan": "KZ", "Philippines": "PH",
    "New Zealand": "NZ", "Portugal": "PT", "Greece": "GR",
}

# ── helpers ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_gdp(country_code: str, start: int, end: int) -> pd.DataFrame:
    """Fetch GDP time series from World Bank API for one country."""
    url = (
        f"{WB_BASE}/country/{country_code}/indicator/{INDICATOR}"
        f"?date={start}:{end}&format=json&per_page=100"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        payload = r.json()
        if len(payload) < 2 or not payload[1]:
            return pd.DataFrame()
        rows = [
            {"year": int(d["date"]), "gdp_usd": d["value"]}
            for d in payload[1]
            if d["value"] is not None
        ]
        df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
        return df
    except Exception as e:
        st.warning(f"Could not fetch {country_code}: {e}")
        return pd.DataFrame()


def fmt_gdp(val: float) -> str:
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    if val >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def build_wide_df(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge per-country DataFrames into one wide DataFrame."""
    frames = []
    for country, df in data.items():
        if df.empty:
            continue
        tmp = df.rename(columns={"gdp_usd": country})
        frames.append(tmp.set_index("year"))
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1).reset_index()
    wide = wide.rename(columns={"year": "Year"})
    return wide


# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Controls")
    st.divider()

    selected_countries = st.multiselect(
        "Countries",
        options=sorted(COUNTRIES.keys()),
        default=["India", "United States", "China"],
    )

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start", min_value=1960, max_value=2023, value=2000)
    with col2:
        end_year = st.number_input("End", min_value=1960, max_value=2023, value=2023)

    if start_year > end_year:
        st.error("Start year must be ≤ end year.")
        st.stop()

    chart_type = st.selectbox("Chart type", ["Line", "Bar", "Area"])
    log_scale  = st.toggle("Log scale (Y-axis)", value=False)

    st.divider()
    fetch_btn = st.button("🔄 Fetch Data", use_container_width=True, type="primary")

# ── main ───────────────────────────────────────────────────────────────────────
st.title("📊 GDP Data Extractor")
st.caption("Powered by the World Bank Open Data API · NY.GDP.MKTP.CD · current USD")

if not selected_countries:
    st.info("Select at least one country in the sidebar, then click **Fetch Data**.")
    st.stop()

if fetch_btn or "gdp_data" not in st.session_state:
    with st.spinner("Fetching from World Bank..."):
        results = {}
        for name in selected_countries:
            code = COUNTRIES[name]
            results[name] = fetch_gdp(code, start_year, end_year)
        st.session_state["gdp_data"] = results
        st.session_state["wide_df"] = build_wide_df(results)

data    = st.session_state.get("gdp_data", {})
wide_df = st.session_state.get("wide_df", pd.DataFrame())

if wide_df.empty:
    st.warning("No data returned. Try different countries or a wider year range.")
    st.stop()

# ── metric cards ──────────────────────────────────────────────────────────────
st.subheader("Latest available GDP")
cols = st.columns(len(selected_countries))
for i, name in enumerate(selected_countries):
    df = data.get(name, pd.DataFrame())
    if not df.empty:
        latest_row = df.dropna(subset=["gdp_usd"]).iloc[-1]
        cols[i].metric(
            label=name,
            value=fmt_gdp(latest_row["gdp_usd"]),
            delta=f"{latest_row['year']}"
        )
    else:
        cols[i].metric(label=name, value="N/A")

st.divider()

# ── chart ──────────────────────────────────────────────────────────────────────
st.subheader("GDP over time")

long_df = wide_df.melt(id_vars="Year", var_name="Country", value_name="GDP (USD)")

if chart_type == "Line":
    fig = px.line(long_df, x="Year", y="GDP (USD)", color="Country",
                  markers=True, template="plotly_white")
elif chart_type == "Bar":
    fig = px.bar(long_df, x="Year", y="GDP (USD)", color="Country",
                 barmode="group", template="plotly_white")
else:
    fig = px.area(long_df, x="Year", y="GDP (USD)", color="Country",
                  template="plotly_white")

fig.update_layout(
    yaxis_type="log" if log_scale else "linear",
    yaxis_tickformat="$,.2s",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=0, t=40, b=0),
)
fig.update_traces(hovertemplate="%{y:$,.2s}")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── raw table + download ───────────────────────────────────────────────────────
st.subheader("Raw data")

fmt_df = wide_df.copy()
for col in fmt_df.columns:
    if col != "Year":
        fmt_df[col] = fmt_df[col].apply(lambda x: fmt_gdp(x) if pd.notna(x) else "—")

st.dataframe(fmt_df, use_container_width=True, hide_index=True)

csv_buf = StringIO()
wide_df.to_csv(csv_buf, index=False)
st.download_button(
    label="⬇️ Download CSV",
    data=csv_buf.getvalue(),
    file_name="gdp_data.csv",
    mime="text/csv",
    use_container_width=True,
)
