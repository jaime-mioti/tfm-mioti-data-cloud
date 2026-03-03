import streamlit as st
import pydeck as pdk
import json
import pandas as pd
import unicodedata

def limpiar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = "".join([c for c in texto if unicodedata.category(c) != 'Mn'])
    return texto.strip().upper()

# 1. Recuperar datos y filtros
df = st.session_state.get('df', None)
df_geo_raw = st.session_state.get('df_geo_raw', None)

# Necesitamos saber qué distritos están seleccionados para resaltar sus barrios
# Nota: Asegúrate de que en tu app principal guardes 'distritos_seleccionados' en session_state
distritos_activos = st.session_state.get('distritos_seleccionados', [])

st.header("📍 Análisis del Mercado por Barrio")

if df is not None and df_geo_raw is not None:
    df['barrio_clean'] = df['barrio'].apply(limpiar_texto)
    df_geo_raw['barrio_clean'] = df_geo_raw['barrio'].apply(limpiar_texto)

    stats_barrio = df.groupby('barrio_clean').agg({
        'precio_m2': 'mean',
        'id': 'count'
    }).reset_index()
    stats_barrio.columns = ['barrio_clean', 'm2_barrio', 'anuncios_barrio']

    geo_merge = df_geo_raw.merge(stats_barrio, on='barrio_clean', how='left')

    features = []
    max_m2 = stats_barrio['m2_barrio'].quantile(0.95) if not stats_barrio.empty else 1
    
    for _, row in geo_merge.iterrows():
        # --- LÓGICA DE COLOR DE RELLENO ---
        if pd.isna(row['m2_barrio']):
            fill_color = [240, 240, 240, 150]
            m2_txt = "Sin anuncios"
            anuncios = 0
        else:
            norm = min(row['m2_barrio'] / max_m2, 1.0)
            fill_color = [int(255 * (1 - norm)), int(255 * (1 - norm * 0.5)), 255, 200]
            m2_txt = f"{int(row['m2_barrio']):,} €/m²"
            anuncios = int(row['anuncios_barrio'])

        # --- 2. LÓGICA DE COLOR DE BORDE (AZUL SI ESTÁ SELECCIONADO) ---
        # Si el distrito de este barrio está en la lista de seleccionados, borde azul brillante
        if row['distrito'] in distritos_activos:
            line_color = [0, 0,0, 255] # Azul vibrante
            line_width = 5
        else:
            line_color = [60, 60, 60, 100]  # Gris discreto
            line_width = 1

        features.append({
            "type": "Feature",
            "geometry": json.loads(row['geom']) if isinstance(row['geom'], str) else row['geom'],
            "properties": {
                "distrito": row['distrito'],
                "barrio": row['barrio'],
                "m2_txt": m2_txt,
                "anuncios": anuncios,
                "fill_color": fill_color,
                "line_color": line_color,  # Guardamos el color del borde
                "line_width": line_width,
                "poblacion_total": int(row['num_personas']) if pd.notna(row['num_personas']) else "Sin datos",
                "hombres": int(row['num_personas_hombres']) if pd.notna(row['num_personas_hombres']) else 0,
                "mujeres": int(row['num_personas_mujeres']) if pd.notna(row['num_personas_mujeres']) else 0
            }
        })

    geojson_data = {"type": "FeatureCollection", "features": features}

    # --- 3. CONFIGURACIÓN DEL MAPA ---
    st.pydeck_chart(pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=40.4168, 
            longitude=-3.7038, 
            zoom=11.2, 
            pitch=0 
        ),
        layers=[
            pdk.Layer(
                "GeoJsonLayer",
                geojson_data,
                pickable=True,
                filled=True,
                stroked=True,
                get_fill_color="properties.fill_color",
                # Usamos las propiedades dinámicas definidas arriba
                get_line_color="properties.line_color",
                get_line_width="properties.line_width",
                line_width_min_pixels=1, 
            )
        ],
        tooltip={
            "html": """
            <div style="font-family: sans-serif; padding: 8px; background: white; color: black; border: 1px solid #ccc;">
                <b style="font-size: 14px;">Barrio: {barrio}</b><br/>
                <small>Distrito: {distrito}</small><br/>
                <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;"/>
                <b>Precio m²:</b> {m2_txt}<br/>
                <b>Anuncios:</b> {anuncios}<br/>
                <b>Población Barrio:</b> {poblacion_total}<br/>
                <b>Hombres:</b> {hombres}<br/>
                <b>Mujeres:</b> {mujeres}<br/>
            </div>
            """
        }
    ))