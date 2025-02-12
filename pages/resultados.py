from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
from streamlit_folium import st_folium

style()

h1("Resultados del análisis")

if st.button("Volver", key="Volver"):
    # borrado de la sesión
    st.session_state['data_raw'] = None
    st.session_state['data_map'] = None
    st.switch_page("app.py")

# Ejemplo de uso con datos simulados del modelo
segmentos_detecciones = [
    (50, 1075),
    (2000, 2500),
    (3000, 3600)
]

lineas_profundidad = [
    {'y': 10, 'color': 'Black', 'estilo': '-', 'grosor': 2},
    {'y': 15, 'color': 'Black', 'estilo': '-', 'grosor': 2},
    {'y': 10, 'color': 'Black', 'estilo': '-', 'grosor': 2},
]

lineas_grosor = [
    {'x': 15, 'color': 'Blue', 'estilo': '-', 'grosor': 2},
    {'x': 17, 'color': 'Blue', 'estilo': '-', 'grosor': 2},
    {'x': 15, 'color': 'Blue', 'estilo': '-', 'grosor': 2},
]

mostrar_radagrama_detecciones(st.session_state['data_raw'],
                              segmentos=segmentos_detecciones,
                              lineas_horizontales=lineas_profundidad, lineas_grosores=lineas_grosor)

if segmentos_detecciones:
    mostrar_mapa_segmentos_detectados(
        segmentos_detecciones)

if st.button("Mas detalles", key="detalles"):
    st.switch_page("pages/detalle.py")
