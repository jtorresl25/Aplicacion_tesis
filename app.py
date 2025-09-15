from scripts.text import *
from scripts.mapa import *
from scripts.rad import *
import tempfile
from streamlit_folium import st_folium
import streamlit as st

# Rutas predefinidas para los archivos de demo
path_rad = "statics/DAT_0020_1.rad"
path_rd7 = "statics/DAT_0020_1.rd7"
path_mapa = "statics/DAT_0020_1.cor"
# Rutas predefinidas para los archivos de demo
path_rad_none = "statics/DAT_0017_1.rad"
path_rd7_none = "statics/DAT_0017_1.rd7"
path_mapa_none = "statics/DAT_0017_1.cor"

# Inicializar estado de sesión para los archivos
if "rad" not in st.session_state:
    st.session_state["rad"] = None
if "rd7" not in st.session_state:
    st.session_state["rd7"] = None
if "mapa" not in st.session_state:
    st.session_state["mapa"] = None

# Aplicar estilo
style()

# Interfaz de Streamlit
h1("Detector de asbestos en imágenes de GPR")

pasos("1. Cargue el archivo de datos .rad")
pasos("2. Cargue el archivo de la imagen .rd7")
pasos("3. Cargue el archivo .cor")

# Botón para cargar demo
if st.button("Cargar Demo asbesto", key="Demo_asbesto"):

    st.session_state["rad"] = path_rad
    st.session_state["rd7"] = path_rd7
    st.session_state["mapa"] = path_mapa

# Botón para cargar demo sin asbesto
if st.button("Cargar Demo sin asbesto", key="Demo_sin_asbesto"):

    st.session_state["rad"] = path_rad_none
    st.session_state["rd7"] = path_rd7_none
    st.session_state["mapa"] = path_mapa_none

# Espacios para cargar manualmente los archivos
rad = st.file_uploader("Cargar archivo .rad", type=["rad"])
rd7 = st.file_uploader("Cargar archivo .rd7", type=["rd7"])
mapa = st.file_uploader("Cargar archivo .cor", type=["cor"])

# Actualizar archivos en el estado si se suben manualmente
if rad is not None:
    st.session_state["rad"] = rad
if rd7 is not None:
    st.session_state["rd7"] = rd7
if mapa is not None:
    st.session_state["mapa"] = mapa

# Velocidad de propagación
st.session_state["velocidad"] = st.number_input(
    "Ingrese la velocidad de propagación (m/ns)", min_value=0.0, value=0.1889)

# Input para ingresar profundidad
st.session_state["profundidad"] = st.number_input(
    "Ingrese la profundidad de la capa (cm)", min_value=0, value=50)

# Input para ingresar el grosor de la capa
st.session_state["grosor"] = st.number_input(
    "Ingrese el grosor de la capa (cm)", min_value=0, value=50)

# Input setear el valor de 0 en el radagrama
st.session_state["cero"] = st.number_input(
    "Ingrese el valor de 0 en el radagrama (ns)", min_value=0, value=7)

# Botón para analizar los archivos
if st.button("Analizar", key="Analizar") and st.session_state["rad"] and st.session_state["rd7"]:
    st.switch_page("pages/cargando.py")

# Mostrar el radagrama si los archivos .rad y .rd7 están disponibles
if st.session_state["rad"] and st.session_state["rd7"]:
    if isinstance(st.session_state["rad"], str) and isinstance(st.session_state["rd7"], str):
        # Los archivos provienen del demo
        rad_path = st.session_state["rad"]
        rd7_path = st.session_state["rd7"]
    else:
        # Los archivos se suben manualmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rad") as temp_file_rad:
            temp_file_rad.write(st.session_state["rad"].read())
            rad_path = temp_file_rad.name
            st.session_state['direccion_rad'] = rad_path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".rd7") as temp_file_rd7:
            temp_file_rd7.write(st.session_state["rd7"].read())
            rd7_path = temp_file_rd7.name
            st.session_state['direccion_rd7'] = rd7_path

    with st.spinner('Cargando radagrama...'):
        data_raw = readMALA(rd7_path, rad_path)
        st.session_state['data_raw'] = data_raw
        mostrar_radagrama(
            rd7_path, rad_path, st.session_state["profundidad"], st.session_state["grosor"], st.session_state["velocidad"], st.session_state["cero"])

# Mostrar el mapa si el archivo .cor está disponible
if st.session_state["mapa"]:
    if isinstance(st.session_state["mapa"], str):
        # El archivo proviene del demo
        mapa_path = st.session_state["mapa"]
    else:
        # El archivo se sube manualmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cor") as temp_file_mapa:
            temp_file_mapa.write(st.session_state["mapa"].read())
            mapa_path = temp_file_mapa.name

    with st.spinner('Cargando mapa...'):
        df_map = leer_archivo_cor(mapa_path)
        st.session_state['df_mapa'] = df_map
        folium_map = mostrar_mapa(df_map)
        st.session_state['direccion_mapa'] = mapa_path
        # Mostrar el mapa interactivo usando streamlit-folium
        st_folium(folium_map, width=700, height=500)
