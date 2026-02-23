import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import pydeck as pdk
import os
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="TFM - Madrid Real Estate Explorer", layout="wide")

# CSS personalizado para diseño limpio y minimalista
st.markdown("""
    <style>
    .property-card-clean {
        border-bottom: 1px solid #eee;
        padding-bottom: 15px;
        margin-bottom: 15px;
    }
    .property-img-clean {
        width: 100%;
        height: 220px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    .price-text {
        color: #1e1e1e;
        font-size: 22px;
        font-weight: bold;
    }
    .metric-badge {
        background-color: #f1f3f5;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85em;
        color: #495057;
        margin-right: 5px;
        display: inline-block;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_engine():
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "pass1234")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    db = os.getenv("DB_NAME", "tfm")
    url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    for i in range(5):
        try:
            engine = create_engine(url)
            with engine.connect() as conn: return engine
        except Exception:
            if i < 4: time.sleep(2)
    return create_engine(url)

@st.cache_data
def load_data():
    engine = get_engine()
    query = """
    SELECT 
        id, 
        (raw_data::jsonb->>'price')::numeric as precio,
        (raw_data::jsonb->>'neighborhood') as barrio,
        (raw_data::jsonb->>'district') as distrito,
        (raw_data::jsonb->>'size')::numeric as tamaño_m2,
        (raw_data::jsonb->>'longitude')::numeric as lon,
        (raw_data::jsonb->>'latitude')::numeric as lat,
        (raw_data::jsonb->>'rooms')::int as habitaciones,
        (raw_data::jsonb->>'bathrooms')::int as baños,
        (raw_data::jsonb->>'thumbnail') as foto,
        (raw_data::jsonb->>'url') as url,
        (raw_data::jsonb->>'propertyType') as tipo,
        (raw_data::jsonb->>'floor') as planta,
        (raw_data::jsonb->>'hasLift')::boolean as ascensor,
        (raw_data::jsonb->>'exterior')::boolean as exterior
    FROM raw_data;
    """
    df = pd.read_sql(query, engine)
    df['precio_m2'] = df['precio'] / df['tamaño_m2']
    df['foto'] = df['foto'].fillna("https://via.placeholder.com/150?text=Sin+Foto")
    return df

def apply_color_logic(df):
    if df.empty: return df, 0, 0
    pmin, pmax = df['precio'].quantile(0.05), df['precio'].quantile(0.95)
    def color_calc(val):
        norm = max(0, min(1, (val - pmin) / (pmax - pmin) if pmax > pmin else 0.5))
        return [int(norm * 255), int((1 - norm) * 255), 0, 180]
    df['fill_color'] = df['precio'].apply(color_calc)
    return df, pmin, pmax

try:
    df_raw = load_data()
    
    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Selección de Zonas (TODAS por defecto)
    todos_distritos = sorted(df_raw['distrito'].unique().tolist())
    sel_dist = st.sidebar.multiselect("Zonas seleccionadas:", todos_distritos, default=todos_distritos)
    
    precio_max = st.sidebar.slider("Presupuesto máximo (€)", 50000, 3000000, 2000000, step=50000)
    
    col_f1, col_f2 = st.sidebar.columns(2)
    min_hab = col_f1.selectbox("Hab. mín.", [0, 1, 2, 3, 4], index=0)
    min_ban = col_f2.selectbox("Baños mín.", [0, 1, 2, 3], index=0)

    # Aplicar Filtros
    df = df_raw[
        (df_raw['distrito'].isin(sel_dist)) & 
        (df_raw['precio'] <= precio_max) &
        (df_raw['habitaciones'] >= min_hab) &
        (df_raw['baños'] >= min_ban)
    ].dropna(subset=['lat', 'lon'])
    
    df, pmin, pmax = apply_color_logic(df)

    # --- PESTAÑAS ---
    tab_mapa, tab_buscador = st.tabs(["📍 Mapa de Mercado", "🏠 Buscador Detallado"])

    with tab_mapa:
        st.write(f"Viendo **{len(df)}** propiedades en Madrid.")
        layer = pdk.Layer(
            "ScatterplotLayer",
            df,
            get_position='[lon, lat]',
            get_fill_color='fill_color',
            get_radius=40,
            radius_min_pixels=4,
            pickable=True,
        )
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=11),
            tooltip={"html": "<b>{precio} €</b><br>{barrio}"}
        ))

    with tab_buscador:
        if df.empty:
            st.warning("Ajusta los filtros para ver resultados.")
        else:
            # Grid de 3 columnas
            cols = st.columns(3)
            for index, (_, row) in enumerate(df.iterrows()):
                with cols[index % 3]:
                    st.markdown(f"""
                        <div class="property-card-clean">
                            <img src="{row['foto']}" class="property-img-clean">
                            <div class="price-text">{int(row['precio']):,} €</div>
                            <div style="margin-bottom:8px;"><b>{row['barrio']}</b></div>
                            <span class="metric-badge">📏 {int(row['tamaño_m2'])} m²</span> 
                            <span class="metric-badge">🛏️ {int(row['habitaciones'])}</span> 
                            <span class="metric-badge">🚿 {int(row['baños'])}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # DESPLEGABLE CON INFORMACIÓN DETALLADA
                    with st.expander("Ver detalles técnicos"):
                        st.write(f"**Tipo:** {row['tipo'].capitalize() if row['tipo'] else 'N/A'}")
                        st.write(f"**Distrito:** {row['distrito']}")
                        st.write(f"**Precio/m²:** {int(row['precio_m2'])} €/m²")
                        st.write(f"**Planta:** {row['planta'] if row['planta'] else 'N/A'}")
                        st.write(f"**Ascensor:** {'Sí' if row['ascensor'] else 'No'}")
                        st.write(f"**Exterior:** {'Sí' if row['exterior'] else 'No'}")
                        st.write(f"**ID Interno:** {row['id']}")
                    
                    st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
                    st.write("") # Espaciador entre filas

except Exception as e:
    st.error(f"Error: {e}")