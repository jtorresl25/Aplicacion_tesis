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

col1, col2, col3, col4 = st.columns(4)
with col1:
    cero = st.number_input(
        "Cero (ns)", min_value=0.0, value=7.0, step=0.5, key="cero")
with col2:
    profundidad = st.number_input(
        "Profundidad (cm)", min_value=0.0, value=20.0, step=1.0, key="profundidad")
with col3:
    grosor = st.number_input(
        "Grosor (cm)", min_value=0.0, value=10.0, step=1.0, key="grosor")
with col4:
    velocidad = st.number_input(
        "Velocidad (m/ns)", min_value=0.05, max_value=0.40, value=0.1889, step=0.001, key="velocidad")

# ====== Controles extra de visualización (compacto, plegable y con tooltips) ======
with st.expander("Ajustes de visualización", expanded=False):
    # --- Fila 1: Colormap + Modo de intensidad ---
    c1, c2 = st.columns([1, 1])
    with c1:
        cmap = st.selectbox(
            "Colormap",
            ["gray", "seismic", "RdBu_r", "viridis",
                "plasma", "inferno", "magma", "cividis"],
            index=0, key="viz_cmap",
            help="Paleta de colores para representar el radargrama. No altera los datos; solo su apariencia. "
                 "‘gray’ es el estándar; ‘seismic’/‘RdBu_r’ resaltan la polaridad."
        )
    with c2:
        intensity_mode = st.radio(
            "Intensidad",
            ["Contraste (±σ/contraste)", "Percentiles"],
            index=0, horizontal=True, key="viz_int_mode",
            help="Elige cómo escalar la amplitud de la imagen. "
                 "• Contraste: usa un rango simétrico ±(σ/contraste). "
                 "• Percentiles: recorta extremos (robusto a outliers)."
        )

    # --- Fila 2: Control de intensidad (compacto) ---
    pmin = pmax = None
    contrast = None
    if intensity_mode == "Contraste (±σ/contraste)":
        contrast = st.slider(
            "Contraste", 1.0, 10.0, 3.0, 0.5, key="viz_contrast",
            help="Escala de intensidad: vmin/vmax = ±(σ/contraste). "
                 "Valores mayores => rango más amplio (menos saturación); "
                 "valores menores => más contraste (posible saturación)."
        )
    else:
        pmin, pmax = st.slider(
            "Percentiles [min, max]", 0.0, 100.0, (2.0, 98.0), 0.5, key="viz_prange",
            help="Define el rango dinámico recortando valores extremos. "
                 "Útil para mejorar contraste cuando hay outliers."
        )

    st.markdown("**Filtros**")

    # --- Fila 3: Filtros (3 columnas) ---
    f1, f2, f3 = st.columns(3)
    with f1:
        use_bg = st.checkbox(
            "Background removal", value=True, key="viz_bg",
            help="Resta la traza media (promedio en columnas) para eliminar componente DC y horizontales "
                 "muy persistentes (baseline)."
        )
        dewow_ns = st.slider(
            "Dewow (ns)", 0.0, 50.0, 10.0, 1.0, key="viz_dewow",
            help="Filtro pasa-altos suave en el tiempo (media móvil). "
                 "Reduce bajas frecuencias del baseline (‘wow’). 5–20 ns suele funcionar bien."
        )
    with f2:
        agc_ns = st.slider(
            "AGC (ns)", 0.0, 200.0, 0.0, 5.0, key="viz_agc",
            help="Ganancia automática por ventana temporal (RMS). "
                 "Compensa atenuación con la profundidad; puede ‘lavar’ amplitudes cercanas si es muy grande."
        )
        gauss_sigma = st.slider(
            "Gauss σ", 0.0, 3.0, 0.0, 0.1, key="viz_gauss",
            help="Suavizado gaussiano 2D (reduce ruido de alta frecuencia). "
                 "Valores pequeños (0.3–1.0) limpian sin perder demasiados detalles."
        )
    with f3:
        unsharp_sigma = st.slider(
            "Unsharp σ", 0.0, 3.0, 0.0, 0.1, key="viz_unsharp_sigma",
            help="Tamaño del desenfoque previo al realce (unsharp). "
                 "Pequeño = bordes finos; grande = bordes más anchos."
        )
        unsharp_amount = st.slider(
            "Unsharp amount", 0.0, 2.0, 0.0, 0.1, key="viz_unsharp_amount",
            help="Intensidad del realce de bordes. 0.3–0.8 suele ser un buen punto de partida."
        )

# Botón para analizar los archivos
if st.button("Analizar horizontalmente", key="Analizar") and st.session_state["rad"] and st.session_state["rd7"]:
    st.switch_page("pages/cargando.py")

# Botón para analizar los archivos
if st.button("Analizar verticalmente", key="Analizar_vertical") and st.session_state["rad"] and st.session_state["rd7"]:
    st.switch_page("pages/resultados_vertical.py")

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
            rd7_path, rad_path,
            profundidad, grosor, velocidad, cero,
            # nuevos params:
            cmap=cmap, intensity_mode=intensity_mode, contrast=contrast,
            pmin=pmin, pmax=pmax,
            use_bg=use_bg, dewow_ns=dewow_ns, agc_ns=agc_ns,
            gauss_sigma=gauss_sigma, unsharp_sigma=unsharp_sigma, unsharp_amount=unsharp_amount
        )

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
