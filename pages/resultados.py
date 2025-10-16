from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
from scripts.evalue import *
from io import BytesIO


segmentos_detecciones, df, df_distribución = st.session_state[
    'segmentos_detecciones'], st.session_state['df'], st.session_state['df_distribución']

style()

if st.button("Volver", key="Volver"):
    # borrado de la sesión
    st.session_state['data_raw'] = None
    st.session_state['data_map'] = None
    st.switch_page("app.py")

h1("Resultados del análisis")
if df is not None and df_distribución is not None:
    col1, col2 = st.columns(2)

    with col1:
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        st.download_button(
            label="📥 Descargar datos en Excel",
            data=excel_buffer,
            file_name="resultados_analisis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col2:
        excel_buffer2 = BytesIO()
        df_distribución.to_excel(excel_buffer2, index=False, engine='openpyxl')
        excel_buffer2.seek(0)
        st.download_button(
            label="📊 Descargar distribución",
            data=excel_buffer2,
            file_name="resultados_distribucion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif df is not None:
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    st.download_button(
        label="📥 Descargar datos en Excel",
        data=excel_buffer,
        file_name="resultados_analisis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif df_distribución is not None:
    excel_buffer2 = BytesIO()
    df_distribución.to_excel(excel_buffer2, index=False, engine='openpyxl')
    excel_buffer2.seek(0)
    st.download_button(
        label="📊 Descargar distribución",
        data=excel_buffer2,
        file_name="resultados_distribucion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
st.text("")
st.text("🔴 Los segmentos coloreados en rojo representan que el modelo ha detectado asbesto en esas secciones")
st.text("en esas secciones.")
st.text("")

# lineas_profundidad = [
#     {'y': 10, 'color': 'Black', 'estilo': '-', 'grosor': 2},
# ]

# lineas_grosor = [
#     {'x': 15, 'color': 'Blue', 'estilo': '-', 'grosor': 2},
# ]
lineas_profundidad = [
]

lineas_grosor = [
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
