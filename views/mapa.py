import streamlit as st
import pydeck as pdk
import json

df = st.session_state.get('df', None)
df_geo_raw = st.session_state.get('df_geo_raw', None)

st.header("📍 Mapa de Mercado")

if df is not None:
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
        stats_distrito = df.groupby('distrito')['precio'].mean().reset_index()
        geo_merge = df_geo_raw.merge(stats_distrito, on='distrito')
        
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
            get_fill_color="properties.fill_color",
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
        )
        st.pydeck_chart(pdk.Deck(
            layers=[layer_geo],
            initial_view_state=pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=10.5),
            tooltip={"html": "<b>Distrito:</b> {distrito}<br><b>Precio Medio:</b> {precio_medio}"}
        ))