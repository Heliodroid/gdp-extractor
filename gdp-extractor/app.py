import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(
    page_title="GDP & Inflation Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

WB_BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "GDP (current USD)":        "NY.GDP.MKTP.CD",
    "GDP per capita (USD)":     "NY.GDP.PCAP.CD",
    "Inflation, CPI (% YoY)":   "FP.CPI.TOTL.ZG",
    "GDP growth (% YoY)":       "NY.GDP.MKTP.KD.ZG",
}

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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_indicator(country_code: str, indicator: str, start: int, end: int) -> pd.DataFrame:
    url = (f"{WB_BASE}/country/{country_code}/indicator/{indicator}"
           f"?date={start}:{end}&format=json&per_page=100")
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            break
        except requests.exceptions.Timeout:
            if attempt == 2:
                st.warning(f"Timeout fetching {country_code} after 3 attempts.")
                return pd.DataFrame()
            import time; time.sleep(2)
        except Exception as e:
            st.warning(f"Could not fetch {country_code}: {e}")
            return pd.DataFrame()
    payload = r.json()
    if len(payload) < 2 or not payload[1]:
        return pd.DataFrame()
    rows = [{"year": int(d["date"]), "value": d["value"]}
            for d in payload[1] if d["value"] is not None]
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

def fmt_val(val: float, indicator: str) -> str:
    if "%" in indicator:
        return f"{val:.2f}%"
    if val >= 1e12: return f"${val/1e12:.2f}T"
    if val >= 1e9:  return f"${val/1e9:.1f}B"
    if val >= 1e6:  return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"

def build_wide(data: dict, countries: list) -> pd.DataFrame:
    frames = []
    for c in countries:
        df = data.get(c, pd.DataFrame())
        if df.empty: continue
        frames.append(df.rename(columns={"value": c}).set_index("year"))
    if not frames: return pd.DataFrame()
    return pd.concat(frames, axis=1).reset_index().rename(columns={"year": "Year"})

# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Controls")
    st.divider()

    selected_countries = st.multiselect(
        "Countries", options=sorted(COUNTRIES.keys()),
        default=["India", "United States", "China"],
    )
    col1, col2 = st.columns(2)
    with col1: start_year = st.number_input("Start", min_value=1960, max_value=2023, value=2000)
    with col2: end_year   = st.number_input("End",   min_value=1960, max_value=2023, value=2023)
    if start_year > end_year:
        st.error("Start ≤ End required."); st.stop()

    chart_type = st.selectbox("Chart type", ["Line", "Bar", "Area"])
    log_scale  = st.toggle("Log scale", value=False)
    st.divider()
    fetch_btn  = st.button("🔄 Fetch Data", use_container_width=True, type="primary")

# ── main ───────────────────────────────────────────────────────────────────────
st.title("📊 GDP & Inflation Explorer")
st.caption("World Bank Open Data API · real-time fetch · no API key needed")

if not selected_countries:
    st.info("Select countries in the sidebar, then click **Fetch Data**."); st.stop()

if fetch_btn or "wb_data" not in st.session_state:
    with st.spinner("Fetching from World Bank..."):
        wb = {}
        for ind_label, ind_code in INDICATORS.items():
            wb[ind_label] = {}
            for name in selected_countries:
                wb[ind_label][name] = fetch_indicator(COUNTRIES[name], ind_code, start_year, end_year)
        st.session_state["wb_data"] = wb

wb = st.session_state.get("wb_data", {})

# ── tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs(list(INDICATORS.keys()) + ["📥 Export"])

for tab, (ind_label, _) in zip(tabs[:-1], INDICATORS.items()):
    with tab:
        data    = wb.get(ind_label, {})
        wide_df = build_wide(data, selected_countries)
        is_pct  = "%" in ind_label

        if wide_df.empty:
            st.warning("No data for this indicator / range."); continue

        # metric cards
        mcols = st.columns(len(selected_countries))
        for i, name in enumerate(selected_countries):
            df = data.get(name, pd.DataFrame())
            if not df.empty:
                latest = df.dropna(subset=["value"]).iloc[-1]
                mcols[i].metric(label=name,
                                value=fmt_val(latest["value"], ind_label),
                                delta=str(int(latest["year"])))
            else:
                mcols[i].metric(label=name, value="N/A")

        st.divider()

        # chart
        long_df = wide_df.melt(id_vars="Year", var_name="Country", value_name=ind_label)
        if chart_type == "Line":
            fig = px.line(long_df, x="Year", y=ind_label, color="Country",
                          markers=True, template="plotly_white")
        elif chart_type == "Bar":
            fig = px.bar(long_df, x="Year", y=ind_label, color="Country",
                         barmode="group", template="plotly_white")
        else:
            fig = px.area(long_df, x="Year", y=ind_label, color="Country",
                          template="plotly_white")

        y_fmt = ".2f%" if is_pct else "$,.2s"
        fig.update_layout(
            yaxis_type="log" if (log_scale and not is_pct) else "linear",
            yaxis_tickformat=y_fmt,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # dual-axis GDP + Inflation overlay (only on GDP tab, single country)
        if ind_label == "GDP (current USD)" and len(selected_countries) == 1:
            name = selected_countries[0]
            inf_df = wb.get("Inflation, CPI (% YoY)", {}).get(name, pd.DataFrame())
            gdp_df = data.get(name, pd.DataFrame())
            if not inf_df.empty and not gdp_df.empty:
                st.markdown(f"**GDP vs Inflation overlay — {name}**")
                merged = gdp_df.merge(inf_df, on="year", suffixes=("_gdp","_inf"))
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=merged["year"], y=merged["value_gdp"],
                                      name="GDP (USD)", yaxis="y1",
                                      marker_color="steelblue", opacity=0.7))
                fig2.add_trace(go.Scatter(x=merged["year"], y=merged["value_inf"],
                                          name="Inflation (%)", yaxis="y2",
                                          line=dict(color="crimson", width=2)))
                fig2.update_layout(
                    template="plotly_white",
                    yaxis=dict(title="GDP (USD)", tickformat="$,.2s"),
                    yaxis2=dict(title="Inflation (%)", overlaying="y", side="right",
                                tickformat=".1f"),
                    hovermode="x unified",
                    legend=dict(orientation="h", y=1.05),
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # raw table
        with st.expander("Raw data"):
            st.dataframe(wide_df, use_container_width=True, hide_index=True)

# ── export tab ─────────────────────────────────────────────────────────────────
with tabs[-1]:
    st.subheader("Download data")
    for ind_label in INDICATORS:
        data    = wb.get(ind_label, {})
        wide_df = build_wide(data, selected_countries)
        if wide_df.empty: continue
        buf = StringIO(); wide_df.to_csv(buf, index=False)
        safe_name = ind_label.replace(" ", "_").replace("(","").replace(")","").replace("%","pct").replace("/","_")
        st.download_button(
            label=f"⬇️ {ind_label}",
            data=buf.getvalue(),
            file_name=f"{safe_name}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"dl_{safe_name}",
        )
