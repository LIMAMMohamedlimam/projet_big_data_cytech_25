"""
NYC Yellow Taxi Dashboard
CY Tech - Big Data Project - TP4
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.db_utils import run_query

# Configuration de la page
st.set_page_config(
    page_title="NYC Taxi Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FFD700;
        text-align: center;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# En-tête
st.markdown('<h1 class="main-header">🚕 NYC Yellow Taxi Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Filtres
st.sidebar.header("🔍 Filtres")

# Requête pour les dates disponibles
dates_query = """
SELECT DISTINCT date_value 
FROM dim_date d
JOIN fact_trips f ON d.date_key = f.pickup_date_key
ORDER BY date_value
"""
available_dates = run_query(dates_query)

if not available_dates.empty:
    min_date = available_dates['date_value'].min()
    max_date = available_dates['date_value'].max()
    
    date_range = st.sidebar.date_input(
        "Période d'analyse",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    st.error("Aucune donnée disponible dans la base de données")
    st.stop()

# Filtre par heure
hour_range = st.sidebar.slider(
    "Plage horaire",
    0, 23, (0, 23)
)

# Bouton de rafraîchissement
if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

# Conversion des dates pour la requête
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

# ============================================================
# SECTION 1: KPIs PRINCIPAUX
# ============================================================

st.header("📊 Indicateurs Clés")

kpi_query = f"""
SELECT 
    COUNT(*) as total_trips,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance,
    AVG(trip_duration_minutes) as avg_duration
FROM fact_trips f
JOIN dim_date d ON f.pickup_date_key = d.date_key
JOIN dim_time t ON f.pickup_time_key = t.time_key
WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
    AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
