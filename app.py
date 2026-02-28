import streamlit as st
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import pydeck as pdk
import os
import time
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="TFM - Madrid Real Estate Explorer", layout="wide")

# CSS personalizado
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

#Funcion para conectarse a la bd, con un retry de 5
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
    
    # La query une ambas tablas por ID de forma eficiente
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
    
    # Post-procesamiento en Pandas
    df['foto'] = df['foto'].fillna("https://via.placeholder.com/150?text=Sin+Foto")
    df['distrito'] = df['distrito'].str.strip()
    df['tipo'] = df['tipo'].map({'flat': 'Piso', 'penthouse': 'Ático', 'chalet': 'Chalet', 'duplex': 'Dúplex', 'studio': 'Estudio', 'countryHouse': 'Casa Rústica'})        
    return df


@st.cache_data
def load_geo_data():
    engine = get_engine()
    # Usamos ST_AsGeoJSON para obtener la geometría lista para PyDeck
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

try:
    df_raw = load_data()
    df_geo_raw = load_geo_data()
    
    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Conteo para el multiselect
    conteo_distritos = df_raw['distrito'].value_counts()
    opciones_distritos = [f"{d} ({conteo_distritos[d]})" for d in sorted(df_raw['distrito'].unique())]
    
    sel_dist_formateados = st.sidebar.multiselect(
        "Filtrar por distrito:", 
        options=opciones_distritos, 
        default=opciones_distritos,
        placeholder="Selecciona uno o varios distritos..."
    )
    
    # Limpiar selección para filtrar el dataframe
    distritos_seleccionados = [d.split(" (")[0] for d in sel_dist_formateados]
    
    opciones_min = [0, 50000, 100000, 150000, 200000, 300000, 500000]
    opciones_max = [100000, 200000, 300000, 500000, 1000000, 3000000, 5000000, "Sin límite"]

    st.sidebar.write("### Precio (€)")

    # Usamos columnas para que queden uno al lado del otro
    col1, col2 = st.sidebar.columns(2)

    min_seleccionado = col1.selectbox(
        "Precio Mínimo", 
        options=opciones_min, 
        format_func=lambda x: f"{x:,} €".replace(",", ".") if x != 0 else "Mín"
    )

    max_seleccionado = col2.selectbox(
        "Precio Máximo", 
        options=opciones_max,
        index=len(opciones_max)-1,
        format_func=lambda x: f"{x:,} €".replace(",", ".") if isinstance(x, int) else x
    )

    # 2. Lógica para la Query SQL
    precio_max_final = 999_999_999 if max_seleccionado == "Sin límite" else max_seleccionado
    
    
    if max_seleccionado == "Sin límite":
        precio_max_val = float('inf') 
    else:
        precio_max_val = float(max_seleccionado)

    precio_min_val = float(min_seleccionado)
    
    col_f1, col_f2 = st.sidebar.columns(2)
    min_hab = col_f1.selectbox("Número mínimo de habitaciones", [0, 1, 2, 3, 4], index=0)
    min_ban = col_f2.selectbox("Número mínimo de baños", [0, 1, 2, 3], index=0)

    # Aplicar Filtros
    df = df_raw[
        (df_raw['distrito'].isin(distritos_seleccionados)) & 
        (df_raw['precio'] >= precio_min_val) &          
        (df_raw['precio'] <= precio_max_val) &
        (df_raw['habitaciones'] >= min_hab) &
        (df_raw['baños'] >= min_ban)
    ].dropna(subset=['lat', 'lon'])
    
    df, pmin, pmax = apply_color_logic(df)

    # --- PESTAÑAS ---
    tab_mapa, tab_buscador = st.tabs(["📍 Mapa de Mercado", "🏠 Buscador Detallado"])

    with tab_mapa:
        modo_mapa = st.radio("Visualización:", ["Puntos individuales", "Coropletas (Precio medio por distrito)"], horizontal=True)
        
        if modo_mapa == "Puntos individuales":
            st.write(f"Viendo **{len(df)}** propiedades.")
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
        
        else:
            # Lógica de Coropletas
            stats_distrito = df.groupby('distrito')['precio'].mean().reset_index()
            geo_merge = df_geo_raw.merge(stats_distrito, on='distrito')
            
            # Preparar GeoJSON para PyDeck
            features = []
            max_p = geo_merge['precio'].max() if not geo_merge.empty else 1
            for _, row in geo_merge.iterrows():
                norm = row['precio'] / max_p
                color = [int(255 * norm), int(255 * (1 - norm)), 100, 160]
                
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(row['geom']),
                    "properties": {
                        "distrito": row['distrito'],
                        "precio_medio": f"{int(row['precio']):,} €",
                        "fill_color": color
                    }
                })
            
            geojson_data = {"type": "FeatureCollection", "features": features}
            
            layer_geo = pdk.Layer(
                "GeoJsonLayer",
                geojson_data,
                pickable=True,
                filled=True,
                extruded=False,
                get_fill_color="properties.fill_color",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=1,
            )
            
            st.pydeck_chart(pdk.Deck(
                layers=[layer_geo],
                initial_view_state=pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=10.5),
                tooltip={"html": "<b>Distrito:</b> {distrito}<br><b>Precio Medio:</b> {precio_medio}"}
            ))

    with tab_buscador:
        if df.empty:
            st.warning("elige al menos un distrito para ver resultados.")
        else:
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
                    
                    with st.expander("Ver detalles técnicos"):
                        st.write(f"**Tipo:** {row['tipo'].capitalize() if row['tipo'] else 'N/A'}")
                        st.write(f"**Distrito:** {row['distrito']}")
                        st.write(f"**Precio/m²:** {int(row['precio_m2'])} €/m²")
                        st.write(f"**Planta:** {row['planta'] if row['planta'] else 'N/A'}")
                        st.write(f"**Ascensor:** {'Sí' if row['ascensor'] else 'No'}")
                        st.write(f"**Exterior:** {'Sí' if row['exterior'] else 'No'}")
                        st.write(f"**ID Interno:** {row['id']}")
                    
                    st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
                    st.write("") 

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Asegúrate de que la tabla 'barrios_geo' existe y tiene PostGIS habilitado.")