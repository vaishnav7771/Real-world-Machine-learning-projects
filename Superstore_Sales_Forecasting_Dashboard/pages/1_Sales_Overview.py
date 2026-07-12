import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from style import inject_css, section_header, apply_plotly_theme, ACCENT, ACCENT2, ACCENT3
from utils import load_data, yearly_sales, monthly_sales, sales_by_region_category

st.set_page_config(page_title="Sales Overview | Nexus", page_icon="📊", layout="wide")
inject_css()

section_header("📊 Sales Overview Dashboard", subtitle="Yearly and monthly performance, sliced by region and category.")

df = load_data()

# ---------------- Total sales by year ----------------
left, right = st.columns([1, 1])

with left:
    st.markdown("#### Total Sales by Year")
    ys = yearly_sales(df)
    fig = px.bar(
        ys, x="Year", y="Sales", text_auto=".2s",
        color="Sales", color_continuous_scale=[ACCENT2, ACCENT],
    )
    fig.update_traces(marker_line_width=0, textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=380)
    apply_plotly_theme(fig)
    st.plotly_chart(fig, width="stretch")

with right:
    st.markdown("#### Monthly Sales Trend")
    ms = monthly_sales(df)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ms["YearMonth"], y=ms["Sales"], mode="lines",
        line=dict(color=ACCENT, width=3), fill="tozeroy",
        fillcolor="rgba(0,229,255,0.12)", name="Monthly Sales",
    ))
    fig2.update_layout(height=380)
    apply_plotly_theme(fig2)
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")

# ---------------- Region / Category interactive filters ----------------
st.markdown("#### Sales by Region & Category")

f1, f2, f3 = st.columns(3)
with f1:
    regions = st.multiselect("Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
with f2:
    categories = st.multiselect("Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique()))
with f3:
    years = st.multiselect("Year", sorted(df["Year"].unique()), default=sorted(df["Year"].unique()))

filtered = df[
    df["Region"].isin(regions) & df["Category"].isin(categories) & df["Year"].isin(years)
]

if filtered.empty:
    st.warning("No data for the selected filters. Adjust your selections above.")
else:
    rc = filtered.groupby(["Region", "Category"], as_index=False)["Sales"].sum()

    c1, c2 = st.columns([1.3, 1])
    with c1:
        fig3 = px.bar(
            rc, x="Region", y="Sales", color="Category", barmode="group",
            color_discrete_sequence=[ACCENT, ACCENT2, ACCENT3],
        )
        fig3.update_layout(height=420, legend=dict(orientation="h", y=1.12))
        apply_plotly_theme(fig3)
        st.plotly_chart(fig3, width="stretch")

    with c2:
        cat_totals = filtered.groupby("Category", as_index=False)["Sales"].sum()
        fig4 = px.pie(
            cat_totals, names="Category", values="Sales", hole=0.55,
            color_discrete_sequence=[ACCENT, ACCENT2, ACCENT3],
        )
        fig4.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#0B0F1A", width=2)))
        fig4.update_layout(height=420, showlegend=False)
        apply_plotly_theme(fig4)
        st.plotly_chart(fig4, width="stretch")

    with st.expander("View filtered data table"):
        st.dataframe(
            filtered.groupby(["Region", "Category"], as_index=False)["Sales"].sum().sort_values("Sales", ascending=False),
            width="stretch", hide_index=True,
        )
