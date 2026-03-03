"""
Script que incluye las funcionalidades de la pantalla del buscador detallado, como queremos que aparezca representado en la interfaz
"""
import streamlit as st
from data_utils import format_descripcion_fisica
import pandas as pd
import json

st.header("🏠 Buscador Detallado")

# Obtenemos los datos filtrados desde el sidebar (que está en app.py)
df_filtrado = st.session_state.get('df', None)

if df_filtrado is None or df_filtrado.empty:
    st.warning("Por favor, selecciona al menos un distrito en el menú lateral para ver las propiedades.")
else:
    st.write(f"Mostrando {len(df_filtrado)} propiedades según tus filtros.")
    cols = st.columns(3)
    for index, (_, row) in enumerate(df_filtrado.iterrows()):
        precio_puntos = f"{int(row['precio']):,}".replace(",", ".")
        desc = format_descripcion_fisica(row)
        
        # Lógica de Parking
        parking_data = row.get('parking')
        parking_v = "No dispone"
        if parking_data and not pd.isna(parking_data):
            if isinstance(parking_data, str):
                try: parking_data = json.loads(parking_data)
                except: parking_data = {}
            if parking_data.get('hasParkingSpace'):
                parking_v = "Incluido" if parking_data.get('isParkingSpaceIncludedInPrice') else "Disponible"

        with cols[index % 3]:
            st.markdown(f"""
                <div class="property-card-clean">
                    <img src="{row['foto']}" class="property-img-clean">
                    <div class="price-text">{precio_puntos} €</div>
                    <div style="margin-bottom:2px;"><b>{row['barrio']}</b></div>
                    <div style="font-size:0.9em; color:#666; margin-bottom:8px;">{desc}</div>
                    <span class="metric-badge">📏 {int(row['tamaño_m2'])} m²</span> 
                    <span class="metric-badge">🛏️ {int(row['n_habitaciones'])}</span> 
                    <span class="metric-badge">🚿 {int(row['n_baños'])}</span>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver detalles"):
                st.write(f"**Dirección:** {row['direccion']}")
                st.write(f"**Estado:** {row.get('estado', 'N/A')}")
                st.write(f"**Precio/m²:** {int(row['precio_m2']):,} €/m²".replace(",", "."))
                st.write(f"**Parking:** {parking_v}")
                st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
            st.write("")