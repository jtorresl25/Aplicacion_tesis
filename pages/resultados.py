from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
from scripts.evalue import *
from io import BytesIO


segmentos_detecciones, df = st.session_state['segmentos_detecciones'], st.session_state['df']

style()

if st.button("Volver", key="Volver"):
    # borrado de la sesión
    st.session_state['data_raw'] = None
    st.session_state['data_map'] = None
    st.switch_page("app.py")

h1("Resultados del análisis")
# Botón para descargar Excel (Añadir este bloque)
if df is not None:
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    st.download_button(
        label="📥 Descargar datos en Excel",
        data=excel_buffer,
        file_name="resultados_analisis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
st.text("")
st.text("🔴 Los segmentos coloreados en rojo representan que el modelo ha detectato asbesto")
st.text(
    f'en esa zona con mas de un {st.session_state["numero"]}% de confianza.')
st.text("")
st.text("⚫ Las lineas de color negro representan la profundidad de la detección.")
st.text("")
st.text("⚪ Las lineas de color blanco representan el final de la capa de asbesto")
st.text("")

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
    st.title("Segmentos detectados")
    mostrar_mapa_segmentos_detectados(
        segmentos_detecciones)

if st.session_state["mapa"]:
    st.title("Mapa del recorrido")
    folium_map = mostrar_mapa(st.session_state["df_mapa"])
    # Mostrar el mapa interactivo usando streamlit-folium
    st_folium(folium_map, width=700, height=500)

if st.button("Mas detalles", key="detalles"):
    st.switch_page("pages/detalle.py")
