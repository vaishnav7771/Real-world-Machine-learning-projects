import streamlit as st
import plotly.graph_objects as go
from style import inject_css, section_header, apply_plotly_theme, ACCENT
from utils import load_data, detect_anomalies

st.set_page_config(page_title="Anomaly Report | Nexus", page_icon="🚨", layout="wide")
inject_css()

section_header(
    "🚨 Anomaly Report",
    subtitle="Weekly sales anomalies detected via Isolation Forest and Rolling Z-Score.",
)

df = load_data()
weekly, avg_sales = detect_anomalies(df)

method = st.radio(
    "Detection method", ["Isolation Forest", "Rolling Z-Score (4-week window, |z| > 2)"],
    horizontal=True,
)
flag_col = "IsoAnomaly" if method == "Isolation Forest" else "ZAnomaly"
anomalies = weekly[weekly[flag_col]]

c1, c2, c3 = st.columns(3)
c1.metric("Weeks Analyzed", f"{len(weekly)}")
c2.metric("Anomalies Detected", f"{len(anomalies)}")
c3.metric("Average Weekly Sales", f"${avg_sales:,.0f}")

# ---------------- Anomaly chart ----------------
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["Order Date"], y=weekly["Sales"], mode="lines",
    name="Weekly Sales", line=dict(color=ACCENT, width=2),
))
if not anomalies.empty:
    fig.add_trace(go.Scatter(
        x=anomalies["Order Date"], y=anomalies["Sales"], mode="markers",
        name="Anomaly", marker=dict(color="#FF3B6B", size=12, symbol="x",
                                     line=dict(color="white", width=1)),
    ))
fig.update_layout(height=460, legend=dict(orientation="h", y=1.12), hovermode="x unified")
apply_plotly_theme(fig)
st.plotly_chart(fig, width="stretch")

# ---------------- Anomaly table ----------------
st.markdown("#### Detected Anomaly Dates")
if anomalies.empty:
    st.info(f"No anomalies detected using {method} at the current threshold.")
else:
    table_cols = ["Order Date", "Sales", "Anomaly Type"]
    if flag_col == "ZAnomaly":
        table_cols += ["Z-Score"]
    show = anomalies[table_cols].copy().sort_values("Order Date")
    show["Sales"] = show["Sales"].round(2)
    if "Z-Score" in show.columns:
        show["Z-Score"] = show["Z-Score"].round(2)
    st.dataframe(show, width="stretch", hide_index=True)

with st.expander("Compare both methods"):
    iso_dates = set(weekly[weekly["IsoAnomaly"]]["Order Date"])
    z_dates = set(weekly[weekly["ZAnomaly"]]["Order Date"])
    common = iso_dates & z_dates
    st.write(f"**Common to both methods:** {len(common)}")
    st.write(f"**Isolation Forest only:** {len(iso_dates - z_dates)}")
    st.write(f"**Rolling Z-Score only:** {len(z_dates - iso_dates)}")
    st.caption(
        "Isolation Forest flags points that sit far from the overall sales distribution, "
        "while the Rolling Z-Score flags sudden local deviations from a recent 4-week baseline — "
        "so the two methods can reasonably disagree on borderline weeks."
    )
