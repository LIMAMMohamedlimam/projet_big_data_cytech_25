# """
# NYC Yellow Taxi Dashboard
# CY Tech - Big Data Project - TP4
# """
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime
# from utils.db_utils import run_query

# # Configuration de la page
# st.set_page_config(
#     page_title="NYC Taxi Dashboard",
#     page_icon="🚕",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # CSS personnalisé
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 3rem;
#         color: #FFD700;
#         text-align: center;
#         font-weight: bold;
#     }
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 20px;
#         border-radius: 10px;
#         box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
#     }
# </style>
# """, unsafe_allow_html=True)

# # En-tête
# st.markdown('<h1 class="main-header">🚕 NYC Yellow Taxi Dashboard</h1>', unsafe_allow_html=True)
# st.markdown("---")

# # Sidebar - Filtres
# st.sidebar.header("🔍 Filtres")

# # Requête pour les dates disponibles
# dates_query = """
# SELECT DISTINCT date_value 
# FROM dim_date d
# JOIN fact_trips f ON d.date_key = f.pickup_date_key
# ORDER BY date_value
# """
# available_dates = run_query(dates_query)

# if not available_dates.empty:
#     min_date = available_dates['date_value'].min()
#     max_date = available_dates['date_value'].max()
    
#     date_range = st.sidebar.date_input(
#         "Période d'analyse",
#         value=(min_date, max_date),
#         min_value=min_date,
#         max_value=max_date
#     )
# else:
#     st.error("Aucune donnée disponible dans la base de données")
#     st.stop()

# # Filtre par heure
# hour_range = st.sidebar.slider(
#     "Plage horaire",
#     0, 23, (0, 23)
# )

# # Bouton de rafraîchissement
# if st.sidebar.button("🔄 Actualiser les données"):
#     st.cache_data.clear()
#     st.rerun()

# # Conversion des dates pour la requête
# if isinstance(date_range, tuple) and len(date_range) == 2:
#     start_date, end_date = date_range
# else:
#     start_date = end_date = date_range

# # ============================================================
# # SECTION 1: KPIs PRINCIPAUX
# # ============================================================

# st.header("📊 Indicateurs Clés")

# kpi_query = f"""
# SELECT 
#     COUNT(*) as total_trips,
#     SUM(total_amount) as total_revenue,
#     AVG(total_amount) as avg_fare,
#     AVG(trip_distance) as avg_distance,
#     AVG(trip_duration_minutes) as avg_duration
# FROM fact_trips f
# JOIN dim_date d ON f.pickup_date_key = d.date_key
# JOIN dim_time t ON f.pickup_time_key = t.time_key
# WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#     AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
# """

# kpi_data = run_query(kpi_query)

# col1, col2, col3, col4, col5 = st.columns(5)

# with col1:
#     st.metric(
#         label="🚖 Total Courses",
#         value=f"{kpi_data['total_trips'][0]:,}",
#         delta=None
#     )

# with col2:
#     st.metric(
#         label="💰 Revenu Total",
#         value=f"${kpi_data['total_revenue'][0]:,.0f}",
#         delta=None
#     )

# with col3:
#     st.metric(
#         label="💵 Tarif Moyen",
#         value=f"${kpi_data['avg_fare'][0]:.2f}",
#         delta=None
#     )

# with col4:
#     st.metric(
#         label="📏 Distance Moyenne",
#         value=f"{kpi_data['avg_distance'][0]:.2f} mi",
#         delta=None
#     )

# with col5:
#     st.metric(
#         label="⏱️ Durée Moyenne",
#         value=f"{kpi_data['avg_duration'][0]:.0f} min",
#         delta=None
#     )

# st.markdown("---")

# # ============================================================
# # SECTION 2: ANALYSE TEMPORELLE
# # ============================================================

# st.header("📅 Analyse Temporelle")

# col1, col2 = st.columns(2)

# with col1:
#     # Revenue par jour de la semaine
#     dow_query = f"""
#     SELECT 
#         d.day_name,
#         d.day_of_week,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY d.day_name, d.day_of_week
#     ORDER BY d.day_of_week
#     """
    
#     dow_data = run_query(dow_query)
    
#     fig_dow = px.bar(
#         dow_data,
#         x='day_name',
#         y='total_revenue',
#         title='Revenu par jour de la semaine',
#         labels={'day_name': 'Jour', 'total_revenue': 'Revenu ($)'},
#         color='total_revenue',
#         color_continuous_scale='Blues'
#     )
#     st.plotly_chart(fig_dow, use_container_width=True)

