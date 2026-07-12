import streamlit as st
from style import inject_css, section_header
from utils import load_data, yearly_sales

st.set_page_config(
    page_title="Nexus Sales Intelligence",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 10px 0 20px 0;">
            <h2 style="margin-bottom:0; font-size:1.4rem;">⟡ NEXUS</h2>
            <p style="color:#8FA3C0; font-size:0.75rem; letter-spacing:1px;">SALES INTELLIGENCE SYSTEM</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Navigate using the pages above ⬆")

section_header(
    "NEXUS SALES INTELLIGENCE",
    subtitle="End-to-end sales forecasting & demand intelligence — powered by SARIMA, XGBoost, Isolation Forest & KMeans.",
    pill="LIVE",
    pill_class="green",
)

df = load_data()
ys = yearly_sales(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${df['Sales'].sum():,.0f}")
c2.metric("Orders Analyzed", f"{df.shape[0]:,}")
c3.metric("Years Covered", f"{int(ys['Year'].min())}–{int(ys['Year'].max())}")
c4.metric("Sub-Categories", f"{df['Sub-Category'].nunique()}")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="glass-card">
    <h3>🧭 What's inside</h3>
    <p style="color:#C7D6EA; line-height:1.9;">
    <b style="color:#00E5FF;">📊 Sales Overview</b> — yearly & monthly trends, region × category breakdown with interactive filters.<br>
    <b style="color:#00E5FF;">🔮 Forecast Explorer</b> — SARIMA vs XGBoost forecasts per Category/Region, with the better model auto-selected by MAE.<br>
    <b style="color:#00E5FF;">🚨 Anomaly Report</b> — Isolation Forest & Rolling Z-Score anomaly detection on weekly sales.<br>
    <b style="color:#00E5FF;">🧩 Demand Segments</b> — KMeans clustering of sub-categories into demand personas for stocking strategy.
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="glass-card" style="margin-top:10px;">
    <span class="pill purple">DATA SOURCE</span>
    <p style="color:#8FA3C0; margin-top:10px;">
    Superstore transactional sales data (2015–2018) · Categories: Furniture, Office Supplies, Technology ·
    Regions: East, West, Central, South
    </p>
    </div>
    """,
    unsafe_allow_html=True,
)
