# pages/resultados_vertical.py
from io import BytesIO
import streamlit as st
from scripts.mapa import *
from streamlit_folium import st_folium

from scripts.text import style, h1
from scripts.rad_vertical import mostrar_radagrama_cajas_aleatorias

# --- La primera llamada de Streamlit debe configurar la página ---
style()  # usa tu set_page_config + estilos

# --- Botón volver ---
if st.button("Volver", key="Volver"):
    st.session_state['data_raw'] = None
    st.session_state['data_map'] = None
    st.switch_page("app.py")

# --- Verificación de insumos ---
if 'data_raw' not in st.session_state or st.session_state['data_raw'] is None:
    st.error("No hay radargrama cargado en sesión.")
    st.stop()

# --- Título ---
h1("Resultados del análisis — Cajas aleatorias (vertical)")

st.text("")
st.text("🔴 Cada caja roja representa una detección de asbesto por parte del modelo.")
st.text("La imagen representada es una muestra de cómo el modelo identifica estas detecciones")
st.text("Aún no se ha conectado un modelo.")
st.text("")

# --- Dibujo del radargrama + cajas aleatorias ---
mostrar_radagrama_cajas_aleatorias(
    st.session_state['data_raw'],
    box_height_rows=16,
    box_width_cols=132,
    prob=0.5,
    max_rows=40,     # número de filas a partir de 7.5 ns
    min_time_ns=7.5,  # umbral
    color="red",
    alpha=0.30
)

# --- (Opcional) Descargas solo si ya existen en sesión (no requerido para cajas aleatorias) ---
df = st.session_state.get('df_vertical')
df_mc = st.session_state.get('df_distribución_vertical')

if df is not None or df_mc is not None:
    st.write("")
    col_a, col_b = st.columns(2)

    if df is not None:
        with col_a:
            buf = BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            buf.seek(0)
            st.download_button(
                "📥 Descargar datos (Excel)",
                buf,
                file_name="resultados_analisis_vertical.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    if df_mc is not None:
        with col_b:
            buf = BytesIO()
            df_mc.to_excel(buf, index=False, engine='openpyxl')
            buf.seek(0)
            st.download_button(
                "📥 Descargar distribución MC",
                buf,
                file_name="distribucion_mc_vertical.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --- Navegación opcional ---
if st.session_state["mapa"]:
    st.title("Mapa del recorrido")
    folium_map = mostrar_mapa(st.session_state["df_mapa"])
    # Mostrar el mapa interactivo usando streamlit-folium
    st_folium(folium_map, width=700, height=500)
