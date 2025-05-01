import time
import streamlit as st
from scripts.text import *
from scripts.evalue import *
import threading

st.markdown(
    f"""
        <h1 style="text-align: center; padding-top: 0; font-size:40px;">Analizando la sostenibilidad</h1>
        """,
    unsafe_allow_html=True
)


# Mensajes para mostrar durante la ejecución del modelo
mensajes = [
    "Analizando señales subterráneas...",
    "Detallando trazas de asbesto...",
    "Refinando el mapa de subsuelo...",
    "Optimizando la detección con IA...",
    "Validando resultados finales..."
]

# Indicador de progreso con lupas
cargando = [
    "🔍",
    "📡🔍",
    "🔍🔬🔍",
    "📡🔍🔍🔬",
    "🔍🔍🔬🔍🔍"
]

# Función para actualizar los mensajes en paralelo


def mostrar_mensajes():
    mensaje_placeholder = st.empty()
    patitas_placeholder = st.empty()
    while not proceso_terminado.is_set():
        for mensaje in mensajes:
            for pata in cargando:
                if proceso_terminado.is_set():
                    break
                patitas_html = f"""
                <div style="padding: 10px; text-align: center; font-size: 30px;">
                    {pata}
                </div>
                """
                patitas_placeholder.markdown(
                    patitas_html, unsafe_allow_html=True)
                time.sleep(0.5)
            if proceso_terminado.is_set():  # Detiene la secuencia si el proceso termina
                break
            # Estilo del mensaje (puedes ajustar los estilos CSS según tus necesidades)
            mensaje_html = f"""
            <div style="padding: 10px; text-align: center; font-size: 30px;">
                {mensaje}
            </div>
            """
            mensaje_placeholder.markdown(mensaje_html, unsafe_allow_html=True)
    patitas_placeholder.empty()  # Limpia el mensaje después de que el proceso termina
    mensaje_placeholder.empty()  # Limpia el mensaje después de que el proceso termina


# Variable de control para saber si el proceso ha terminado
proceso_terminado = threading.Event()

global data
global df_mapa

data = st.session_state['data_raw']
df_mapa = st.session_state['df_mapa'][[
    'ID', 'Latitud', 'NS', 'Longitud', 'EW']]


def ejecutar_proceso():
    global segmentos_detecciones
    global df
    global segmentos_detecciones
    global df
    segmentos_detecciones, df = evaluar_imagen_completa(
        data, df_mapa)
    print("Segmentos detectados: ", segmentos_detecciones)
    proceso_terminado.set()  # Indica que el proceso ha terminado
    try:
        pass
    except Exception as e:
        segmentos_detecciones = "error"
        print("Error en el proceso:", e)
        proceso_terminado.set()


hilo_proceso = threading.Thread(target=ejecutar_proceso)
hilo_proceso.start()

# Inicia el hilo para los mensajes
mostrar_mensajes()

# Espera a que el hilo que ejecuta `run()` termine antes de continuar
hilo_proceso.join()

print("Proceso terminado")

if segmentos_detecciones == "error":
    st.error("Ocurrió un error durante el análisis. Por favor, inténtelo de nuevo.")
else:
    st.session_state['segmentos_detecciones'] = segmentos_detecciones
    st.session_state['df'] = df

    st.switch_page("pages/resultados.py")
