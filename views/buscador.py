import streamlit as st
from data_utils import format_descripcion_fisica, load_prediction_model, load_data
import pandas as pd
import numpy as np
import json

# --- CONFIGURACIÓN Y CARGA ---
model_assets = load_prediction_model()

# Inicializamos el estado de la vista si no existe
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = "buscador"

# Función Callback para cambiar de vista inmediatamente
def cambiar_vista():
    if st.session_state.vista_actual == "buscador":
        st.session_state.vista_actual = "tasador"
    else:
        st.session_state.vista_actual = "buscador"

# --- CABECERA ---
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.header("🏠 Buscador Detallado")
with col_t2:
    st.write("")
    texto_boton = "📊 Tasa tu vivienda" if st.session_state.vista_actual == "buscador" else "🔍 Volver al buscador"
    st.button(texto_boton, on_click=cambiar_vista, use_container_width=True)

# --- LÓGICA DE RENDERIZADO ---

if st.session_state.vista_actual == "tasador":
    # --- VISTA 1: TASADOR ---
    if model_assets is None:
        st.error("No se encontró el archivo del modelo.")
    else:
        st.info("Algoritmo de valoración basado en el aprendizaje automático de precios actuales.")
        
        with st.form("tasador_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                m2 = st.number_input("Metros cuadrados", 10, 1000, 85)
                habs = st.slider("Habitaciones", 1, 6, 2)
            with c2:
                banos = st.slider("Baños", 1, 4, 1)
                barrio_sel = st.selectbox("Barrio", model_assets["unique_values"]["barrios"])
            with c3:
                estado = st.selectbox("Estado de conservación", model_assets["unique_values"]["estados"])
                tipo = st.selectbox("Tipología", model_assets["unique_values"]["tipos"])
            
            enviar = st.form_submit_button("Calcular Tasación", type="primary")

        if enviar:
            # 1. Predicción del Modelo
            input_data = pd.DataFrame([[m2, habs, banos, barrio_sel, estado, tipo]], 
                                     columns=['tamaño_m2', 'n_habitaciones', 'n_baños', 'barrio', 'estado', 'tipo_propiedad'])
            pred_log = model_assets["model"].predict(input_data)[0]
            rmse_log = model_assets["rmse_log"]
            # Volvemos a escala real
            pred = np.exp(pred_log)
            lower = np.exp(pred_log - 1.96 * rmse_log)
            upper = np.exp(pred_log + 1.96 * rmse_log)
            st.success(f"### Valor estimado: {int(pred):,} €".replace(",", "."))
            st.markdown(f"""
                <div style="background-color: #f0f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; color: #1e3a8a; margin-bottom: 25px;">
                    Rango de mercado esperado: <b>{int(lower):,} €</b> - <b>{int(upper):,} €</b>
                </div>
            """, unsafe_allow_html=True)

            # 2. Lógica de Comparables en el mismo Distrito (sin depender de filtros laterales)
            st.subheader(f"📋 Viviendas similares en el distrito")
            
            # Cargamos el DF completo para buscar el distrito del barrio seleccionado
            df_full = load_data()
            
            # Identificamos a qué distrito pertenece el barrio seleccionado
            info_barrio = df_full[df_full['barrio'] == barrio_sel].head(1)
            
            if not info_barrio.empty:
                distrito_sel = info_barrio['distrito'].values[0]
                # Filtramos por distrito y número de habitaciones
                similares = df_full[(df_full['distrito'] == distrito_sel) & 
                                    (df_full['n_habitaciones'] == habs)].head(3)
                
                if not similares.empty:
                    cols_sim = st.columns(3)
                    for i, (_, row) in enumerate(similares.iterrows()):
                        with cols_sim[i]:
                            # --- DISEÑO EXACTO DEL BUSCADOR ---
                            precio_puntos = f"{int(row['precio']):,}".replace(",", ".")
                            desc = format_descripcion_fisica(row)
                            
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
                                st.write(f"**Precio/m²:** {int(row['precio_m2']):,} €/m²".replace(",", "."))
                                st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
                else:
                    st.info("No se encontraron viviendas comparables en este distrito con esas habitaciones.")
            else:
                st.warning("No se pudo determinar el distrito para este barrio en la base de datos.")

else:
    # --- VISTA 2: BUSCADOR (Usa el DF filtrado por el menú lateral) ---
    df_filtrado = st.session_state.get('df', None)
    
    if df_filtrado is None or df_filtrado.empty:
        st.warning("Por favor, selecciona al menos un distrito en el menú lateral para ver las propiedades.")
    else:
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