# with col2:
#     # Distribution par heure
#     hour_query = f"""
#     SELECT 
#         t.hour,
#         COUNT(*) as trip_count,
#         AVG(f.total_amount) as avg_fare
#     FROM fact_trips f
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY t.hour
#     ORDER BY t.hour
#     """
    
#     hour_data = run_query(hour_query)
    
#     fig_hour = px.line(
#         hour_data,
#         x='hour',
#         y='trip_count',
#         title='Nombre de courses par heure',
#         labels={'hour': 'Heure', 'trip_count': 'Nombre de courses'},
#         markers=True
#     )
#     st.plotly_chart(fig_hour, use_container_width=True)

# # ============================================================
# # SECTION 3: ANALYSE GÉOGRAPHIQUE
# # ============================================================

# st.header("🗺️ Analyse Géographique")

# col1, col2 = st.columns(2)

# with col1:
#     # Top zones de pickup
#     pickup_query = f"""
#     SELECT 
#         l.zone,
#         l.borough,
#         COUNT(*) as pickup_count
#     FROM fact_trips f
#     JOIN dim_location l ON f.pickup_location_key = l.location_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY l.zone, l.borough
#     ORDER BY pickup_count DESC
#     LIMIT 10
#     """
    
#     pickup_data = run_query(pickup_query)
    
#     fig_pickup = px.bar(
#         pickup_data,
#         y='zone',
#         x='pickup_count',
#         color='borough',
#         title='Top 10 zones de pickup',
#         labels={'zone': 'Zone', 'pickup_count': 'Courses'},
#         orientation='h'
#     )
#     fig_pickup.update_layout(yaxis={'categoryorder':'total ascending'})
#     st.plotly_chart(fig_pickup, use_container_width=True)

# with col2:
#     # Répartition par arrondissement
#     borough_query = f"""
#     SELECT 
#         l.borough,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_location l ON f.pickup_location_key = l.location_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#         AND l.borough IS NOT NULL
#     GROUP BY l.borough
#     ORDER BY trip_count DESC
#     """
    
#     borough_data = run_query(borough_query)
    
#     fig_borough = px.pie(
#         borough_data,
#         values='trip_count',
#         names='borough',
#         title='Répartition des courses par arrondissement',
#         hole=0.4
#     )
#     st.plotly_chart(fig_borough, use_container_width=True)

# # ============================================================
# # SECTION 4: ANALYSE FINANCIÈRE
# # ============================================================

# st.header("💳 Analyse Financière")

# col1, col2 = st.columns(2)

# with col1:
#     # Types de paiement
#     payment_query = f"""
#     SELECT 
#         p.payment_description,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_payment p ON f.payment_key = p.payment_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY p.payment_description
#     ORDER BY trip_count DESC
#     """
    
#     payment_data = run_query(payment_query)
    
#     fig_payment = px.bar(
#         payment_data,
#         x='payment_description',
#         y='total_revenue',
#         title='Revenu par type de paiement',
#         labels={'payment_description': 'Type de paiement', 'total_revenue': 'Revenu ($)'},
#         color='total_revenue',
#         color_continuous_scale='Greens'
#     )
#     st.plotly_chart(fig_payment, use_container_width=True)

# with col2:
#     # Performance par vendor
#     vendor_query = f"""
#     SELECT 
#         v.vendor_name,
#         COUNT(*) as trip_count,
#         AVG(f.total_amount) as avg_fare
#     FROM fact_trips f
#     JOIN dim_vendor v ON f.vendor_key = v.vendor_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY v.vendor_name
#     ORDER BY trip_count DESC
#     """
    
#     vendor_data = run_query(vendor_query)
    
#     fig_vendor = go.Figure(data=[
#         go.Bar(name='Nombre de courses', x=vendor_data['vendor_name'], y=vendor_data['trip_count'], yaxis='y', offsetgroup=1),
#         go.Bar(name='Tarif moyen', x=vendor_data['vendor_name'], y=vendor_data['avg_fare'], yaxis='y2', offsetgroup=2)
#     ])
#     fig_vendor.update_layout(
#         title='Performance par fournisseur',
#         yaxis=dict(title='Nombre de courses'),
#         yaxis2=dict(title='Tarif moyen ($)', overlaying='y', side='right'),
#         barmode='group'
#     )
#     st.plotly_chart(fig_vendor, use_container_width=True)

