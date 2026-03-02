import os
import hmac
import streamlit as st
from data_utils import load_data, load_geo_data, apply_color_logic

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="TFM - Madrid Real Estate Explorer", layout="wide")

def require_login() -> None:
    """Bloquea la app hasta que el usuario se autentique.

    Se apoya en st.session_state para recordar el login durante la sesión.
    """

    # 1) Si ya hay una sesión autenticada, no pedimos credenciales otra vez.
    if st.session_state.get("auth_ok", False):
        return

    # 2) Leemos las credenciales "válidas" desde variables de entorno.
    #    (Mejor práctica: no hardcodear passwords en el código.)
    valid_user = os.getenv("APP_USER", "")
    valid_pass = os.getenv("APP_PASS", "")

    # Si no están configuradas, no tiene sentido pedir login (nadie podrá entrar).
    if not valid_user or not valid_pass:
        st.error("Faltan APP_USER / APP_PASS en variables de entorno (docker-compose/.env).")
        st.stop()

    # 3) UI del login.
    st.title("🔐 Bienvenido al TFM de Madrid Real Estate Explorer")

    # Usamos un form para que la validación ocurra solo al pulsar el botón.
    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

    # 4) Validación solo cuando el usuario pulsa "Entrar".
    if submitted:
        # Comparación segura (evita filtraciones por timing; mejor que ==)
        user_ok = hmac.compare_digest(user, valid_user)
        pass_ok = hmac.compare_digest(pwd, valid_pass)

        if user_ok and pass_ok:
            # Guardamos el estado de autenticación para el resto de la sesión.
            st.session_state["auth_ok"] = True
            # Forzamos rerun para que la app continúe (ya autenticada).
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    # 5) Cortamos la ejecución aquí si no hay login.
    #    Importante: evita que se carguen datos, se conecte a BD, etc.
    st.stop()


# Ejecutamos el guard al principio (antes de cargar datos).
require_login()


st.markdown("""
    <style>
    .property-card-clean { border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px; }
    .property-img-clean { width: 100%; height: 220px; object-fit: cover; border-radius: 12px; margin-bottom: 10px; }
    .price-text { color: #1e1e1e; font-size: 22px; font-weight: bold; }
    .metric-badge { background-color: #f1f3f5; padding: 3px 10px; border-radius: 6px; font-size: 0.85em; color: #495057; margin-right: 5px; display: inline-block; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

try:
    df_raw = load_data()
    df_geo_raw = load_geo_data()
    
    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    conteo_distritos = df_raw['distrito'].value_counts()
    opciones_distritos = [f"{d} ({conteo_distritos[d]})" for d in sorted(df_raw['distrito'].unique())]
    
    sel_dist_formateados = st.sidebar.multiselect(
        "Filtrar por distrito:", 
        options=opciones_distritos, 
        default=None,
        placeholder="Selecciona uno o varios distritos..."
    )
    
    distritos_seleccionados = [d.split(" (")[0] for d in sel_dist_formateados]
    
    opciones_min = [0, 50000, 100000, 150000, 200000, 300000, 500000]
    opciones_max = [100000, 200000, 300000, 500000, 1000000, 3000000, 5000000, "Sin límite"]

    st.sidebar.write("### Precio (€)")
    col1, col2 = st.sidebar.columns(2)
    min_sel = col1.selectbox("Mín", options=opciones_min, format_func=lambda x: f"{x:,} €" if x != 0 else "Mín")
    max_sel = col2.selectbox("Máx", options=opciones_max, index=len(opciones_max)-1)

    precio_max_val = float('inf') if max_sel == "Sin límite" else float(max_sel)
    
    col_f1, col_f2 = st.sidebar.columns(2)
    min_hab = col_f1.selectbox("Habitaciones", [0, 1, 2, 3, 4], index=0)
    min_ban = col_f2.selectbox("Baños", [0, 1, 2, 3], index=0)

    # Filtrado Dinámico
    df = df_raw[
        (df_raw['distrito'].isin(distritos_seleccionados)) & 
        (df_raw['precio'] >= float(min_sel)) &          
        (df_raw['precio'] <= precio_max_val) &
        (df_raw['n_habitaciones'] >= min_hab) &
        (df_raw['n_baños'] >= min_ban)
    ].dropna(subset=['lat', 'lon'])
    
    df, _, _ = apply_color_logic(df)

    # GUARDAR EN SESSION STATE
    st.session_state['df'] = df
    st.session_state['df_geo_raw'] = df_geo_raw
    
    # Logout en sidebar.
    if st.sidebar.button("Cerrar sesión"):
        st.session_state["auth_ok"] = False
        st.rerun()
    # NAVEGACIÓN
    pg = st.navigation([
        st.Page("views/mapa.py", title="📍 Mapa de Mercado", default=True),
        st.Page("views/buscador.py", title="🏠 Buscador Detallado")
    ])
    pg.run()

except Exception as e:
    st.error(f"Error: {e}")