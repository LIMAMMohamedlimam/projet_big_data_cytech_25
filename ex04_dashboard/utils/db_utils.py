import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

@st.cache_resource
def get_connection():
    """Crée et cache la connexion PostgreSQL"""
    db_config = st.secrets["postgres"]
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    return create_engine(connection_string)

@st.cache_data(ttl=300)  # Caching des données pendant 5 minutes
def run_query(query):
    """Exécute une requête SQL et retourne un DataFrame"""
    engine = get_connection()
    return pd.read_sql(query, engine)
