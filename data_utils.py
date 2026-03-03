import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
import time
import joblib
from pathlib import Path

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
        i.n_habitaciones,
        i.n_baños,
        (r.raw_data->>'thumbnail') as foto,
        i.tipo_propiedad as tipo,
        i.planta,
        i.tiene_ascensor as ascensor,
        i.es_exterior as exterior,
        i.precio_m2,
        i.direccion,
        i.estado,
        i.parking,
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
    df['estado'] = df['estado'].map({'good': 'En buen estado', 'renew': 'Necesita refoma', 'newdevelopment': 'Obra nueva'})
          
    return df

@st.cache_data
def load_geo_data():
    engine = get_engine()
    query = """SELECT bg.distrito, bg.barrio, pb.num_personas, pb.num_personas_hombres, pb.num_personas_mujeres, ST_AsGeoJSON(geometry) as geom FROM barrios_geo bg
            lEFT JOIN poblacion_barrios pb ON bg.barrio = pb.barrio;"""
    df_geo = pd.read_sql(query, engine)
    df_geo['distrito'] = df_geo['distrito'].str.strip()
    return df_geo

# Obtener la ruta de la carpeta donde está este archivo (la raíz)
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "modelo_tasacion_inmobiliario.pkl"

@st.cache_resource # Usamos cache_resource porque es un objeto pesado
def load_prediction_model():
    if not MODEL_PATH.exists():
        st.error(f"No se encontró el modelo en: {MODEL_PATH}")
        return None
    return joblib.load(MODEL_PATH)

def apply_color_logic(df):
    if df.empty: return df, 0, 0
    pmin, pmax = df['precio'].quantile(0.05), df['precio'].quantile(0.95)
    def color_calc(val):
        norm = max(0, min(1, (val - pmin) / (pmax - pmin) if pmax > pmin else 0.5))
        return [int(norm * 255), int((1 - norm) * 255), 0, 180]
    df['fill_color'] = df['precio'].apply(color_calc)
    return df, pmin, pmax

def format_descripcion_fisica(row):
    # 1. Gestionar tipos que no muestran planta
    tipos_sin_planta = ['Chalet', 'Casa Rústica']
    if row['tipo'] in tipos_sin_planta:
        detalles = []
    else:
        # 2. Gestionar la planta (Nulos o Números)
        if pd.isna(row['planta']) or row['planta'] == 0:
            p_str = "Bajo"
        else:
            # Añadimos el símbolo ª (femenino para Planta)
            p_str = f"Planta {int(row['planta'])}ª"
        detalles = [p_str]

    # 3. Exterior / Interior
    if not pd.isna(row['exterior']):
        detalles.append("exterior" if row['exterior'] else "interior")

    # 4. Ascensor
    asc_str = "con ascensor" if row['ascensor'] else "sin ascensor"
    
    # Unimos todo: "Planta 3ª exterior" + " con ascensor"
    frase_principal = " ".join(detalles)
    return f"{frase_principal} {asc_str}".strip().capitalize()