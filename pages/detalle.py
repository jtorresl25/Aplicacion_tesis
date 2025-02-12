from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
from streamlit_folium import st_folium

style()

h1("Resultados del análisis")

if st.button("Volver", key="Volver_resultados"):
    st.switch_page("pages/resultados.py")


col1, col2 = st.columns(2)

with col1:
    h1("Radagrama")

with col2:
    h1("Resultados")

dibujar_segmentos_radagrama(st.session_state['data_raw'][0])
