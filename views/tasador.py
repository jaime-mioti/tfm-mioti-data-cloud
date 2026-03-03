import streamlit as st
import pandas as pd
import numpy as np
from data_utils import format_descripcion_fisica, load_prediction_model, load_data

# --- CONFIGURACIÓN Y CARGA ---
# Asegúrate de que load_prediction_model() devuelva el nuevo .pkl con 9 variables
model_assets = load_prediction_model()

st.set_page_config(page_title="Tasador Inmobiliario", layout="wide")
st.header("📊 Tasador de Vivienda")

if model_assets is None:
    st.error("No se encontró el archivo del modelo 'modelo_tasacion_inmobiliario.pkl'.")
else:
    st.info("Algoritmo para estimar lo que vale una vivienda basado en sus características.")
    
    with st.form("tasador_form"):
        # Bloque Principal
        c1, c2, c3 = st.columns(3)
        with c1:
            m2 = st.number_input("Superficie (m²)", 10, 1000, 90)
            barrio_sel = st.selectbox("Barrio", model_assets["unique_values"]["barrios"])
        with c2:
            habs = st.number_input("Habitaciones", 1, 6, 2)
            estado = st.selectbox("Estado de conservación", model_assets["unique_values"]["estados"])
        with c3:
            banos = st.number_input("Baños", 1, 4, 1)
            tipo = st.selectbox("Tipología", model_assets["unique_values"]["tipos"])

        st.divider()
        
        # Bloque de Extras (Nuevas variables)
        st.write("**Equipamiento Adicional**")
        e1, e2, e3 = st.columns(3)
        with e1:
            exterior = st.checkbox("Es exterior", value=True)
        with e2:
            ascensor = st.checkbox("Tiene ascensor", value=True)
        with e3:
            parking = st.checkbox("Tiene plaza de parking", value=False)
        
        enviar = st.form_submit_button("Calcular Tasación", type="primary")

    if enviar:
       
        input_data = pd.DataFrame([[
            m2, 
            habs, 
            banos, 
            barrio_sel, 
            estado, 
            tipo,
            int(exterior), 
            int(ascensor), 
            int(parking)
        ]], columns=model_assets["features"])

        # Predicción
        pred_log = model_assets["model"].predict(input_data)[0]
        rmse_log = model_assets["rmse_log"]
        
        pred = np.exp(pred_log)
        # Para los intervalos de confianza
        lower = np.exp(pred_log - 1.96 * rmse_log)
        upper = np.exp(pred_log + 1.96 * rmse_log)
        
        # Visualización de Resultados
        st.success(f"### Valor estimado: {int(pred):,} €".replace(",", "."))
        
        res1, res2 = st.columns(2)
        res1.metric("Precio m²", f"{int(pred/m2):,} €/m²".replace(",", "."))
        res2.markdown(f"""
            <div style="background-color: #f0f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32;">
                <b>Valor estimado entre:</b><br>
                {int(lower):,} € - {int(upper):,} €
            </div>
        """, unsafe_allow_html=True)

        # 3. Lógica de Comparables
        st.divider()
        st.subheader("🏠 Viviendas similares en la zona")
        df_full = load_data()
            
        similares = df_full[(df_full['barrio'] == barrio_sel) & 
                            (df_full['n_habitaciones'] == habs)].head(3)
        
        if not similares.empty:
            cols_sim = st.columns(3)
            for i, (_, row) in enumerate(similares.iterrows()):
                with cols_sim[i]:
                    precio_puntos = f"{int(row['precio']):,}".replace(",", ".")
                    st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:10px; background: white; min-height: 320px;">
                            <img src="{row.get('foto', '')}" style="width:100%; height:140px; object-fit:cover; border-radius:5px;">
                            <div style="font-size:1.2em; font-weight:bold; margin-top:8px;">{precio_puntos} €</div>
                            <b>{row['barrio']}</b><br>
                            <small style="color:#666;">{format_descripcion_fisica(row)}</small>
                            <div style="margin-top:10px; font-size:0.8em;">📏 {int(row['tamaño_m2'])}m² | 🛏️ {int(row['n_habitaciones'])} | 🚿 {int(row['n_baños'])}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No hay comparables directos en este barrio.")