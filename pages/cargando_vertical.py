# pages/cargando_vertical.py
import time
import threading
import streamlit as st
from scripts.text import *
from scripts.evalue_vertical import evaluar_imagen_vertical  # tu nuevo módulo vertical

# === Configura aquí a qué página saltar al final ===
RESULTS_PAGE = "pages/resultados_vertical.py"  # o tu página vertical dedicada

# ------------------- Encabezado -------------------
st.markdown(
    """
        <h1 style="text-align: center; padding-top: 0; font-size:40px;">
            Analizando las muestras (segmentación vertical)
        </h1>
    """,
    unsafe_allow_html=True
)

# ------------------- Mensajes/animación -------------------
mensajes = [
    "Analizando señales subterráneas...",
    "Detallando trazas de asbesto...",
    "Refinando el mapa de subsuelo...",
    "Optimizando la detección con IA...",
    "Validando resultados finales..."
]
cargando = ["🔍", "📡🔍", "🔍🔬🔍", "📡🔍🔍🔬", "🔍🔍🔬🔍🔍"]

proceso_terminado = threading.Event()


def mostrar_mensajes():
    mensaje_placeholder = st.empty()
    icon_placeholder = st.empty()
    while not proceso_terminado.is_set():
        for msg in mensajes:
            for icon in cargando:
                if proceso_terminado.is_set():
                    break
                icon_placeholder.markdown(
                    f"<div style='padding:10px; text-align:center; font-size:30px;'>{icon}</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.5)
            if proceso_terminado.is_set():
                break
            mensaje_placeholder.markdown(
                f"<div style='padding:10px; text-align:center; font-size:30px;'>{msg}</div>",
                unsafe_allow_html=True
            )
    icon_placeholder.empty()
    mensaje_placeholder.empty()


# ------------------- Insumos desde sesión -------------------
data = st.session_state.get("data_raw")
if data is None:
    st.error("No hay radargrama en sesión ('data_raw'). Regresa y carga los archivos.")
    st.stop()

df_mapa = st.session_state.get("df_mapa")
if df_mapa is not None:
    req = ['ID', 'Latitud', 'NS', 'Longitud', 'EW']
    if all(c in df_mapa.columns for c in req):
        df_mapa = df_mapa[req].copy()
    else:
        df_mapa = None

# Hiperparámetros (toma de session_state o defaults)
vert_height = int(st.session_state.get("vert_height", 128))
vert_stride = int(st.session_state.get("vert_stride", 64))
n_metros = int(st.session_state.get("n_metros", 3))
horiz_width = int(44 * n_metros)
horiz_stride = int(44 * n_metros)
mc_iterations = int(st.session_state.get("mc_iterations", 25))
positive_threshold = float(st.session_state.get("positive_threshold", 0.5))
weights_path = st.session_state.get(
    "weights_vertical", "best_model_export_v.pth")

# ------------------- Trabajo pesado (hilo) -------------------
resultado_error = {"ok": True, "exc": None}
cajas_positivas_v = None
df_v = None
df_distrib_v = None


def ejecutar_proceso():
    nonlocal_vars = {}
    try:
        out = evaluar_imagen_vertical(
            data=data,
            df_mapa=df_mapa,
            weights_path=str(weights_path),
            vert_height=int(vert_height),
            vert_stride=int(vert_stride),
            horiz_width=int(horiz_width),
            horiz_stride=int(horiz_stride),
            mc_iterations=int(mc_iterations),
            positive_threshold=float(positive_threshold)
        )
        nonlocal_vars["cajas"], nonlocal_vars["df"], nonlocal_vars["dfmc"] = out
    except Exception as e:
        resultado_error["ok"] = False
        resultado_error["exc"] = e
    finally:
        # Propaga resultados (si hay)
        if "cajas" in nonlocal_vars:
            globals()['cajas_positivas_v'] = nonlocal_vars["cajas"]
            globals()['df_v'] = nonlocal_vars["df"]
            globals()['df_distrib_v'] = nonlocal_vars["dfmc"]
        proceso_terminado.set()


# Lanza hilos: cómputo + animación
hilo_proc = threading.Thread(target=ejecutar_proceso, name="ejecutar_proceso")
hilo_proc.start()
mostrar_mensajes()   # corre en hilo principal
hilo_proc.join()
print("Proceso vertical terminado")

# ------------------- Manejo de resultados -------------------
if not resultado_error["ok"]:
    st.error("Ocurrió un error durante el análisis vertical.")
    st.caption("Detalle técnico para depuración:")
    st.exception(resultado_error["exc"])
    st.stop()

# Guarda resultados en sesión (vertical + genéricos para reutilizar UI actual)
st.session_state['segmentos_detecciones_vertical'] = cajas_positivas_v
st.session_state['df_vertical'] = df_v
st.session_state['df_distribución_vertical'] = df_distrib_v

# reutilizar resultados.py
st.session_state['segmentos_detecciones'] = cajas_positivas_v
st.session_state['df'] = df_v
st.session_state['df_distribución'] = df_distrib_v

# Redirige a resultados
st.switch_page(RESULTS_PAGE)