# # ============================================================
# # FOOTER
# # ============================================================

# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; color: gray;'>
#     <p>NYC Yellow Taxi Dashboard | CY Tech - Big Data Project 2026</p>
# </div>
# """, unsafe_allow_html=True)



# YanisYS
# yanisys
# Invisible

# YanisYS — 07/12/2025 21:26
# Faut m’inviter
# YanisYS — 16/12/2025 12:11
# Type de fichier joint : acrobat
# Brief_Motivation_ZIDI_Yanis.pdf
# 227.72 KB
# YanisYS — 16/12/2025 16:04
# Type de fichier joint : acrobat
# Brief_Motivation_ZIDI_Yanis.pdf
# 227.72 KB
# Type de fichier joint : acrobat
# Grades_Yanis_ZIDI_Semester1.pdf
# 643.78 KB
# Type de fichier joint : acrobat
# Grades_Yanis_ZIDI_Semester2.pdf
# 238.88 KB
# Type de fichier joint : acrobat
# Pasport_ZIDI_Yanis.pdf
# 141.01 KB
# Type de fichier joint : acrobat
# proof_of_current_enrolmentDI01N3_2025-2026_ZIDI_Yanis.pdf
# 85.65 KB
# Type de fichier joint : acrobat
# Resume_Intership_ZIDI_Yanis.pdf
# 651.10 KB
# Romeo — 16/12/2025 16:11
# https://drive.google.com/drive/folders/1goPQwX7aD2-DFlEGzWBJzYh022JefVcM?usp=sharing
# Google Drive
# YanisYS
#  a commencé un appel qui a duré quelques secondes. — 12/01/2026 22:34
# YanisYS
#  a commencé un appel qui a duré quelques secondes. — 12/01/2026 22:35
# YanisYS — 12/01/2026 22:36
# rappel moi
# Romeo
#  a commencé un appel qui a duré 2 heures. — 12/01/2026 22:36
# Romeo — 12/01/2026 22:46
# Ho Chi Minh Ville,
# YanisYS
#  a commencé un appel qui a duré 2 heures. — 17/01/2026 12:45
# YanisYS — 17/01/2026 12:46
# Transféré
# J'ai un projet à faire en optimisation metaheuristique je t'ai donné ma prob et le lien github que j'ai cloner sur mon vs



# je vais te donner un github qu'il faut utiliser pour s'aider dedans on a dans policies/heuristic des metaheuristiques et dans evals/benchmarck des datasets qu'on doit utiliser

# message.txt
# 3 Ko
# Transféré
# import random
# import numpy as np
# import csv

# class MOHSPolicy:
#     def __init__(self, hm_size=15, archive_size=50):

# MOHS.py
# 7 Ko
# YanisYS — 17/01/2026 12:53
# Transféré
# policy: "MOHS"
# algo: "MOHS"

# env:
#   dataset: "Pakistan"
#   flag: "Tuple30K"

# MOHS.yaml
# 1 Ko
# Romeo — 17/01/2026 12:54
# Image
# YanisYS — 17/01/2026 12:54
# policy: "MOHS"
# algo: "MOHS"

# env:
#   dataset: "Pakistan"
#   flag: "Tuple30K"

# MOHS.yaml
# 1 Ko
# Romeo — 17/01/2026 13:04
# https://github.com/tutur90/Task-Offloading-Fog
# GitHub
# GitHub - tutur90/Task-Offloading-Fog
# Contribute to tutur90/Task-Offloading-Fog development by creating an account on GitHub.
# Contribute to tutur90/Task-Offloading-Fog development by creating an account on GitHub.
# python main.py --config configs/Pakistan/Heuristics/MOHS.yaml
# pip install -r re
# Romeo — 17/01/2026 14:16
# l'article 2202_10628 pour comprendre le contexte
# Article ApplicationOffloadingStrategyForHierarching.pdf Analyse de l'article - Application Offloading Strategy (APSO)
# ✅ Cet article est TRÈS PERTINENT pour ton projet !
# Même si ce n'est pas Harmony Search, cet article montre exactement ce que ta prof demande :
# Critère de ta profPrésent dans l'articleMulti-objectif✅ Oui (coût + utilisation ressources)Archive Pareto✅ Oui (Pareto-Optimal Set)Dominance dans la recherche✅ Oui !Réinjection des solutions✅ Oui !Task Offloading Fog-Cloud✅ Exactement le même contexte
# 🔑 Points clés à retenir pour ton implémentation
# La dominance Pareto intégrée dans la recherche (ce que ta prof veut) :

