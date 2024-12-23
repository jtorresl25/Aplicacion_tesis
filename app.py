from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
import tempfile
from streamlit_folium import st_folium

# streamlit run app.py

style()

# Interfaz de Streamlit
h1("Detector de asbestos en imágenes de GPR")

if st.button("Cargar demo", key="Cargar demo"):
    path_rad = "statics\DAT_0052_1.rad"
    path_rd7 = "statics\DAT_0052_1.rd7"
    path_mapa = "statics\DAT_0052_1.cor"
    rad = open(path_rad, "rb")
    rd7 = open(path_rd7, "rb")
    mapa = open(path_mapa, "rb")
    st.session_state['direccion_mapa'] = path_mapa
    st.session_state['direccion_rad'] = path_rad
    st.session_state['direccion_rd7'] = path_rd7
    st.switch_page("pages/resultados.py")

pasos("1. Cargue el archivo de datos .rad")
pasos("2. Cargue el archivo de la imagen .rd7")
pasos("3. Cargue el archivo .cor")

rad = st.file_uploader("Cargar archivo .rad", type=["rad"])
rd7 = st.file_uploader("Cargar archivo .rd7", type=["rd7"])
mapa = st.file_uploader("Cargar archivo .cor", type=["cor"])

if st.button("Analizar", key="Analizar") and rad is not None and rd7 is not None:
    st.switch_page("pages/resultados.py")


# Mostrar el radagrama al cargar el archivo
if rad is not None and rd7 is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".rad") as temp_file_rad:
        # Escribir los datos del archivo subido en el archivo temporal
        temp_file_rad.write(rad.read())
        rad = temp_file_rad.name  # Obtener la ruta del archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".rd7") as temp_file_rd7:
        # Escribir los datos del archivo subido en el archivo temporal
        temp_file_rd7.write(rd7.read())
        rd7 = temp_file_rd7.name
    with st.spinner('Cargando radagrama...'):
        mostrar_radagrama(rd7, rad)

# Mostrar el mapa al cargar el archivo
if mapa is not None:
    with st.spinner('Cargando mapa...'):
        df_map = leer_archivo_cor(mapa)
        folium_map = mostrar_mapa(df_map)
        st.session_state['direccion_mapa'] = mapa
        # Mostrar el mapa interactivo usando streamlit-folium
        st_folium(folium_map, width=700, height=500)
