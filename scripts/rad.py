import os
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from scripts.mapa import *
from streamlit_folium import st_folium
from scripts.text import *
# from scripts.evalue import *

# Función modificada para leer el contenido binario de los archivos subidos


def readMALA(file_rd7, file_rad):
    info = readGPRhdr(file_rad)

    # I'm not sure what the format of rd7 is. Just assuming it's the same
    filename = file_rd7
    data = np.fromfile(filename, dtype=np.int32)

    nrows = int(len(data)/int(info['SAMPLES']))

    data = (np.asmatrix(data.reshape(nrows, int(info['SAMPLES'])))).transpose()

    return data, info


def readGPRhdr(filename):
    '''
    Reads the MALA header

    INPUT: 
    filename      file name for header with .rad extension

    OUTPUT:
    info          dict with information from the header
    '''
    # Read in text file
    info = {}
    with open(filename) as f:
        for line in f:
            strsp = line.split(':')
            info[strsp[0]] = strsp[1].strip()

    # if the distance interval is zero, set it to one
    # TODO should be done properly with the coordinates (if available)
    # Alain: I changed 0.1 to eps, in case someone uses high spatial resolution (e.g. lab)
    if float(info['DISTANCE INTERVAL']) < np.finfo(float).eps:
        info['DISTANCE INTERVAL'] = 1.

    return info


def mostrar_radagrama(file_name, file_name_rad):
    xrng = 10
    yrng = 20
    contrast = 3.0
    # colores utiles HSV, gray
    color = "gray"
    print(file_name)
    data_raw = readMALA(file_name, file_name_rad)
    st.session_state['data_raw'] = data_raw
    data = data_raw[0]
    print(data.shape)
    print(data)
    # twtt es un array que representa el tiempo en un rango de 0 a y nanosegundos en n "segmentos".
    # Ej: empieza desde cero, aumentando en 0.1955 unidades hasta los 197.65 nanosegundos repartidos en 1012 samples
    twtt = np.linspace(
        0, float(data_raw[1]["TIMEWINDOW"]), int(data_raw[1]['SAMPLES']))
    # profilePos es un array que representa la distancia en un rango de 0 a x metros de longitud en n "segmentos".
    # Ej: empieza desde cero, aumentando en 0.049 unidades hasta los 87.401 metros repartidos en 1784 segmentos
    profilePos = float(data_raw[1]["DISTANCE INTERVAL"]
                       )*np.arange(0, data.shape[1])
    # Intervalo de distancia (eje x):
    dx = profilePos[3]-profilePos[2]
    # Intervalo de tiempos (eje y)
    dt = twtt[3]-twtt[2]

    stdcont = np.nanmax(np.abs(data)[:])
    # Crear la figura y los ejes
    fig, ax = plt.subplots()

    # Mostrar la imagen en los ejes (ax) con los parámetros adecuados
    img = ax.imshow(data, cmap=color, extent=[min(profilePos) - dx/2.0,
                                              max(profilePos) + dx/2.0,
                                              max(twtt) + dt/2.0,
                                              min(twtt) - dt/2.0],
                    aspect="auto", vmin=-stdcont/contrast, vmax=stdcont/contrast)

    # Etiquetas de los ejes
    ax.set_ylabel("Tiempo [ns]")
    ax.set_xlabel("Posición del perfil [m]")
    ax.xaxis.tick_top()  # Mover los ticks del eje X a la parte superior
    # Colocar la etiqueta del eje X en la parte superior
    ax.xaxis.set_label_position('top')

    # Definir límites
    ax.set_ylim(yrng)
    ax.set_xlim(xrng)

    # Mostrar la figura en Streamlit
    st.pyplot(fig)


def grafico_radagrama(data):
    # Crear la figura y los ejes
    fig, ax = plt.subplots()

    # Mostrar la imagen en los ejes (ax) con los parámetros adecuados
    img = ax.imshow(data, cmap="gray", aspect="auto")

    # Etiquetas de los ejes
    ax.set_ylabel("Tiempo [ns]")
    ax.set_xlabel("Posición del perfil [m]")
    ax.xaxis.tick_top()  # Mover los ticks del eje X a la parte superior
    # Colocar la etiqueta del eje X en la parte superior
    ax.xaxis.set_label_position('top')

    # Mostrar la figura en Streamlit
    st.pyplot(fig)


def dibujar_segmentos_radagrama(data):
    length = data.shape[1]
    # Bucle para dibujar los segmentos en el radagrama, cada uno de 244 columnas
    for i in range(0, length, 244):
        # Crear dos columnas
        col1, col2 = st.columns(2)
        set_0 = 5
        df = data[set_0:set_0+244, i:i+244]

        if df.shape[1] == 244:
            # resultado = evaluar_imagen(df)
            resultado = "Asbesto"
            profundidad = 50
            grosor = 10

            # En la primera columna mostrar el gráfico
            with col1:
                # Crear la figura y los ejes
                fig, ax = plt.subplots()

                # Mostrar la imagen en los ejes (ax) con los parámetros adecuados
                img = ax.imshow(df, cmap="gray", aspect="auto")

                # Calcular el intervalo correcto de posiciones en el eje x
                inicio = i  # Calcula la posición inicial en metros
                # Calcula la posición final en metros
                fin = (i + 244)
                # Establecer las posiciones de las etiquetas en el eje x
                ax.set_xticks([0, 243])
                # Etiquetas con valores reales de posición
                ax.set_xticklabels([f"{inicio:.2f}", f"{fin:.2f}"])

                # Etiquetas de los ejes
                ax.set_ylabel("Tiempo [ns]")
                ax.set_xlabel("Posición del perfil [m]")
                ax.xaxis.tick_top()
                ax.xaxis.set_label_position('top')

                # Graficar las dos líneas horizontales en la profundidad dada
                ax.hlines(profundidad, xmin=0, xmax=243, colors='r',
                          linestyles='-', linewidth=1)
                ax.hlines(profundidad + grosor, xmin=0, xmax=243,
                          colors='r', linestyles='-', linewidth=1)

                # Mostrar la figura en Streamlit
                st.pyplot(fig)

                if 'df_mapa' in st.session_state:

                    df_mapa = st.session_state['df_mapa']
                    # df mapa toma las filas donde id se encuentra entre inicio y fin
                    df_mapa = df_mapa[(df_mapa['ID'] >= inicio)
                                      & (df_mapa['ID'] <= fin)]
                    # Leer el archivo .cor
                    folium_map = mostrar_mapa(df_mapa)
                    # Mostrar el mapa interactivo usando streamlit-folium
                    st_folium(folium_map, width=400, height=150, key=fin)

            # En la segunda columna mostrar el texto (que luego podrás modificar)
            with col2:

                text_resultados(
                    f"""
            Tipo de material: {resultado}
            """)
                text_resultados(
                    f"""
            Profundidad: 2 metros
            """)
                text_resultados(
                    f"""
            Grosor de la capa: 30 cm
            """)
            # Separador entre segmentos
            st.markdown("---")