# "We first select the non-dominated computing devices in the population and put them into a PO set. Next, for selecting a computing device from the current population, we randomly select a computing device from the set as an optimal computing device."

# Les 3 ensembles pour guider la recherche :

# Set 1 : Solutions meilleures que leur best précédent
# Set 2 : Solutions pires que leur best précédent
# Set 3 : Solutions meilleures que le global best

# Mise à jour de position basée sur l'archive :
# dsi = (1 − β)dsi−1 + βMOkl + αεⁱ
# où MOkl vient de l'archive Pareto !
# 📋 Verdict
# Garde cet article comme MODÈLE pour adapter Harmony Search en version multi-objectif. Tu devras :

# Remplacer PSO par Harmony Search
# Garder la même logique d'archive Pareto
# Réinjecter les solutions Pareto dans l'improvisation (comme l'article fait avec les mises à jour de position)

# Continue à m'envoyer tes autres articles - je cherche toujours un article spécifique sur Multi-Objective Harmony Search (MOHS) !
# YanisYS — 17/01/2026 15:13
# python .\visualisation.py
# YanisYS — 03/02/2026 16:02
# https://www.languesfaciles.fr/blog/39-Passer-le-TOEIC-en-ligne-en-2026---Guide-complet-et-conseils#:~:text=Avantages%20du%20test%20TOEIC%20en,vers%20un%20centre%20d'examen.
# Passer le TOEIC en ligne en 2026 : Guide complet et conseils
# Passer le TOEIC en ligne en 2026 est plus flexible et rapide que jamais ! Découvrez les avantages, les exigences et nos conseils pour réussir votre test sereinement. Inscription, matériel requis, déroulement et astuces : suivez notre guide complet pour optimiser votre score !
# Image
# YanisYS — 03/02/2026 16:54
# Image
# YanisYS — 03/02/2026 17:37
# Image
# YanisYS
#  a commencé un appel qui a duré 2 heures. — 03/02/2026 17:41
# YanisYS — 07/02/2026 15:35
# https://github.com/LIMAMMohamedlimam/projet_big_data_cytech_25.git
# GitHub
# GitHub - LIMAMMohamedlimam/projet_big_data_cytech_25
# Contribute to LIMAMMohamedlimam/projet_big_data_cytech_25 development by creating an account on GitHub.
# GitHub - LIMAMMohamedlimam/projet_big_data_cytech_25
# YanisYS
#  a commencé un appel qui a duré une heure. — 09/02/2026 22:36
# Romeo — 09/02/2026 22:43
# Image
# YanisYS — 09/02/2026 22:49
# Type de fichier joint : acrobat
# Projet-V2 (1).pdf
# 118.43 KB
# YanisYS — 10/02/2026 21:42
# yanis.zidiyy@gmail.com
# YanisYS — 00:03
# et ca c'est le code pour la mise en page de l'exo 4
# """
# NYC Yellow Taxi Dashboard
# CY Tech - Big Data Project - TP4
# """
# import streamlit as st
# import pandas as pd

# message.txt
# 16 Ko
# a
# Romeo
# romeo9526
 
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

# # ============================================================
# # SECTION 1: KPIs PRINCIPAUX (PAYSAGE)
# # ============================================================

# st.markdown('<h2 class="section-title">📊 Indicateurs Clés de Performance</h2>', unsafe_allow_html=True)

# kpi_query = f"""
# SELECT 
#     COUNT(*) as total_trips,
#     SUM(total_amount) as total_revenue,
#     AVG(total_amount) as avg_fare,
#     AVG(trip_distance) as avg_distance,
#     AVG(trip_duration_minutes) as avg_duration
# FROM fact_trips f
# JOIN dim_date d ON f.pickup_date_key = d.date_key
# JOIN dim_time t ON f.pickup_time_key = t.time_key
# WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#     AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
# """

# kpi_data = run_query(kpi_query)

# # KPIs en ligne
# col1, col2, col3, col4, col5 = st.columns(5)

# with col1:
#     st.metric(
#         label="🚖 Total Courses",
#         value=f"{kpi_data['total_trips'][0]:,}"
#     )

