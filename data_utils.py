import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import time

def get_engine():
    url = f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
    for i in range(5):
        try:
            engine = create_engine(url)
            with engine.connect() as conn: 
                return engine
        except Exception:
            if i < 4: time.sleep(2)
    return create_engine(url)

@st.cache_data
def load_data():
    engine = get_engine()
    query = """
    SELECT 
        i.id, 
        i.precio,
        i.barrio,
        i.distrito,
        i.tamaño_m2,
        ST_X(i.geom) as lon, 
        ST_Y(i.geom) as lat,
        i.n_habitaciones as habitaciones,
        i.n_baños as baños,
        (r.raw_data->>'thumbnail') as foto,
        i.tipo_propiedad as tipo,
        i.planta,
        i.tiene_ascensor as ascensor,
        i.es_exterior as exterior,
        i.precio_m2,
        ir.url
    FROM public.inmuebles i
    LEFT JOIN public.raw_data r ON i.id = r.id
    LEFT JOIN public.idealista_reference ir ON i.id = ir.id;
    """
    df = pd.read_sql(query, engine)
    df['foto'] = df['foto'].fillna("https://via.placeholder.com/150?text=Sin+Foto")
    df['distrito'] = df['distrito'].str.strip()
    df['tipo'] = df['tipo'].map({
        'flat': 'Piso', 'penthouse': 'Ático', 'chalet': 'Chalet', 
        'duplex': 'Dúplex', 'studio': 'Estudio', 'countryHouse': 'Casa Rústica'
    })        
    return df

@st.cache_data
def load_geo_data():
    engine = get_engine()
    query = "SELECT distrito, ST_AsGeoJSON(geometry) as geom FROM barrios_geo;"
    df_geo = pd.read_sql(query, engine)
    df_geo['distrito'] = df_geo['distrito'].str.strip()
    return df_geo

def apply_color_logic(df):
    if df.empty: return df, 0, 0
    pmin, pmax = df['precio'].quantile(0.05), df['precio'].quantile(0.95)
    def color_calc(val):
        norm = max(0, min(1, (val - pmin) / (pmax - pmin) if pmax > pmin else 0.5))
        return [int(norm * 255), int((1 - norm) * 255), 0, 180]
    df['fill_color'] = df['precio'].apply(color_calc)
    return df, pmin, pmax