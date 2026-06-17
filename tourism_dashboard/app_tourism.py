 
# IMPORTS
 
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

 
# PAGE CONFIG
 
st.set_page_config(
    page_title="Outbound Tourism Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

 
# LOAD DATA
 
@st.cache_data
def load_data():
    df = pd.read_parquet("tourism_dashboard/data/07_streamlit_dataset.parquet")
    df["period"] = pd.to_datetime(df["period"])
    # Creem una columna de nom de mes abreujat per als gràfics
    df['month_name'] = df['period'].dt.strftime('%b')
    return df

df = load_data()

 
# STYLE & COLORS
 
st.markdown("""
    <style>
    .stApp { background-color: #050b16; }
    h1, h2, h3 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .stDataFrame { background-color: #1e293b; border-radius: 8px; }
    div[data-testid="stMetric"] {
        background-color: #0f172a; padding: 15px; border-radius: 10px; border-left: 5px solid #06b6d4;
    }
    [data-testid="stSidebar"] { background-color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# HEADER
st.markdown("<h1>🌍 Tourism Intelligence Framework</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; margin-top: -15px;'>Strategic Analytics for Outbound Flight Capacity Allocation</p>", unsafe_allow_html=True)
st.markdown("---")

# SIDEBAR
st.sidebar.title("Parametrització")
dashboard_mode = st.sidebar.radio("Perspectiva d'Anàlisi:", ["Origen (Mercat Emissor)", "Destinació (Mercat Receptor)"])
st.sidebar.markdown("---")
years = sorted(df["year"].dropna().unique())
selected_years = st.sidebar.slider("Finestra Temporal:", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))

df_f_base = df[(df["year"] >= selected_years[0]) & (df["year"] <= selected_years[1])].copy()

 
# PÀGINA 1: ORIGEN
 
if dashboard_mode == "Origen (Mercat Emissor)":
    df_f = df_f_base.copy()
    
    st.subheader("📈 Evolució mensual de sortides (Viatgers totals)")
    
    evol_df = df_f.groupby("period")["total_tourists"].sum().reset_index()
    fig_evol = px.line(evol_df, x="period", y="total_tourists", markers=True, 
                       color_discrete_sequence=["#38bdf8"])
    

    fig_evol.update_traces(text=evol_df["total_tourists"].apply(lambda x: f"{x/1000000:.1f}M"), 
                           textposition="top center", mode="lines+markers+text")
    
    fig_evol.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                           height=350, margin=dict(t=20, b=20, l=0, r=0),
                           xaxis_title="", yaxis_title="Viatgers")
    st.plotly_chart(fig_evol, use_container_width=True)


    @st.cache_data
    def get_origin_metrics(data):
        m = data.groupby("destination_clean").agg(total_vials=("total_tourists", "sum"), avg_monthly=("total_tourists", "mean")).reset_index()
        m["market_share"] = (m["total_vials"] / m["total_vials"].sum() * 100).round(2)
        return m.sort_values("total_vials", ascending=False)

    dest_metrics = get_origin_metrics(df_f)


    c1, c2, c3 = st.columns([1, 1.2, 2])
    with c1:
        st.metric("Viatgers totals", f"{df_f['total_tourists'].sum():,.0f}")
        st.metric("Rutes actives", df_f['destination_clean'].nunique())
    with c2:
        continent_df = df_f.groupby("continent")["total_tourists"].sum().reset_index()
        fig_don = px.pie(continent_df, values="total_tourists", names="continent", hole=0.5, title="Pes per Continent")
        fig_don.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_don, use_container_width=True)
    with c3:
        fig_tr = px.treemap(dest_metrics.head(15), path=["destination_clean"], values="total_vials", title="Top 15 Destins")
        fig_tr.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_tr, use_container_width=True)

    st.subheader("🗓️ Radiografia d'Estacionalitat (Intensitat independent per país)")
    top_15 = dest_metrics.head(15)["destination_clean"].tolist()
    h_df = df_f[df_f["destination_clean"].isin(top_15)].groupby(["destination_clean", "month"])["total_tourists"].sum().reset_index()
    h_pivot = h_df.pivot(index="destination_clean", columns="month", values="total_tourists").fillna(0)
    h_pct = (h_pivot.div(h_pivot.sum(axis=1), axis=0) * 100).round(1)
    h_color = h_pivot.div(h_pivot.max(axis=1), axis=0)

    fig_heat = go.Figure(data=go.Heatmap(z=h_color.values, x=h_color.columns, y=h_color.index,
            text=h_pct.apply(lambda x: x.map("{:.1f}%".format)).values, texttemplate="%{text}",
            colorscale=[[0, "#1e3a8a"], [0.5, "#f8fafc"], [1, "#b91c1c"]], showscale=False))
    fig_heat.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, b=10, t=40))
    st.plotly_chart(fig_heat, use_container_width=True)

 
# PÀGINA 2: DESTINACIÓ
 
else:
    df_f_d = df_f_base.copy()
    sel_dest = st.sidebar.selectbox("Selecciona País de Destinació:", sorted(df_f_d["destination_clean"].unique()))
    df_f = df_f_d[df_f_d["destination_clean"] == sel_dest]
    
    st.subheader(f"🎯 Anàlisi detallat de la ruta: Espanya ➔ {sel_dest}")

    col_bar, col_table = st.columns([1, 1.5])
    
    with col_bar:
        st.write("**Promig de viatgers per mes**")
        mon_avg = df_f.groupby("month")["total_tourists"].mean().reset_index()

        fig_mon = px.bar(mon_avg, x="total_tourists", y="month", orientation='h', color="total_tourists",
                         color_continuous_scale="Blues")
        fig_mon.update_layout(showlegend=False, coloraxis_showscale=False, height=400,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              yaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_mon, use_container_width=True)
        
    with col_table:
        st.write("**Resum estadístic de la ruta (Comparatiu YoY)**")

        stats_df = df_f.groupby("year").agg(Total=("total_tourists", "sum")).reset_index()
        stats_df["Var. %"] = stats_df["Total"].pct_change().map("{:+.1f}%".format).replace("nan%", "-")
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        

        flow_df = df_f.groupby(["city", "latitude", "longitude", "destination_lat", "destination_lon"])["total_tourists"].sum().reset_index().head(40)
        fig_map = go.Figure()
        for _, row in flow_df.iterrows():
            fig_map.add_trace(go.Scattergeo(lon=[row["longitude"], row["destination_lon"]], lat=[row["latitude"], row["destination_lat"]],
                mode="lines", line=dict(width=1, color="#38bdf8"), opacity=0.4))
        fig_map.update_layout(height=300, geo=dict(bgcolor="#050b16", showland=True, landcolor="#1e293b", projection_type="natural earth"),
                              margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)