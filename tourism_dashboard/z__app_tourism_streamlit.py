 
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
    df = pd.read_parquet("data/07_streamlit_dataset.parquet")
    df["period"] = pd.to_datetime(df["period"])
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
    /* Estilització del Sidebar per assemblar-se més a la imatge */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

 
# HEADER (Títol superior fora del sidebar)
 
st.markdown("<h1>🌍 Tourism Intelligence Framework</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; margin-top: -15px;'>Strategic Analytics for Outbound Flight Capacity Allocation</p>", unsafe_allow_html=True)
st.markdown("---")

 
# SIDEBAR (MENÚ LATERAL)
 
st.sidebar.title("Parametrització")

# Estructura del sidebar similar a la imatge
dashboard_mode = st.sidebar.radio("Perspectiva d'Anàlisi:", ["Origen (Mercat Emissor)", "Destinació (Mercat Receptor)"])

st.sidebar.markdown("---")
years = sorted(df["year"].dropna().unique())
selected_years = st.sidebar.slider("Finestra Temporal:", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))

# Filtre base d'anys
df_f_base = df[(df["year"] >= selected_years[0]) & (df["year"] <= selected_years[1])].copy()

 
# LÒGICA DE LA PANTALLA 1: ORIGEN (EMISSOR)
 
if dashboard_mode == "Origen (Mercat Emissor)":
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtres Geogràfics")
    
    territory_level = st.sidebar.selectbox("Nivell Territorial:", ["Total Espanya", "Comunitat Autònoma", "Província"])
    
    # 2. Assignem df_f
    df_f = df_f_base.copy()
    
    if territory_level == "Comunitat Autònoma":
        regions = sorted(df_f["autonomous_community"].dropna().unique())
        sel = st.sidebar.multiselect("Selecciona Comunitat(s):", regions, default=regions[0] if regions else None)
        df_f = df_f[df_f["autonomous_community"].isin(sel)] if sel else df_f
        title_prefix = f"Anàlisi d'Origen: {' + '.join(sel) if sel else 'Cap selecció'}"
        
    elif territory_level == "Província":
        provs = sorted(df_f["province"].dropna().unique())
        default_prov = ["Barcelona"] if "Barcelona" in provs else [provs[0]] if provs else None
        sel = st.sidebar.multiselect("Selecciona Província/es:", provs, default=default_prov)
        df_f = df_f[df_f["province"].isin(sel)] if sel else df_f
        title_prefix = f"Anàlisi d'Origen: {' + '.join(sel) if sel else 'Cap selecció'}"
        
    else:
        title_prefix = "Anàlisi d'Origen: Espanya (Total)"

    st.subheader(f"📊 {title_prefix}")

    # Càlculs per a la taula d'origen
    @st.cache_data
    def get_origin_metrics(data):
        if data.empty:
            return pd.DataFrame(columns=["destination_clean", "total_vials", "avg_monthly", "market_share", "yoy_growth", "top_month"])

        metrics = data.groupby("destination_clean").agg(
            total_vials=("total_tourists", "sum"),
            avg_monthly=("total_tourists", "mean")
        ).reset_index()
        
        metrics["avg_monthly"] = metrics["avg_monthly"].round(0).fillna(0).astype(int)
        
        total_total = metrics["total_vials"].sum()
        metrics["market_share"] = (metrics["total_vials"] / total_total * 100).round(2) if total_total > 0 else 0.0
        
        # Creixement del Període Seleccionat (Últim vs Primer any filtrat)
        yoy_pivot = data.groupby(["destination_clean", "year"])["total_tourists"].sum().unstack(fill_value=0)
        cols = sorted(yoy_pivot.columns)
        if len(cols) >= 2:
            y_curr, y_first = cols[-1], cols[0]
            yoy_series = ((yoy_pivot[y_curr] - yoy_pivot[y_first]) / yoy_pivot[y_first].replace(0, np.nan)) * 100
            yoy_series = yoy_series.fillna(0).round(1)
        else:
            yoy_series = pd.Series(0.0, index=yoy_pivot.index)
            
        metrics = metrics.merge(yoy_series.rename("yoy_growth"), on="destination_clean", how="left").fillna(0)
        
        top_month_series = data.groupby(["destination_clean", "month"])["total_tourists"].sum().reset_index()
        if not top_month_series.empty:
            idx = top_month_series.groupby("destination_clean")["total_tourists"].idxmax()
            top_months = top_month_series.loc[idx, ["destination_clean", "month"]]
            metrics = metrics.merge(top_months.rename(columns={"month": "top_month"}), on="destination_clean", how="left")
        else:
            metrics["top_month"] = 1
            
        return metrics.sort_values("total_vials", ascending=False)

    dest_metrics = get_origin_metrics(df_f)

    if dest_metrics.empty:
        st.warning("⚠️ No hi ha registres de viatgers per a aquesta combinació de filtres.")
        st.stop()

     
    # KPIs, CONTINENTS I TREEMAP DE DESTINACIONS
     
    col_kpi, col_donut, col_tree = st.columns([1, 1.2, 2])
    
    with col_kpi:
        st.metric("Viatgers Totals", f"{df_f['total_tourists'].sum():,.0f}")
        st.metric("Rutes Actives", df_f['destination_clean'].nunique())
        top_country = dest_metrics.iloc[0]["destination_clean"] if not dest_metrics.empty else "N/A"
        st.metric("Destinació Líder", top_country)

    with col_donut:
        if "continent" in df_f.columns:
            df_donut = df_f.copy()
            # Canviem el nom de l'etiqueta d'Europa per reflectir la realitat filtrada del dataset
            df_donut.loc[df_donut["continent"] == "Europe", "continent"] = "Europe (Nordic/Mid-Haul)*"
            
            continent_df = df_donut.groupby("continent")["total_tourists"].sum().reset_index()
            
            fig_donut = px.pie(
                continent_df, 
                values="total_tourists", 
                names="continent", 
                hole=0.6,
                title="Distribució per Continent",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            fig_donut.update_layout(
                margin=dict(t=35, b=10, l=10, r=10), 
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown("<p style='font-size:11px; color:#94A3B8; text-align:center;'>*Europe només inclou rutes seleccionades: Islàndia, Finlàndia i Noruega.</p>", unsafe_allow_html=True)
        else:
            st.info("No hi ha dades de continent disponibles.")

    with col_tree:
        fig_tree = px.treemap(dest_metrics.head(20), path=["destination_clean"], values="total_vials",
                              color="market_share", color_continuous_scale="Viridis",
                              title="Quota de Mercat (Top 20 Destinacions)")
        fig_tree.update_layout(margin=dict(t=35, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_tree, use_container_width=True)

     
    # TAULA DE RENDIMENT COMERCIAL ORIGINAL COMPLETA
     
    st.subheader("📈 Rendiment del Catàleg de Destinacions")
    display_table = dest_metrics.head(30).copy()
    display_table = display_table[["destination_clean", "total_vials", "avg_monthly", "market_share", "yoy_growth", "top_month"]]
    display_table.columns = ["Destinació", "Volum Total", "Mitjana Mensual", "Quota %", "Creixement Període %", "Mes Pic"]
    
    st.dataframe(
        display_table,
        column_config={
            "Quota %": st.column_config.ProgressColumn("Quota de Mercat", format="%.2f%%", min_value=0, max_value=100),
            "Creixement Període %": st.column_config.NumberColumn("Creixement (Període)", format="%+.1f%%"),
            "Volum Total": st.column_config.NumberColumn("Volum Total", format="%d")
        },
        hide_index=True, 
        use_container_width=True
    )

    st.markdown("---")

     
    # HEATMAP PER FILA (COLORS INDEPENDENTS PER PAÍS + TEXT EN %)
     
    st.subheader("🗓️ Radiografia d'Estacionalitat (Intensitat independent per país)")
    
    top_15_dests = dest_metrics.head(15)["destination_clean"].tolist()
    h_df = df_f[df_f["destination_clean"].isin(top_15_dests)].groupby(["destination_clean", "month"])["total_tourists"].sum().reset_index()
    
    if not h_df.empty:
        h_pivot = h_df.pivot(index="destination_clean", columns="month", values="total_tourists").fillna(0)
        
        # 1. Dades per al TEXT (% real mensual de cada país)
        h_pivot_pct = (h_pivot.div(h_pivot.sum(axis=1), axis=0) * 100).round(1)
        
        # 2. Dades per al COLOR (Escalat del 0 al 1 exclusivament dins de cada fila)
        h_pivot_color = h_pivot.div(h_pivot.max(axis=1), axis=0)
        
        # Escala Divergent: Blau fosc (fluix) -> Blanc (mitjà) -> Vermell (pic de la ruta)
        escala_divergent = [
            [0.0, "#1e3a8a"],  
            [0.5, "#f8fafc"],  
            [1.0, "#b91c1c"]   
        ]
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=h_pivot_color.values,
            x=h_pivot_color.columns,
            y=h_pivot_color.index,
            text=h_pivot_pct.apply(lambda x: x.map("{:.1f}%".format)).values,
            texttemplate="%{text}",
            colorscale=escala_divergent,
            showscale=False,
            hoverinfo="x+y+text"
        ))
        
        fig_heat.update_layout(
            title="Percentatge de trànsit mensual (El vermell marca el pic específic de cada destí)",
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            height=500,
            xaxis=dict(tickmode='linear', dtick=1, title="Mes de l'Any"),
            yaxis=dict(title=""),
            margin=dict(l=10, r=10, b=10, t=40)
        )
        
        fig_heat.update_traces(textfont=dict(size=11, family="Arial"))
        st.plotly_chart(fig_heat, use_container_width=True)

 
# LÒGICA DE LA PANTALLA 2: DESTINACIÓ (RECEPTOR)
 
else:
    df_f = df_f_base.copy()
    destinations = sorted(df_f["destination_clean"].dropna().unique())
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtre de Destí")
    sel_dest = st.sidebar.selectbox("Selecciona País de Destinació:", destinations)
    df_f = df_f[df_f["destination_clean"] == sel_dest]
    
    st.subheader(f"🎯 Radiografia de la Destinació: {sel_dest}")
    
    if df_f.empty:
        st.warning("⚠️ No hi ha dades per a aquest destí en els anys seleccionats.")
        st.stop()
    
    tot_travelers = df_f["total_tourists"].sum()
    top_prov = df_f.groupby("province")["total_tourists"].sum().idxmax() if not df_f.empty else "N/A"
    peak_month = df_f.groupby("month")["total_tourists"].sum().idxmax() if not df_f.empty else "N/A"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Viatgers Rebuts (Des d'Espanya)", f"{tot_travelers:,.0f}")
    col2.metric("Principal Província Emissora", top_prov)
    col3.metric("Temporada Alta (Mes Pic)", f"Mes {peak_month}")
    
    st.markdown("---")
    
    col_bar, col_season = st.columns(2)
    
    with col_bar:
        prov_df = df_f.groupby("province", as_index=False)["total_tourists"].sum().sort_values("total_tourists", ascending=True).tail(10)
        fig_prov = px.bar(prov_df, x="total_tourists", y="province", orientation="h", 
                          title=f"D'on viatgen a {sel_dest}?", template="plotly_dark",
                          color="total_tourists", color_continuous_scale="Blues")
        fig_prov.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, l=10, r=10, b=10), coloraxis_showscale=False, xaxis_title="Viatgers")
        st.plotly_chart(fig_prov, use_container_width=True)
        
    with col_season:
        season_df = df_f.groupby("month", as_index=False)["total_tourists"].sum()
        fig_season = px.line(season_df, x="month", y="total_tourists", markers=True,
                             title=f"Corba d'Estacionalitat ({sel_dest})", template="plotly_dark")
        fig_season.update_traces(line=dict(width=4, color="#06b6d4"), marker=dict(size=8))
        fig_season.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, l=10, r=10, b=10), xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_season, use_container_width=True)

    st.markdown("---")
    
    st.subheader(f"🗺️ Rutes Captives: Extracció Territorial cap a {sel_dest}")
    flow_df = df_f.groupby(["city", "latitude", "longitude", "destination_lat", "destination_lon"], as_index=False)["total_tourists"].sum().dropna()
    flow_df = flow_df.sort_values("total_tourists", ascending=False).head(50)

    fig_map = go.Figure()
    for _, row in flow_df.iterrows():
        fig_map.add_trace(go.Scattergeo(
            lon=[row["longitude"], row["destination_lon"]],
            lat=[row["latitude"], row["destination_lat"]],
            mode="lines+markers",
            line=dict(width=max(row["total_tourists"] / 5000, 1), color="#d946ef"),
            marker=dict(size=3, color="#d946ef"),
            hoverinfo="text",
            text=f"{row['city']} → {sel_dest}: {int(row['total_tourists']):,} pax"
        ))

    fig_map.update_layout(
        height=500, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            bgcolor="#050b16", showland=True, landcolor="#1e293b",
            showcountries=True, countrycolor="#334155",
            projection_type="natural earth",
            center=dict(lat=40.4168, lon=-3.7038), projection_scale=1.5
        ),
        showlegend=False
    )
    st.plotly_chart(fig_map, use_container_width=True)