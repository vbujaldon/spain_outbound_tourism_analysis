"""
Tourism Intelligence Framework — Enhanced Dashboard
Strategic Analytics for Outbound Flight Capacity Allocation
IT Academy / Barcelona Activa — Data Analytics Capstone
"""

# ── IMPORTS ──────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Outbound Tourism Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── COLOUR PALETTE ───────────────────────────────────────────────────────────
# Dark-ops palette: deep navy bg, cyan accent, warm amber secondary

BG_DARK   = "#050b16"
BG_CARD   = "#0f172a"
BG_SIDE   = "#1e293b"
CYAN      = "#06b6d4"
CYAN_LT   = "#38bdf8"
AMBER     = "#f59e0b"
RED       = "#ef4444"
GREEN     = "#22c55e"
SLATE     = "#94a3b8"
WHITE     = "#f8fafc"
NAVY_MID  = "#1e3a8a"

CONTINENT_COLORS = {
    "Africa": "#f97316",
    "Americas": "#06b6d4",
    "Asia": "#a855f7",
    "Oceania": "#22c55e",
    "Europe": "#64748b",
}

# ── STYLE ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_DARK}; }}
    h1, h2, h3 {{ color: {WHITE} !important; font-family: 'Inter', sans-serif; }}
    p, span, label {{ color: {SLATE}; }}
    .stDataFrame {{ background-color: {BG_SIDE}; border-radius: 8px; }}
    div[data-testid="stMetric"] {{
        background-color: {BG_CARD}; padding: 15px; border-radius: 10px;
        border-left: 5px solid {CYAN};
    }}
    div[data-testid="stMetric"] label {{ color: {SLATE} !important; }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: {WHITE} !important; }}
    [data-testid="stSidebar"] {{ background-color: {BG_SIDE}; }}
    .kpi-negative {{ color: {RED}; font-weight: 700; }}
    .kpi-positive {{ color: {GREEN}; font-weight: 700; }}