# with col2:
#     st.metric(
#         label="💰 Revenu Total",
#         value=f"${kpi_data['total_revenue'][0]:,.0f}"
#     )

# with col3:
#     st.metric(
#         label="💵 Tarif Moyen",
#         value=f"${kpi_data['avg_fare'][0]:.2f}"
#     )

# with col4:
#     st.metric(
#         label="📏 Distance Moyenne",
#         value=f"{kpi_data['avg_distance'][0]:.2f} mi"
#     )

# with col5:
#     st.metric(
#         label="⏱️ Durée Moyenne",
#         value=f"{kpi_data['avg_duration'][0]:.0f} min"
#     )

# st.markdown("<br>", unsafe_allow_html=True)

# # ============================================================
# # SECTION 2: ANALYSE TEMPORELLE (PAYSAGE)
# # ============================================================

# st.markdown('<h2 class="section-title">📅 Analyse Temporelle</h2>', unsafe_allow_html=True)

# col1, col2 = st.columns(2)

# with col1:
#     # Revenue par jour de la semaine
#     dow_query = f"""
#     SELECT 
#         d.day_name,
#         d.day_of_week,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY d.day_name, d.day_of_week
#     ORDER BY d.day_of_week
#     """
    
#     dow_data = run_query(dow_query)
    
#     fig_dow = px.bar(
#         dow_data,
#         x='day_name',
#         y='total_revenue',
#         title='Revenu par jour de la semaine',
#         labels={'day_name': 'Jour', 'total_revenue': 'Revenu ($)'},
#         color='total_revenue',
#         color_continuous_scale='Viridis'
#     )
#     fig_dow.update_layout(
#         paper_bgcolor='white',
#         plot_bgcolor='#f8f9fa',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     fig_dow.update_xaxes(
#         tickfont=dict(color="#475569"),
#         title_font=dict(color="#1e293b")
#     )
#     fig_dow.update_yaxes(
#         tickfont=dict(color="#475569"),
#         title_font=dict(color="#1e293b")
#     )
#     st.plotly_chart(fig_dow, use_container_width=True)

# with col2:
#     # Distribution par heure
#     hour_query = f"""
#     SELECT 
#         t.hour,
#         COUNT(*) as trip_count,
#         AVG(f.total_amount) as avg_fare
#     FROM fact_trips f
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY t.hour
#     ORDER BY t.hour
#     """
    
#     hour_data = run_query(hour_query)
    
#     fig_hour = px.line(
#         hour_data,
#         x='hour',
#         y='trip_count',
#         title='Nombre de courses par heure',
#         labels={'hour': 'Heure', 'trip_count': 'Nombre de courses'},
#         markers=True
#     )
#     fig_hour.update_traces(line_color='#667eea', marker=dict(size=8, color='#764ba2'))
#     fig_hour.update_layout(
#         paper_bgcolor='white',
#         plot_bgcolor='#f8f9fa',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     fig_hour.update_xaxes(
#         tickfont=dict(color="#475569"),
#         title_font=dict(color="#1e293b")
#     )
#     fig_hour.update_yaxes(
#         tickfont=dict(color="#475569"),
#         title_font=dict(color="#1e293b")
#     )

#     st.plotly_chart(fig_hour, use_container_width=True)

# # ============================================================
# # SECTION 3: ANALYSE GÉOGRAPHIQUE (PAYSAGE)
# # ============================================================

# st.markdown('<h2 class="section-title">🗺️ Analyse Géographique</h2>', unsafe_allow_html=True)

# col1, col2 = st.columns(2)

# with col1:
#     # Top zones de pickup
#     pickup_query = f"""
#     SELECT 
#         l.zone,
#         l.borough,
#         COUNT(*) as pickup_count
#     FROM fact_trips f
#     JOIN dim_location l ON f.pickup_location_key = l.location_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY l.zone, l.borough
#     ORDER BY pickup_count DESC
#     LIMIT 10
#     """
    
#     pickup_data = run_query(pickup_query)
    
#     fig_pickup = px.bar(
#         pickup_data,
#         y='zone',
#         x='pickup_count',
#         color='borough',
#         title='Top 10 zones de pickup',
#         labels={'zone': 'Zone', 'pickup_count': 'Courses'},
#         orientation='h',
#         color_discrete_sequence=px.colors.qualitative.Set2
#     )
#     fig_pickup.update_layout(
#         yaxis={'categoryorder':'total ascending'},
#         paper_bgcolor='white',
#         plot_bgcolor='#f8f9fa',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     st.plotly_chart(fig_pickup, use_container_width=True)

