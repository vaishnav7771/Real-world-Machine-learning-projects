"""Shared futuristic styling: CSS injection + Plotly template."""
import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

ACCENT = "#00E5FF"
ACCENT2 = "#7C4DFF"
ACCENT3 = "#00FFA3"
BG = "#0B0F1A"
PANEL = "rgba(18, 24, 38, 0.65)"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background: radial-gradient(circle at 15% 0%, rgba(0,229,255,0.10), transparent 40%),
                radial-gradient(circle at 85% 15%, rgba(124,77,255,0.12), transparent 45%),
                radial-gradient(circle at 50% 100%, rgba(0,255,163,0.06), transparent 50%),
                {BG};
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, rgba(11,15,26,0.98) 0%, rgba(18,24,38,0.98) 100%);
    border-right: 1px solid rgba(0,229,255,0.15);
}}

/* Headings */
h1 {{
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, {ACCENT}, {ACCENT2});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1px;
    padding-bottom: 4px;
}}
h2, h3 {{
    font-family: 'Orbitron', sans-serif !important;
    color: #E6F1FF !important;
    letter-spacing: 0.5px;
}}

/* Glass panel / card container */
.glass-card {{
    background: {PANEL};
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 16px;
    padding: 18px 22px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 24px rgba(0,229,255,0.06), inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 14px;
}}

/* Metric cards */
div[data-testid="stMetric"] {{
    background: {PANEL};
    border: 1px solid rgba(0,229,255,0.20);
    border-radius: 14px;
    padding: 14px 18px 10px 18px;
    box-shadow: 0 0 20px rgba(0,229,255,0.07);
}}
div[data-testid="stMetricLabel"] {{
    color: #8FA3C0 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
div[data-testid="stMetricValue"] {{
    color: {ACCENT} !important;
    font-family: 'Orbitron', sans-serif;
}}

/* Divider glow line */
.glow-divider {{
    height: 2px;
    border: none;
    margin: 6px 0 20px 0;
    background: linear-gradient(90deg, transparent, {ACCENT}, {ACCENT2}, transparent);
    box-shadow: 0 0 10px {ACCENT};
}}

/* Badge / pill */
.pill {{
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    background: rgba(0,229,255,0.12);
    border: 1px solid rgba(0,229,255,0.35);
    color: {ACCENT};
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
.pill.purple {{
    background: rgba(124,77,255,0.14);
    border: 1px solid rgba(124,77,255,0.4);
    color: #B69CFF;
}}
.pill.green {{
    background: rgba(0,255,163,0.10);
    border: 1px solid rgba(0,255,163,0.35);
    color: {ACCENT3};
}}

/* Buttons */
.stButton>button, .stDownloadButton>button {{
    background: linear-gradient(90deg, {ACCENT}, {ACCENT2});
    color: #05121A;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    box-shadow: 0 0 16px rgba(0,229,255,0.35);
}}

/* Dataframe */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(0,229,255,0.15);
}}

/* Selectbox / slider labels */
label {{
    color: #C7D6EA !important;
    font-weight: 500 !important;
}}

/* Hide default streamlit footer/menu clutter */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def section_header(title, subtitle=None, pill=None, pill_class=""):
    pill_html = f'<span class="pill {pill_class}">{pill}</span>' if pill else ""
    sub_html = f'<p style="color:#8FA3C0;margin-top:2px;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
            <h1 style="margin-bottom:0;">{title}</h1>
            {pill_html}
        </div>
        {sub_html}
        <hr class="glow-divider"/>
        """,
        unsafe_allow_html=True,
    )


def get_plotly_template():
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#E6F1FF", size=13),
        colorway=[ACCENT, ACCENT2, ACCENT3, "#FF6EC7", "#FFD166", "#5DA9FF"],
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.08)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return template


def apply_plotly_theme(fig):
    fig.update_layout(template=get_plotly_template())
    return fig
