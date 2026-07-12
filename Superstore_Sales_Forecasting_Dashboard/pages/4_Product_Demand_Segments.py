import streamlit as st
import plotly.express as px
from style import inject_css, section_header, apply_plotly_theme, ACCENT, ACCENT2, ACCENT3
from utils import load_data, cluster_subcategories

st.set_page_config(page_title="Demand Segments | Nexus", page_icon="🧩", layout="wide")
inject_css()

section_header(
    "🧩 Product Demand Segments",
    subtitle="KMeans clustering of sub-categories by Total Sales, Growth Rate, Volatility & Average Order Value.",
)

df = load_data()
feat, summary, explained_var = cluster_subcategories(df, n_clusters=3)

segment_colors = {
    "Growing Demand": ACCENT3,
    "High Volume, Stable Demand": ACCENT,
    "Moderate, Stable Demand": ACCENT2,
    "Declining Demand": "#FF6EC7",
}

c1, c2 = st.columns([1.3, 1])

with c1:
    st.markdown("#### Cluster Chart (PCA Projection)")
    fig = px.scatter(
        feat, x="PC1", y="PC2", color="Demand Segment", text="Sub-Category",
        color_discrete_map=segment_colors, size="Total Sales Volume", size_max=40,
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(color="#0B0F1A", width=1)))
    fig.update_layout(
        height=520, legend=dict(orientation="h", y=1.15),
        xaxis_title=f"PC1 ({explained_var[0]:.0%} variance)",
        yaxis_title=f"PC2 ({explained_var[1]:.0%} variance)",
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, width="stretch")

with c2:
    st.markdown("#### Cluster Profile (Averages)")
    summary_display = summary.reset_index()
    summary_display["Demand Segment"] = summary_display["Cluster"].map(
        dict(zip(feat["Cluster"], feat["Demand Segment"]))
    )
    st.dataframe(
        summary_display[["Demand Segment", "Total Sales Volume", "Sales Growth Rate (%)", "Sales Volatility"]],
        width="stretch", hide_index=True,
    )

    st.markdown("#### Segment Sizes")
    counts = feat["Demand Segment"].value_counts().reset_index()
    counts.columns = ["Demand Segment", "Sub-Categories"]
    fig2 = px.bar(
        counts, x="Sub-Categories", y="Demand Segment", orientation="h",
        color="Demand Segment", color_discrete_map=segment_colors,
    )
    fig2.update_layout(height=220, showlegend=False)
    apply_plotly_theme(fig2)
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")
st.markdown("#### Sub-Category → Cluster Mapping")

for segment in feat["Demand Segment"].unique():
    sub = feat[feat["Demand Segment"] == segment].sort_values("Total Sales Volume", ascending=False)
    color = segment_colors.get(segment, ACCENT)
    st.markdown(
        f'<span class="pill" style="background:rgba(0,0,0,0); border-color:{color}; color:{color};">{segment}</span>',
        unsafe_allow_html=True,
    )
    show = sub[["Sub-Category", "Total Sales Volume", "Sales Growth Rate (%)", "Sales Volatility", "Average Order Value"]].copy()
    for col in ["Total Sales Volume", "Sales Growth Rate (%)", "Sales Volatility", "Average Order Value"]:
        show[col] = show[col].round(2)
    st.dataframe(show, width="stretch", hide_index=True)
    st.markdown("<br>", unsafe_allow_html=True)