</style>
""", unsafe_allow_html=True)


# ── LOAD DATA ────────────────────────────────────────────────────────────────

@st.cache_data
def load_main():
    """Load the main geo-level tourism dataset."""
    df = pd.read_parquet(BASE_DIR / "data" / "07_streamlit_dataset.parquet")
    df["period"] = pd.to_datetime(df["period"])
    df["month_name"] = df["period"].dt.strftime("%b")
    return df


@st.cache_data
def load_destination_summary():
    """Load destination intelligence profiles from NB-08."""
    try:
        df = pd.read_parquet(BASE_DIR / "data" / "08_destination_summary.parquet")
        return df
    except FileNotFoundError:
        return None


@st.cache_data
def load_destination_summary_strategic():
    """Load strategic-subset destination profiles from NB-08."""
    try:
        df = pd.read_parquet(BASE_DIR / "data" / "08_destination_summary_strategic_subset.parquet")
        return df
    except FileNotFoundError:
        return None


df = load_main()
df_summary = load_destination_summary()
df_summary_strat = load_destination_summary_strategic()


# ── PLOTLY LAYOUT DEFAULTS ───────────────────────────────────────────────────

def base_layout(height=400, **kwargs):
    """Return a dict of common layout parameters for all charts."""
    axis_defaults = dict(gridcolor="rgba(148,163,184,0.1)", zerolinecolor="rgba(148,163,184,0.1)")
    # Merge user-supplied xaxis/yaxis with defaults (user keys win)
    xaxis = {**axis_defaults, **kwargs.pop("xaxis", {})}
    yaxis = {**axis_defaults, **kwargs.pop("yaxis", {})}
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(color=SLATE, family="Inter, sans-serif"),
        margin=dict(t=40, b=30, l=10, r=10),
        xaxis=xaxis,
        yaxis=yaxis,
    )
    layout.update(kwargs)
    return layout


# ── HEADER ───────────────────────────────────────────────────────────────────

st.markdown(
    "<h1>🌍 Tourism Intelligence Framework</h1>"
    f"<p style='color:{SLATE}; margin-top:-15px; font-size:1.05rem;'>"
    "Strategic Analytics for Outbound Flight Capacity Allocation"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# ── SIDEBAR — FILTERS ───────────────────────────────────────────────────────

st.sidebar.title("🎛️ Filters")

# — Navigation
page = st.sidebar.radio(
    "Dashboard Section",
    ["📊 Market Overview", "🏆 Destination Intelligence", "🗺️ Territorial Analysis", "🎯 Route Deep Dive"],
)

st.sidebar.markdown("---")

# — Year multi-select
years_available = sorted(df["year"].dropna().unique().astype(int))
selected_years = st.sidebar.multiselect(
    "Years",
    options=years_available,
    default=years_available,
    help="Select one or more years to include in the analysis.",
)
if not selected_years:
    selected_years = years_available
    st.sidebar.warning("No year selected — showing all.")

# — Origin filter (geographic hierarchy)
st.sidebar.markdown("---")
st.sidebar.markdown("**Origin Filter**")

# Detect available geographic columns
has_ccaa = "autonomous_community" in df.columns
has_province = "depart_province" in df.columns
has_city = "depart_city" in df.columns

origin_levels = ["🇪🇸 All Spain"]
if has_ccaa:
    origin_levels.append("Comunitat Autònoma")
if has_province:
    origin_levels.append("Província")
if has_city:
    origin_levels.append("Població")

origin_level = st.sidebar.selectbox("Geographic level", origin_levels)

selected_ccaa = None
selected_province = None
selected_city = None

if origin_level == "Comunitat Autònoma" and has_ccaa:
    ccaa_opts = sorted(df["autonomous_community"].dropna().unique())
    selected_ccaa = st.sidebar.selectbox("Select CCAA", ccaa_opts)
elif origin_level == "Província" and has_province:
    if has_ccaa:
        ccaa_opts = sorted(df["autonomous_community"].dropna().unique())
        selected_ccaa = st.sidebar.selectbox("CCAA (optional)", ["All"] + ccaa_opts)
        if selected_ccaa == "All":
            selected_ccaa = None
    prov_pool = df.copy()
    if selected_ccaa:
        prov_pool = prov_pool[prov_pool["autonomous_community"] == selected_ccaa]
    prov_opts = sorted(prov_pool["depart_province"].dropna().unique())
    selected_province = st.sidebar.selectbox("Select Province", prov_opts)
elif origin_level == "Població" and has_city:
    if has_province:
        prov_opts = sorted(df["depart_province"].dropna().unique())
        selected_province = st.sidebar.selectbox("Province", prov_opts)
    city_pool = df.copy()
    if selected_province:
        city_pool = city_pool[city_pool["depart_province"] == selected_province]
    city_opts = sorted(city_pool["depart_city"].dropna().unique())
    selected_city = st.sidebar.selectbox("Select City", city_opts)

# — Continent filter
st.sidebar.markdown("---")
continent_opts = sorted(df["continent"].dropna().unique())
selected_continents = st.sidebar.multiselect(
    "Continents",
    options=continent_opts,
    default=continent_opts,
)
if not selected_continents:
    selected_continents = continent_opts


# ── APPLY FILTERS ────────────────────────────────────────────────────────────

mask = (df["year"].isin(selected_years)) & (df["continent"].isin(selected_continents))
if selected_ccaa and has_ccaa:
    mask = mask & (df["autonomous_community"] == selected_ccaa)
if selected_province and has_province:
    mask = mask & (df["depart_province"] == selected_province)
if selected_city and has_city:
    mask = mask & (df["depart_city"] == selected_city)

df_f = df[mask].copy()

# Show active filter context
origin_label = "Spain"
if selected_city:
    origin_label = selected_city
elif selected_province:
    origin_label = selected_province
elif selected_ccaa:
    origin_label = selected_ccaa

if origin_label != "Spain":
    st.caption(f"📍 Origin filter active: **{origin_label}** · {len(selected_years)} year(s) · {len(selected_continents)} continent(s)")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — MARKET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Market Overview":

    # — KPI row
    total_pax = df_f["total_tourists"].sum()
    n_routes = df_f["destination_clean"].nunique()
    n_months = df_f["period"].nunique()
    avg_monthly = total_pax / max(n_months, 1)

    # YoY growth for the latest complete year
    latest_yr = max(selected_years)
    prev_yr = latest_yr - 1
    pax_latest = df_f[df_f["year"] == latest_yr]["total_tourists"].sum()
    pax_prev = df_f[df_f["year"] == prev_yr]["total_tourists"].sum()
    yoy_pct = ((pax_latest / pax_prev) - 1) * 100 if pax_prev > 0 else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Travellers", f"{total_pax:,.0f}")
    c2.metric("Active Routes", f"{n_routes}")
    c3.metric("Avg. Monthly Flow", f"{avg_monthly:,.0f}")
    if yoy_pct is not None:
        c4.metric(f"YoY Growth ({latest_yr})", f"{yoy_pct:+.1f}%")
    else:
        c4.metric("YoY Growth", "N/A")

    # — Monthly evolution line
    st.subheader("📈 Monthly Outbound Evolution")
    evol = df_f.groupby("period")["total_tourists"].sum().reset_index()
    fig = px.area(evol, x="period", y="total_tourists", color_discrete_sequence=[CYAN])
    fig.update_traces(line=dict(width=2))
    fig.update_layout(**base_layout(350, xaxis_title="", yaxis_title="Travellers"))
    st.plotly_chart(fig, use_container_width=True)

    # — Continental breakdown + Top destinations side by side
    col_a, col_b = st.columns([1, 1.6])

    with col_a:
        st.subheader("🌐 Continental Breakdown")
        cont_df = df_f.groupby("continent")["total_tourists"].sum().reset_index()
        cont_df = cont_df.sort_values("total_tourists", ascending=False)
        cont_colors = [CONTINENT_COLORS.get(c, SLATE) for c in cont_df["continent"]]
        fig_pie = px.pie(
            cont_df, values="total_tourists", names="continent", hole=0.55,
            color="continent", color_discrete_map=CONTINENT_COLORS,
        )
        fig_pie.update_traces(textinfo="label+percent", textfont_size=11)
        fig_pie.update_layout(**base_layout(320), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("🏅 Top 15 Destinations")
        dest_agg = (
            df_f.groupby(["destination_clean", "continent"])["total_tourists"]
            .sum().reset_index()
            .sort_values("total_tourists", ascending=False)
            .head(15)
        )
        fig_bar = px.bar(
            dest_agg, x="total_tourists", y="destination_clean", orientation="h",
            color="continent", color_discrete_map=CONTINENT_COLORS,
        )
        fig_bar.update_layout(
            **base_layout(420, yaxis=dict(autorange="reversed", title="")),
            xaxis_title="Total Travellers",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # — Continental evolution over time (stacked area)
    st.subheader("📊 Continental Mix Over Time")
    cont_time = (
        df_f.groupby([df_f["period"].dt.to_period("Q").astype(str), "continent"])["total_tourists"]
        .sum().reset_index()
        .rename(columns={"period": "quarter"})
    )
    fig_stack = px.area(
        cont_time, x="quarter", y="total_tourists", color="continent",
        color_discrete_map=CONTINENT_COLORS,
    )
    fig_stack.update_layout(
        **base_layout(350),
        xaxis_title="", yaxis_title="Travellers",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # — Seasonality heatmap (top 15 destinations)
    st.subheader("🗓️ Seasonality Fingerprint — Top 15 Destinations")
    st.caption("Each row normalised independently: colour = intensity relative to that destination's own peak month.")
    top_15_names = dest_agg["destination_clean"].tolist()
    h_df = (
        df_f[df_f["destination_clean"].isin(top_15_names)]
        .groupby(["destination_clean", "month"])["total_tourists"]
        .sum().reset_index()
    )
    h_pivot = h_df.pivot(index="destination_clean", columns="month", values="total_tourists").fillna(0)
    h_pct = (h_pivot.div(h_pivot.sum(axis=1), axis=0) * 100).round(1)
    h_norm = h_pivot.div(h_pivot.max(axis=1), axis=0)

    # Reorder rows by total volume
    row_order = dest_agg["destination_clean"].tolist()
    h_norm = h_norm.reindex([r for r in row_order if r in h_norm.index])
    h_pct = h_pct.reindex(h_norm.index)

    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig_heat = go.Figure(data=go.Heatmap(
        z=h_norm.values,
        x=month_labels[:h_norm.shape[1]],
        y=h_norm.index,
        text=h_pct.apply(lambda x: x.map("{:.1f}%".format)).values,
        texttemplate="%{text}",
        colorscale=[[0, NAVY_MID], [0.5, WHITE], [1, "#b91c1c"]],
        showscale=False,
    ))
    fig_heat.update_layout(**base_layout(max(380, len(h_norm) * 28)))
    st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — DESTINATION INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🏆 Destination Intelligence":

    # We use df_summary from NB-08 if available; otherwise compute from main data
    if df_summary is not None:
        st.subheader("📋 Destination Intelligence Summary")
        st.caption(
            "Source: NB-08 destination profiles. Includes ranking, market share, YoY growth, "
            "seasonality CV, search signal correlation, and peak months."
        )

        # Year selector for the ranking view
        summary_years = sorted(df_summary["year"].dropna().unique().astype(int))
        sel_rank_year = st.selectbox(
            "Show ranking for year:", summary_years, index=len(summary_years) - 1
        )

        ds = df_summary[df_summary["year"] == sel_rank_year].sort_values("ranking").copy()

        # Format for display
        display_cols = {
            "ranking": "Rank",
            "destination": "Destination",
            "continent": "Continent",
            "total_tourists": "Travellers",
            "share_%": "Share %",
            "yoy_%": "YoY %",
            "top_3_months": "Peak Months",
            "seasonality_cv": "Season. CV",
            "monthly_searches_avg": "Avg Searches",
            "trend_index_avg": "Trend Idx",
            "corr_searches": "Spearman r",
        }
        avail_cols = [c for c in display_cols if c in ds.columns]
        ds_show = ds[avail_cols].rename(columns=display_cols).head(30)
        st.dataframe(ds_show, use_container_width=True, hide_index=True, height=500)

        # — Top 10 Ranking comparison across years (bump chart)
        st.subheader("🔀 How COVID Reshaped Long-Haul Rankings")
        st.caption("Ranking evolution of top destinations across years. Lines connect the same destination.")

        # Get top 10 of latest year to track
        top_track = (
            df_summary[df_summary["year"] == max(summary_years)]
            .sort_values("ranking").head(10)["destination"].tolist()
        )
        bump_df = df_summary[df_summary["destination"].isin(top_track)].copy()
        bump_df = bump_df.sort_values(["year", "ranking"])

        fig_bump = go.Figure()
        color_cycle = [CYAN, AMBER, "#a855f7", "#f97316", GREEN, RED, "#ec4899", "#8b5cf6", SLATE, WHITE]
        for i, dest in enumerate(top_track):
            sub = bump_df[bump_df["destination"] == dest]
            fig_bump.add_trace(go.Scatter(
                x=sub["year"], y=sub["ranking"], mode="lines+markers+text",
                name=dest, text=sub["destination"],
                textposition="middle right", textfont=dict(size=9),
                line=dict(width=2, color=color_cycle[i % len(color_cycle)]),
                marker=dict(size=8),
            ))
        fig_bump.update_layout(
            **base_layout(450,
                yaxis=dict(autorange="reversed", title="Ranking Position", dtick=1),
                xaxis=dict(title="", dtick=1),
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_bump, use_container_width=True)

        # — Correlation distribution
        st.subheader("📡 Search Signal Quality")
        st.caption(
            "Distribution of Spearman correlations between monthly search volume and actual traveller flow. "
            "Median ≈ 0.19 — signals are weak but present."
        )
        if "corr_searches" in df_summary.columns:
            latest_corr = df_summary[df_summary["year"] == max(summary_years)].dropna(subset=["corr_searches"])
            fig_hist = px.histogram(
                latest_corr, x="corr_searches", nbins=20,
                color_discrete_sequence=[CYAN],
                labels={"corr_searches": "Spearman r (searches vs tourists)"},
            )
            median_r = latest_corr["corr_searches"].median()
            fig_hist.add_vline(
                x=median_r, line_dash="dash", line_color=AMBER,
                annotation_text=f"Median: {median_r:.3f}", annotation_position="top right",
            )
            fig_hist.update_layout(**base_layout(320, xaxis_title="Spearman r", yaxis_title="Destinations"))
            st.plotly_chart(fig_hist, use_container_width=True)

        # — Seasonality CV vs Volume scatter
        st.subheader("🎯 Opportunity Matrix: Volume × Seasonality")
        st.caption(
            "Destinations in the top-right quadrant (high volume, high CV) "
            "represent peak-season capacity planning priorities."
        )
        latest_ds = df_summary[df_summary["year"] == max(summary_years)].dropna(
            subset=["total_tourists", "seasonality_cv"]
        )
        if len(latest_ds) > 0:
            fig_scatter = px.scatter(
                latest_ds, x="total_tourists", y="seasonality_cv",
                text="destination", color="continent",
                color_discrete_map=CONTINENT_COLORS,
                size="total_tourists", size_max=30,
            )
            fig_scatter.update_traces(textposition="top center", textfont_size=8)
            fig_scatter.update_layout(
                **base_layout(450),
                xaxis_title="Annual Travellers",
                yaxis_title="Seasonality CV (higher = more concentrated)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        # Fallback: compute basic ranking from the main dataset
        st.subheader("🏆 Destination Ranking")
        st.caption("⚠️ File `08_destination_summary.parquet` not found. Showing basic ranking from main data.")

        for yr in sorted(selected_years, reverse=True)[:3]:
            yr_data = df_f[df_f["year"] == yr]
            ranking = (
                yr_data.groupby("destination_clean")["total_tourists"]
                .sum().reset_index()
                .sort_values("total_tourists", ascending=False)
                .head(10).reset_index(drop=True)
            )
            ranking.index += 1
            ranking.index.name = "Rank"
            ranking.columns = ["Destination", "Total Travellers"]
            st.markdown(f"**Top 10 — {yr}**")
            st.dataframe(ranking, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TERRITORIAL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🗺️ Territorial Analysis":

    st.subheader("🗺️ Origin Concentration Analysis")
    st.caption(
        "Where does outbound long-haul demand originate within Spain? "
        "Madrid + Barcelona typically account for ~66% of commercial long-haul flow."
    )

    # — Province-level aggregation
    if has_province:
        prov_agg = (
            df_f.groupby("depart_province")["total_tourists"]
            .sum().reset_index()
            .sort_values("total_tourists", ascending=False)
        )
        prov_agg["share_pct"] = (prov_agg["total_tourists"] / prov_agg["total_tourists"].sum() * 100).round(2)
        prov_agg["cum_share"] = prov_agg["share_pct"].cumsum().round(2)

        # Top 15 provinces bar
        fig_prov = px.bar(
            prov_agg.head(15), x="total_tourists", y="depart_province", orientation="h",
            color="share_pct", color_continuous_scale=["#1e3a8a", CYAN, AMBER],
            text=prov_agg.head(15)["share_pct"].apply(lambda x: f"{x:.1f}%"),
        )
        fig_prov.update_layout(
            **base_layout(420, yaxis=dict(autorange="reversed", title="")),
            xaxis_title="Total Travellers",
            coloraxis_colorbar=dict(title="Share %"),
        )
        st.plotly_chart(fig_prov, use_container_width=True)

        # Cumulative concentration curve (Lorenz-like)
        st.subheader("📐 Cumulative Concentration Curve")
        st.caption(
            "How many provinces does it take to reach 80% of total demand? "
            "A steep rise means high geographic concentration."
        )
        prov_agg_sorted = prov_agg.reset_index(drop=True)
        prov_agg_sorted["rank"] = range(1, len(prov_agg_sorted) + 1)
        fig_lorenz = go.Figure()
        fig_lorenz.add_trace(go.Scatter(
            x=prov_agg_sorted["rank"], y=prov_agg_sorted["cum_share"],
            mode="lines+markers", line=dict(color=CYAN, width=2),
            marker=dict(size=5), name="Cumulative share",
        ))
        fig_lorenz.add_hline(y=80, line_dash="dash", line_color=AMBER,
                             annotation_text="80% threshold", annotation_position="bottom right")
        n_80 = prov_agg_sorted[prov_agg_sorted["cum_share"] >= 80]["rank"].min()
        if pd.notna(n_80):
            fig_lorenz.add_vline(x=n_80, line_dash="dot", line_color=AMBER)
            st.info(f"📌 **{int(n_80)} provinces** out of {len(prov_agg_sorted)} account for 80% of total demand.")
        fig_lorenz.update_layout(
            **base_layout(320, xaxis_title="Number of Provinces (ranked)", yaxis_title="Cumulative Share %"),
        )
        st.plotly_chart(fig_lorenz, use_container_width=True)

        # Province-level table
        st.subheader("📊 Full Province Ranking")
        st.dataframe(
            prov_agg.rename(columns={
                "depart_province": "Province",
                "total_tourists": "Travellers",
                "share_pct": "Share %",
                "cum_share": "Cum. Share %",
            }),
            use_container_width=True, hide_index=True, height=400,
        )

    # — CCAA-level view
    if has_ccaa:
        st.subheader("🏛️ Outbound Demand by Comunitat Autònoma")
        ccaa_agg = (
            df_f.groupby("autonomous_community")["total_tourists"]
            .sum().reset_index()
            .sort_values("total_tourists", ascending=False)
        )
        ccaa_agg["share_pct"] = (ccaa_agg["total_tourists"] / ccaa_agg["total_tourists"].sum() * 100).round(1)

        fig_ccaa = px.bar(
            ccaa_agg, x="autonomous_community", y="total_tourists",
            color="share_pct", color_continuous_scale=["#1e3a8a", CYAN],
            text=ccaa_agg["share_pct"].apply(lambda x: f"{x:.1f}%"),
        )
        fig_ccaa.update_layout(
            **base_layout(380, xaxis_title="", yaxis_title="Travellers"),
            xaxis_tickangle=-45,
            coloraxis_colorbar=dict(title="Share %"),
        )
        st.plotly_chart(fig_ccaa, use_container_width=True)

    # — Territorial evolution
    if has_province:
        st.subheader("📈 Top 5 Provinces — Quarterly Evolution")
        top5_prov = prov_agg.head(5)["depart_province"].tolist()
        prov_time = (
            df_f[df_f["depart_province"].isin(top5_prov)]
            .groupby([df_f[df_f["depart_province"].isin(top5_prov)]["period"].dt.to_period("Q").astype(str), "depart_province"])
            ["total_tourists"].sum().reset_index()
            .rename(columns={"period": "quarter"})
        )
        fig_prov_time = px.line(
            prov_time, x="quarter", y="total_tourists", color="depart_province",
            markers=True,
        )
        fig_prov_time.update_layout(
            **base_layout(350, xaxis_title="", yaxis_title="Travellers"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
        )
        st.plotly_chart(fig_prov_time, use_container_width=True)

    if not has_province and not has_ccaa:
        st.warning(
            "Territorial analysis requires geographic origin columns "
            "(`depart_province`, `autonomous_community`). "
            "Please use the `07_spanish_all_countries_geo.parquet` dataset."
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ROUTE DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🎯 Route Deep Dive":

    dest_opts = sorted(df_f["destination_clean"].unique())
    sel_dest = st.sidebar.selectbox("🛫 Destination Country", dest_opts)
    df_route = df_f[df_f["destination_clean"] == sel_dest].copy()

    st.subheader(f"🎯 Route Analysis: {origin_label} ➔ {sel_dest}")

    # — KPI row
    route_total = df_route["total_tourists"].sum()
    route_avg = df_route.groupby("period")["total_tourists"].sum().mean()

    yearly_totals = df_route.groupby("year")["total_tourists"].sum()
    if len(yearly_totals) >= 2:
        last_two = yearly_totals.sort_index().iloc[-2:]
        route_yoy = ((last_two.iloc[-1] / last_two.iloc[0]) - 1) * 100
    else:
        route_yoy = None

    # Recovery vs 2019 if available
    pax_2019 = df_route[df_route["year"] == 2019]["total_tourists"].sum()
    latest_full_yr = max(selected_years)
    pax_latest_route = df_route[df_route["year"] == latest_full_yr]["total_tourists"].sum()
    recovery = (pax_latest_route / pax_2019 * 100) if pax_2019 > 0 else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Travellers", f"{route_total:,.0f}")
    k2.metric("Monthly Average", f"{route_avg:,.0f}")
    if route_yoy is not None:
        k3.metric(f"YoY ({latest_full_yr})", f"{route_yoy:+.1f}%")
    else:
        k3.metric("YoY", "N/A")
    if recovery is not None and pax_2019 > 0:
        k4.metric(f"Recovery vs 2019", f"{recovery:.0f}%")
    else:
        k4.metric("Recovery vs 2019", "N/A")

    # — Yearly evolution with YoY bars
    st.subheader("📊 Annual Volume & Year-on-Year Change")
    stats = df_route.groupby("year").agg(Total=("total_tourists", "sum")).reset_index()
    stats["YoY_%"] = stats["Total"].pct_change() * 100

    fig_yoy = make_subplots(specs=[[{"secondary_y": True}]])
    fig_yoy.add_trace(
        go.Bar(x=stats["year"], y=stats["Total"], name="Travellers",
               marker_color=CYAN, opacity=0.7),
        secondary_y=False,
    )
    fig_yoy.add_trace(
        go.Scatter(x=stats["year"], y=stats["YoY_%"], name="YoY %",
                   mode="lines+markers+text",
                   text=stats["YoY_%"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else ""),
                   textposition="top center", textfont=dict(size=10, color=AMBER),
                   line=dict(color=AMBER, width=2), marker=dict(size=8)),
        secondary_y=True,
    )
    fig_yoy.update_layout(
        **base_layout(350),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_yoy.update_yaxes(title_text="Travellers", secondary_y=False, gridcolor="rgba(148,163,184,0.1)")
    fig_yoy.update_yaxes(title_text="YoY %", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_yoy, use_container_width=True)

    # — Monthly pattern + Route map
    col_season, col_map = st.columns([1, 1])

    with col_season:
        st.subheader("🗓️ Monthly Seasonality Profile")
        mon_avg = df_route.groupby("month")["total_tourists"].mean().reset_index()
        mon_avg["month_label"] = mon_avg["month"].apply(
            lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m-1]
        )
        peak_month = mon_avg.loc[mon_avg["total_tourists"].idxmax(), "month_label"]
        fig_mon = px.bar(
            mon_avg, x="month_label", y="total_tourists",
            color="total_tourists", color_continuous_scale=["#1e3a8a", CYAN, AMBER],
        )
        fig_mon.update_layout(
            **base_layout(350, xaxis_title="", yaxis_title="Avg. Travellers"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_mon, use_container_width=True)
        st.caption(f"🔥 Peak month: **{peak_month}**")

    with col_map:
        st.subheader("🌐 Route Flow Map")
        geo_cols = ["latitude", "longitude", "destination_lat", "destination_lon"]
        if all(c in df_route.columns for c in geo_cols):
            group_cols = [c for c in ["depart_city"] + geo_cols if c in df_route.columns]
            if "depart_city" not in df_route.columns:
                group_cols = geo_cols
            flow_df = (
                df_route.groupby(group_cols)["total_tourists"]
                .sum().reset_index()
                .sort_values("total_tourists", ascending=False)
                .head(30)
            )
            fig_map = go.Figure()
            max_flow = flow_df["total_tourists"].max()
            for _, row in flow_df.iterrows():
                w = max(0.5, (row["total_tourists"] / max_flow) * 4)
                fig_map.add_trace(go.Scattergeo(
                    lon=[row["longitude"], row["destination_lon"]],
                    lat=[row["latitude"], row["destination_lat"]],
                    mode="lines", line=dict(width=w, color=CYAN_LT),
                    opacity=0.5, showlegend=False,
                ))
            fig_map.update_layout(
                height=350,
                geo=dict(
                    bgcolor=BG_DARK, showland=True, landcolor=BG_SIDE,
                    projection_type="natural earth",
                    showocean=True, oceancolor=BG_DARK,
                ),
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Geographic coordinates not available for route map.")

    # — Monthly trend lines by year (overlay for pattern comparison)
    st.subheader("📈 Monthly Overlay — Year Comparison")
    st.caption("Compare seasonal patterns across years to spot shifts in demand timing.")
    year_month = df_route.groupby(["year", "month"])["total_tourists"].sum().reset_index()
    year_month["month_label"] = year_month["month"].apply(
        lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m-1]
    )
    fig_overlay = px.line(
        year_month, x="month_label", y="total_tourists", color="year",
        markers=True, color_discrete_sequence=px.colors.sequential.ice_r,
    )
    fig_overlay.update_layout(
        **base_layout(350, xaxis_title="", yaxis_title="Travellers"),
        legend=dict(title="Year", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_overlay, use_container_width=True)

    # — Origin breakdown for this destination (if territorial columns exist)
    if has_province:
        st.subheader(f"🏛️ Where does demand for {sel_dest} originate?")
        origin_dest = (
            df_route.groupby("depart_province")["total_tourists"]
            .sum().reset_index()
            .sort_values("total_tourists", ascending=False)
        )
        origin_dest["share"] = (origin_dest["total_tourists"] / origin_dest["total_tourists"].sum() * 100).round(1)

        col_orig_bar, col_orig_table = st.columns([1.2, 1])
        with col_orig_bar:
            fig_orig = px.bar(
                origin_dest.head(10), x="total_tourists", y="depart_province",
                orientation="h", text=origin_dest.head(10)["share"].apply(lambda x: f"{x:.1f}%"),
                color_discrete_sequence=[CYAN],
            )
            fig_orig.update_layout(
                **base_layout(350, xaxis_title="Travellers", yaxis=dict(autorange="reversed", title="")),
            )
            st.plotly_chart(fig_orig, use_container_width=True)

        with col_orig_table:
            st.dataframe(
                origin_dest.head(15).rename(columns={
                    "depart_province": "Province", "total_tourists": "Travellers", "share": "Share %"
                }),
                use_container_width=True, hide_index=True,
            )

    # — Destination intelligence card from NB-08 summary
    if df_summary is not None:
        dest_key = sel_dest
        dest_intel = df_summary[df_summary["destination"].str.lower() == dest_key.lower()]
        if len(dest_intel) == 0 and "destination_clean" in df_summary.columns:
            dest_intel = df_summary[df_summary["destination_clean"].str.lower() == dest_key.lower()]
        if len(dest_intel) > 0:
            st.subheader(f"🧠 Intelligence Card — {sel_dest}")
            latest_intel = dest_intel.sort_values("year").iloc[-1]
            ic1, ic2, ic3, ic4, ic5 = st.columns(5)
            ic1.metric("Ranking", f"#{int(latest_intel.get('ranking', 0))}")
            ic2.metric("Market Share", f"{latest_intel.get('share_%', 0):.2f}%")
            ic3.metric("Seasonality CV", f"{latest_intel.get('seasonality_cv', 0):.3f}")
            ic4.metric("Search Corr.", f"{latest_intel.get('corr_searches', 0):.3f}")
            peak = latest_intel.get("top_3_months", "—")
            ic5.metric("Peak Months", str(peak))


# ── FOOTER ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    f"<p style='text-align:center; color:{SLATE}; font-size:0.8rem;'>"
    "Tourism Intelligence Framework · IT Academy / Barcelona Activa · "
    "Data: INE Experimental Mobility Statistics (Jul 2019 – Dec 2025) · "
    "Capstone Project — Vanessa Bujaldon"
    "</p>",
    unsafe_allow_html=True,
)
