import streamlit as st

df = st.session_state.get('df', None)

st.header("🏠 Buscador Detallado")

if df is None or df.empty:
    st.warning("Elige al menos un distrito para ver resultados.")
else:
    st.write(f"Mostrando {len(df)} resultados.")
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
                st.write(f"**Tipo:** {row['tipo'] if row['tipo'] else 'N/A'}")
                st.write(f"**Precio/m²:** {int(row['precio_m2'])} €/m²")
                st.write(f"**Ascensor:** {'Sí' if row['ascensor'] else 'No'}")
                st.write(f"**ID:** {row['id']}")
            
            st.link_button("Ver en Idealista ↗", row['url'], use_container_width=True)
            st.write("")