# with col2:
#     # Répartition par arrondissement
#     borough_query = f"""
#     SELECT 
#         l.borough,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_location l ON f.pickup_location_key = l.location_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#         AND l.borough IS NOT NULL
#     GROUP BY l.borough
#     ORDER BY trip_count DESC
#     """
    
#     borough_data = run_query(borough_query)
    
#     fig_borough = px.pie(
#         borough_data,
#         values='trip_count',
#         names='borough',
#         title='Répartition des courses par arrondissement',
#         hole=0.4,
#         color_discrete_sequence=px.colors.qualitative.Pastel
#     )
#     fig_borough.update_layout(
#         paper_bgcolor='white',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     st.plotly_chart(fig_borough, use_container_width=True)

# # ============================================================
# # SECTION 4: ANALYSE FINANCIÈRE (PAYSAGE)
# # ============================================================

# st.markdown('<h2 class="section-title">💳 Analyse Financière</h2>', unsafe_allow_html=True)

# col1, col2 = st.columns(2)

# with col1:
#     # Types de paiement
#     payment_query = f"""
#     SELECT 
#         p.payment_description,
#         COUNT(*) as trip_count,
#         SUM(f.total_amount) as total_revenue
#     FROM fact_trips f
#     JOIN dim_payment p ON f.payment_key = p.payment_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY p.payment_description
#     ORDER BY trip_count DESC
#     """
    
#     payment_data = run_query(payment_query)
    
#     fig_payment = px.bar(
#         payment_data,
#         x='payment_description',
#         y='total_revenue',
#         title='Revenu par type de paiement',
#         labels={'payment_description': 'Type de paiement', 'total_revenue': 'Revenu ($)'},
#         color='total_revenue',
#         color_continuous_scale='Teal'
#     )
#     fig_payment.update_layout(
#         paper_bgcolor='white',
#         plot_bgcolor='#f8f9fa',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     st.plotly_chart(fig_payment, use_container_width=True)

# with col2:
#     # Performance par vendor
#     vendor_query = f"""
#     SELECT 
#         v.vendor_name,
#         COUNT(*) as trip_count,
#         AVG(f.total_amount) as avg_fare
#     FROM fact_trips f
#     JOIN dim_vendor v ON f.vendor_key = v.vendor_key
#     JOIN dim_date d ON f.pickup_date_key = d.date_key
#     JOIN dim_time t ON f.pickup_time_key = t.time_key
#     WHERE d.date_value BETWEEN '{start_date}' AND '{end_date}'
#         AND t.hour BETWEEN {hour_range[0]} AND {hour_range[1]}
#     GROUP BY v.vendor_name
#     ORDER BY trip_count DESC
#     """
    
#     vendor_data = run_query(vendor_query)
    
#     fig_vendor = go.Figure(data=[
#         go.Bar(
#             name='Nombre de courses', 
#             x=vendor_data['vendor_name'], 
#             y=vendor_data['trip_count'], 
#             yaxis='y', 
#             offsetgroup=1,
#             marker_color='#667eea'
#         ),
#         go.Bar(
#             name='Tarif moyen', 
#             x=vendor_data['vendor_name'], 
#             y=vendor_data['avg_fare'], 
#             yaxis='y2', 
#             offsetgroup=2,
#             marker_color='#764ba2'
#         )
#     ])
#     fig_vendor.update_layout(
#         title='Performance par fournisseur',
#         yaxis=dict(title='Nombre de courses'),
#         yaxis2=dict(title='Tarif moyen ($)', overlaying='y', side='right'),
#         barmode='group',
#         paper_bgcolor='white',
#         plot_bgcolor='#f8f9fa',
#         title_font_size=16,
#         title_font_color='#1e293b',
#         font=dict(color='#475569')
#     )
#     st.plotly_chart(fig_vendor, use_container_width=True)

# # ============================================================
# # FOOTER
# # ============================================================

# st.markdown("""
# <div class="footer">
#     <p><strong>NYC Yellow Taxi Dashboard</strong> | CY Tech - Big Data Project 2026</p>
#     <p>Projet réalisé dans le cadre du cours Big Data</p>
# </div>
# """, unsafe_allow_html=True)





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
