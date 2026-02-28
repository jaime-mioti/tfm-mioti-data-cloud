import streamlit as st
from data_utils import format_descripcion_fisica, load_prediction_model
import pandas as pd
import json

# --- CONFIGURACIÓN Y CARGA ---
model_assets = load_prediction_model()
df = st.session_state.get('df', None)

# Inicializamos el estado si no existe
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = "buscador"

# Función Callback para cambiar de vista (esto soluciona el doble click)
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
    # Determinamos el texto del botón basándonos en el estado actual
    texto_boton = "📊 Tasa tu vivienda" if st.session_state.vista_actual == "buscador" else "🔍 Volver al buscador"
    
    # Usamos on_click para que el cambio sea inmediato y limpie estados previos
    st.button(texto_boton, on_click=cambiar_vista, use_container_width=True)

# --- LÓGICA DE RENDERIZADO DE VISTAS ---

if st.session_state.vista_actual == "tasador":
    # --- VISTA 1: TASADOR ---
    if model_assets is None:
        st.error("No se encontró el archivo del modelo para realizar tasaciones.")
    else:
        st.info("Algoritmo de valoración basado en el aprendizaje automático de precios actuales.")
        
        with st.form("tasador_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                m2 = st.number_input("Metros cuadrados", 10, 1000, 85)
                habs = st.slider("Habitaciones", 1, 6, 2)
            with c2:
                banos = st.slider("Baños", 1, 4, 1)
                barrio = st.selectbox("Barrio", model_assets["unique_values"]["barrios"])
            with c3:
                estado = st.selectbox("Estado de conservación", model_assets["unique_values"]["estados"])
                tipo = st.selectbox("Tipología", model_assets["unique_values"]["tipos"])
            
            enviar = st.form_submit_button("Calcular Tasación", type="primary")

        if enviar:
            input_data = pd.DataFrame([[m2, habs, banos, barrio, estado, tipo]], 
                                     columns=['tamaño_m2', 'n_habitaciones', 'n_baños', 'barrio', 'estado', 'tipo_detalle_clean'])
            
            pred = model_assets["model"].predict(input_data)[0]
            rmse = model_assets["rmse"]

            st.success(f"### Valor estimado: {int(pred):,} €".replace(",", "."))
            
            st.markdown(f"""
                <div style="background-color: #f0f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; color: #1e3a8a;">
                    Rango de mercado esperado: <b>{int(pred - rmse):,} €</b> - <b>{int(pred + rmse):,} €</b>
                </div>
            """, unsafe_allow_html=True)

            st.subheader("📋 Viviendas comparables en el barrio")
            if df is not None and not df.empty:
                # Asegúrate de usar n_habitaciones (corregido en el paso anterior)
                similares = df[(df['barrio'] == barrio) & (df['n_habitaciones'] == habs)].head(3)
                if not similares.empty:
                    cols_sim = st.columns(len(similares))
                    for i, (_, r) in enumerate(similares.iterrows()):
                        with cols_sim[i]:
                            st.image(r['foto'], use_container_width=True)
                            st.write(f"**{int(r['precio']):,} €**".replace(",", "."))
                            st.caption(f"{r['estado']} | {int(r['tamaño_m2'])}m²")
                else:
                    st.write("No hay viviendas exactas en el mapa actual para comparar.")
            else:
                st.warning("Selecciona distritos en el panel lateral para ver comparables aquí.")

else:
    # --- VISTA 2: BUSCADOR ---
    if df is None or df.empty:
        st.warning("Por favor, selecciona al menos un distrito en el menú lateral para ver las propiedades.")
    else:
        cols = st.columns(3)
        for index, (_, row) in enumerate(df.iterrows()):
            precio_puntos = f"{int(row['precio']):,}".replace(",", ".")
            descripcion_vivienda = format_descripcion_fisica(row)
            
            # Gestión de Parking
            parking_data = row.get('parking')
            if not parking_data or pd.isna(parking_data):
                parking_v = "No dispone"
            else:
                if isinstance(parking_data, str):
                    try: parking_data = json.loads(parking_data)
                    except: parking_data = {}
                
                if parking_data.get('hasParkingSpace'):
                    if parking_data.get('isParkingSpaceIncludedInPrice'):
                        parking_v = "Incluido"
                    else:
                        p_p = parking_data.get('parkingSpacePrice', 0)
                        parking_v = f"Opcional ({int(p_p):,} €)".replace(",", ".") if p_p > 0 else "Disponible"
                else:
                    parking_v = "No dispone"

            with cols[index % 3]:
                st.markdown(f"""
                    <div class="property-card-clean">
                        <img src="{row['foto']}" class="property-img-clean">
                        <div class="price-text">{precio_puntos} €</div>
                        <div style="margin-bottom:2px;"><b>{row['barrio']}</b></div>
                        <div style="font-size:0.9em; color:#666; margin-bottom:8px;">{descripcion_vivienda}</div>
                        <span class="metric-badge">📏 {int(row['tamaño_m2'])} m²</span> 
                        <span class="metric-badge">🛏️ {int(row['n_habitaciones'])}</span> 
                        <span class="metric-badge">🚿 {int(row['n_baños'])}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Ver detalles"):
                    st.write(f"**Dirección:** {row['direccion']}")
                    st.write(f"**Precio/m²:** {int(row['precio_m2']):,} €/m²".replace(",", "."))
                    st.write(f"**Parking:** {parking_v}")
                    st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
                st.write("")