"""

kpi_data = run_query(kpi_query)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="🚖 Total Courses",
        value=f"{kpi_data['total_trips'][0]:,}",
        delta=None
    )

with col2:
    st.metric(
        label="💰 Revenu Total",
        value=f"${kpi_data['total_revenue'][0]:,.0f}",
        delta=None
    )

with col3:
    st.metric(
        label="💵 Tarif Moyen",
        value=f"${kpi_data['avg_fare'][0]:.2f}",
        delta=None
    )

with col4:
    st.metric(
        label="📏 Distance Moyenne",
        value=f"{kpi_data['avg_distance'][0]:.2f} mi",
        delta=None
    )

with col5:
    st.metric(
        label="⏱️ Durée Moyenne",
        value=f"{kpi_data['avg_duration'][0]:.0f} min",
        delta=None
    )

st.markdown("---")

# ============================================================
# SECTION 2: ANALYSE TEMPORELLE
# ============================================================

st.header("📅 Analyse Temporelle")

col1, col2 = st.columns(2)

with col1:
    # Revenue par jour de la semaine
    dow_query = f"""
    SELECT 
        d.day_name,
        d.day_of_week,
        COUNT(*) as trip_count,
        SUM(f.total_amount) as total_revenue
    FROM fact_trips f
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
    GROUP BY d.day_name, d.day_of_week
    ORDER BY d.day_of_week
    """
    
    dow_data = run_query(dow_query)
    
    fig_dow = px.bar(
        dow_data,
        x='day_name',
        y='total_revenue',
        title='Revenu par jour de la semaine',
        labels={'day_name': 'Jour', 'total_revenue': 'Revenu ($)'},
        color='total_revenue',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_dow, use_container_width=True)

with col2:
    # Distribution par heure
    hour_query = f"""
    SELECT 
        t.hour,
        COUNT(*) as trip_count,
        AVG(f.total_amount) as avg_fare
    FROM fact_trips f
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
    GROUP BY t.hour
    ORDER BY t.hour
    """
    
    hour_data = run_query(hour_query)
    
    fig_hour = px.line(
        hour_data,
        x='hour',
        y='trip_count',
        title='Nombre de courses par heure',
        labels={'hour': 'Heure', 'trip_count': 'Nombre de courses'},
        markers=True
    )
    st.plotly_chart(fig_hour, use_container_width=True)

# ============================================================
# SECTION 3: ANALYSE GÉOGRAPHIQUE
# ============================================================

st.header("🗺️ Analyse Géographique")

col1, col2 = st.columns(2)

with col1:
    # Top zones de pickup
    pickup_query = f"""
    SELECT 
        l.zone,
        l.borough,
        COUNT(*) as pickup_count
    FROM fact_trips f
    JOIN dim_location l ON f.pickup_location_key = l.location_key
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
    GROUP BY l.zone, l.borough
    ORDER BY pickup_count DESC
    LIMIT 10
    """
    
    pickup_data = run_query(pickup_query)
    
    fig_pickup = px.bar(
        pickup_data,
        y='zone',
        x='pickup_count',
        color='borough',
        title='Top 10 zones de pickup',
        labels={'zone': 'Zone', 'pickup_count': 'Courses'},
        orientation='h'
    )
    fig_pickup.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_pickup, use_container_width=True)

with col2:
    # Répartition par arrondissement
    borough_query = f"""
    SELECT 
        l.borough,
        COUNT(*) as trip_count,
        SUM(f.total_amount) as total_revenue
    FROM fact_trips f
    JOIN dim_location l ON f.pickup_location_key = l.location_key
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
        AND l.borough IS NOT NULL
    GROUP BY l.borough
    ORDER BY trip_count DESC
    """
    
    borough_data = run_query(borough_query)
    
    fig_borough = px.pie(
        borough_data,
        values='trip_count',
        names='borough',
        title='Répartition des courses par arrondissement',
        hole=0.4
    )
    st.plotly_chart(fig_borough, use_container_width=True)

# ============================================================
# SECTION 4: ANALYSE FINANCIÈRE
# ============================================================

st.header("💳 Analyse Financière")

col1, col2 = st.columns(2)

with col1:
    # Types de paiement
    payment_query = f"""
    SELECT 
        p.payment_description,
        COUNT(*) as trip_count,
        SUM(f.total_amount) as total_revenue
    FROM fact_trips f
    JOIN dim_payment p ON f.payment_key = p.payment_key
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
    GROUP BY p.payment_description
    ORDER BY trip_count DESC
    """
    
    payment_data = run_query(payment_query)
    
    fig_payment = px.bar(
        payment_data,
        x='payment_description',
        y='total_revenue',
        title='Revenu par type de paiement',
        labels={'payment_description': 'Type de paiement', 'total_revenue': 'Revenu ($)'},
        color='total_revenue',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_payment, use_container_width=True)

with col2:
    # Performance par vendor
    vendor_query = f"""
    SELECT 
        v.vendor_name,
        COUNT(*) as trip_count,
        AVG(f.total_amount) as avg_fare
    FROM fact_trips f
    JOIN dim_vendor v ON f.vendor_key = v.vendor_key
    JOIN dim_date d ON f.pickup_date_key = d.date_key
    JOIN dim_time t ON f.pickup_time_key = t.time_key
    WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
        AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
    GROUP BY v.vendor_name
    ORDER BY trip_count DESC
    """
    
    vendor_data = run_query(vendor_query)
    
    fig_vendor = go.Figure(data=[
        go.Bar(name='Nombre de courses', x=vendor_data['vendor_name'], y=vendor_data['trip_count'], yaxis='y', offsetgroup=1),
        go.Bar(name='Tarif moyen', x=vendor_data['vendor_name'], y=vendor_data['avg_fare'], yaxis='y2', offsetgroup=2)
    ])
    fig_vendor.update_layout(
        title='Performance par fournisseur',
        yaxis=dict(title='Nombre de courses'),
        yaxis2=dict(title='Tarif moyen ($)', overlaying='y', side='right'),
        barmode='group'
    )
    st.plotly_chart(fig_vendor, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>NYC Yellow Taxi Dashboard | CY Tech - Big Data Project 2026</p>
</div>
""", unsafe_allow_html=True)
