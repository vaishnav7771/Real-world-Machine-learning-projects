import streamlit as st
import plotly.graph_objects as go
from style import inject_css, section_header, apply_plotly_theme, ACCENT, ACCENT2
from utils import load_data, fit_best_forecast_model, forecast_future

st.set_page_config(page_title="Forecast Explorer | Nexus", page_icon="🔮", layout="wide")
inject_css()

section_header(
    "🔮 Forecast Explorer",
    subtitle="SARIMA vs XGBoost (lag-feature) forecasting — the better model is auto-selected per series by holdout MAE.",
)

df = load_data()

c1, c2 = st.columns([1, 1])
with c1:
    dimension = st.selectbox("Select dimension", ["Category", "Region"])
with c2:
    value = st.selectbox(f"Select {dimension}", sorted(df[dimension].unique()))

horizon_label = st.select_slider(
    "Forecast horizon",
    options=["1 month ahead", "2 months ahead", "3 months ahead"],
    value="3 months ahead",
)
horizon = {"1 month ahead": 1, "2 months ahead": 2, "3 months ahead": 3}[horizon_label]

with st.spinner(f"Fitting SARIMA & XGBoost models on {value} ({dimension})..."):
    result = fit_best_forecast_model(df, dimension, value)
    forecast = forecast_future(result["series"], result["best_model"], horizon)

series = result["series"]

st.markdown(
    f"""
    <div class="glass-card" style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
        <span class="pill">BEST MODEL: {result['best_model']}</span>
        <span style="color:#8FA3C0;">selected automatically — lower holdout MAE between SARIMA and XGBoost</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- Forecast chart ----------------
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=series.index, y=series.values, mode="lines+markers",
    name="Historical Sales", line=dict(color=ACCENT2, width=2.5),
    marker=dict(size=5),
))
fig.add_trace(go.Scatter(
    x=forecast.index, y=forecast.values, mode="lines+markers",
    name=f"Forecast ({result['best_model']})", line=dict(color=ACCENT, width=3, dash="dash"),
    marker=dict(size=9, symbol="diamond"),
))
# connect last historical point to first forecast point
fig.add_trace(go.Scatter(
    x=[series.index[-1], forecast.index[0]], y=[series.values[-1], forecast.values[0]],
    mode="lines", line=dict(color=ACCENT, width=3, dash="dash"), showlegend=False,
))
fig.update_layout(height=460, legend=dict(orientation="h", y=1.12), hovermode="x unified")
apply_plotly_theme(fig)
st.plotly_chart(fig, width="stretch")

# ---------------- Forecast table ----------------
st.markdown("#### Forecasted Values")
fc_table = forecast.reset_index()
fc_table.columns = ["Month", "Forecasted Sales"]
fc_table["Forecasted Sales"] = fc_table["Forecasted Sales"].round(2)
st.dataframe(fc_table, width="stretch", hide_index=True)

# ---------------- Metrics ----------------
st.markdown("#### Model Performance (Holdout Evaluation)")
m1, m2, m3 = st.columns(3)
m1.metric("MAE", f"${result['mae']:,.2f}")
m2.metric("RMSE", f"${result['rmse']:,.2f}")
m3.metric("Best Model", result["best_model"])

with st.expander("Compare all candidate models"):
    for name, metrics in result["all_results"].items():
        tag = "🏆 " if name == result["best_model"] else ""
        st.write(f"**{tag}{name}** — MAE: `${metrics['mae']:,.2f}` · RMSE: `${metrics['rmse']:,.2f}`")
