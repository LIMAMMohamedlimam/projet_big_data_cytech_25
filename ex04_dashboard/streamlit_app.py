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

# CSS personnalisé pour fond clair et design épuré
st.markdown("""
<style>
    /* Fond principal clair */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Titre principal */
    .main-header {
        font-size: 3.5rem;
        color: #1e3a8a;
        text-align: center;
        font-weight: 800;
        margin-bottom: 1rem;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sous-titre */
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards des KPIs */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Titres de sections */
    .section-title {
        color: #1e293b;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Amélioration des métriques Streamlit */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 600;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px solid #e2e8f0;
    }
    
    /* Boutons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Graphiques */
    .plot-container {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 2px solid #e2e8f0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# EN-TÊTE CENTRÉ
# ============================================================

st.markdown('<h1 class="main-header">NYC YELLOW TAXI DASHBOARD</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">CY Tech - Big Data Project 2026</p>', unsafe_allow_html=True)

# ============================================================
# FILTRES ALIGNÉS HORIZONTALEMENT
# ============================================================

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
    
    # Filtres en ligne
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    
    with col_f1:
        date_range = st.date_input(
            "📅 Période d'analyse",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    with col_f2:
        hour_range = st.slider(
            "🕐 Plage horaire",
            0, 23, (0, 23)
        )
    
    with col_f3:
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()
else:
    st.error("⚠️ Aucune donnée disponible dans la base de données")
    st.stop()

# Conversion des dates pour la requête
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

st.markdown("---")


# ============================================================
# SECTION 1: KPIs PRINCIPAUX (PAYSAGE)
# ============================================================

st.markdown('<h2 class="section-title">📊 Indicateurs Clés de Performance</h2>', unsafe_allow_html=True)

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
    st.metric(label="🚖 Total Courses", value=f"{kpi_data['total_trips'][0]:,}")

with col2:
    st.metric(label="💰 Revenu Total", value=f"${kpi_data['total_revenue'][0]:,.0f}")

with col3:
    st.metric(label="💵 Tarif Moyen", value=f"${kpi_data['avg_fare'][0]:.2f}")

with col4:
    st.metric(label="📏 Distance Moyenne", value=f"{kpi_data['avg_distance'][0]:.2f} mi")

with col5:
    st.metric(label="⏱️ Durée Moyenne", value=f"{kpi_data['avg_duration'][0]:.0f} min")

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# SECTION 2: ANALYSE TEMPORELLE (PAYSAGE)
# ============================================================

st.markdown('<h2 class="section-title">📅 Analyse Temporelle</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
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
        color_continuous_scale='Viridis'
    )

    fig_dow.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569') , # couleur globale du texte
        yaxis=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        ),
        yaxis2=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        )
    )

    # Couleur des valeurs (ticks) + titres axes
    fig_dow.update_xaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))
    fig_dow.update_yaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))

    st.plotly_chart(fig_dow, use_container_width=True)

with col2:
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
    fig_hour.update_traces(line_color='#667eea', marker=dict(size=8, color='#764ba2'))

    fig_hour.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569'),
        yaxis=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        ),
        yaxis2=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        )
    )

    fig_hour.update_xaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))
    fig_hour.update_yaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))

    st.plotly_chart(fig_hour, use_container_width=True)


# ============================================================
# SECTION 3: ANALYSE GÉOGRAPHIQUE (PAYSAGE)
# ============================================================

st.markdown('<h2 class="section-title">🗺️ Analyse Géographique</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
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
        orientation='h',
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_pickup.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569'),
        legend=dict(title_font=dict(color="#1e293b") , font=dict(color="#1e293b")  # couleur du texte des items
    )
        
    )

    # axes ticks + titres (utile ici surtout pour l’axe X; l’axe Y a des catégories)
    fig_pickup.update_xaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))
    fig_pickup.update_yaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))

    st.plotly_chart(fig_pickup, use_container_width=True)

with col2:
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
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig_borough.update_layout(
        paper_bgcolor='white',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569'),
        legend=dict(title_font=dict(color="#1e293b") , font=dict(color="#1e293b"))  # couleur du texte des items
        
    )

    # Pour un pie: couleur du texte sur/près des secteurs (pas x/y axes)
    # (utile si tu affiches "percent", "label", etc.)
    fig_borough.update_traces(
        insidetextfont=dict(color="#1e293b"),
        outsidetextfont=dict(color="#1e293b")
    )

    st.plotly_chart(fig_borough, use_container_width=True)


# ============================================================
# SECTION 4: ANALYSE FINANCIÈRE (PAYSAGE)
# ============================================================

st.markdown('<h2 class="section-title">💳 Analyse Financière</h2>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
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
        color_continuous_scale='Teal'
    )

    fig_payment.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569'),
        # legend=dict(title_font=dict(color="#1e293b") , font=dict(color="#1e293b"))  # couleur du texte des items
        yaxis=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        ),
        yaxis2=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        )

    )

    fig_payment.update_xaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))
    fig_payment.update_yaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))

    st.plotly_chart(fig_payment, use_container_width=True)

with col2:
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
        go.Bar(
            name='Nombre de courses',
            x=vendor_data['vendor_name'],
            y=vendor_data['trip_count'],
            yaxis='y',
            offsetgroup=1,
            marker_color='#667eea'
        ),
        go.Bar(
            name='Tarif moyen',
            x=vendor_data['vendor_name'],
            y=vendor_data['avg_fare'],
            yaxis='y2',
            offsetgroup=2,
            marker_color='#764ba2'
        )
    ])

    fig_vendor.update_layout(
        title='Performance par fournisseur',
        barmode='group',
        paper_bgcolor='white',
        plot_bgcolor='#f8f9fa',
        title_font_size=16,
        title_font_color='#1e293b',
        font=dict(color='#475569'),
        yaxis=dict(title='Nombre de courses'),
        yaxis2=dict(title='Tarif moyen ($)', overlaying='y', side='right')
    )

    # Important: ici tu as 2 axes Y (y et y2) => update_yaxes(..., secondary_y=...) ne marche pas.
    # On met explicitement yaxis / yaxis2
    fig_vendor.update_xaxes(tickfont=dict(color="#475569"), title_font=dict(color="#1e293b"))
    
    fig_vendor.update_layout(
        yaxis=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        ),
        yaxis2=dict(
            title_font=dict(color="#1e293b"),
            tickfont=dict(color="#475569")
        )
    )

    st.plotly_chart(fig_vendor, use_container_width=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p><strong>NYC Yellow Taxi Dashboard</strong> | CY Tech - Big Data Project 2026</p>
    <p>Projet réalisé dans le cadre du cours Big Data</p>
</div>
""", unsafe_allow_html=True)
