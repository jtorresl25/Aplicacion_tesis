from geopy.distance import geodesic
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
    data_raw = readMALA(file_name, file_name_rad)
    st.session_state['data_raw'] = data_raw
    data = data_raw[0]
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


def mostrar_radagrama_detecciones(data_raw, segmentos=None, lineas_horizontales=None, lineas_grosores=None):
    # Configuración inicial
    xrng = 10
    yrng = 20
    contrast = 3.0
    color = "gray"
    data = data_raw[0]

    twtt = np.linspace(
        0, float(data_raw[1]["TIMEWINDOW"]), int(data_raw[1]['SAMPLES']))
    profilePos = float(data_raw[1]["DISTANCE INTERVAL"]
                       ) * np.arange(0, data.shape[1])
    dx = profilePos[3] - profilePos[2]
    dt = twtt[3] - twtt[2]
    stdcont = np.nanmax(np.abs(data)[:])

    fig, ax = plt.subplots()

    # Gráfico base
    img = ax.imshow(data, cmap=color,
                    extent=[min(profilePos) - dx/2.0,
                            max(profilePos) + dx/2.0,
                            max(twtt) + dt/2.0,
                            min(twtt) - dt/2.0],
                    aspect="auto",
                    vmin=-stdcont/contrast,
                    vmax=stdcont/contrast)

    # Resaltar segmentos y dibujar líneas
    if segmentos:
        for i, segmento in enumerate(segmentos):
            start_col, end_col = segmento
            inicio = profilePos[start_col]
            fin = profilePos[end_col]

            # Resaltar área del segmento
            ax.axvspan(inicio, fin, color='red', alpha=0.3)

            # Dibujar líneas horizontales solo en el segmento
            if lineas_horizontales and i < len(lineas_horizontales):
                linea = lineas_horizontales[i]
                ax.hlines(linea['y'],
                          xmin=inicio,
                          xmax=fin,
                          colors='black',
                          linestyles='-',
                          linewidths=2,)

            # Dibujar lineas de grosor solo en el segmento
            if lineas_grosores and i < len(lineas_grosores):
                linea = lineas_grosores[i]
                ax.hlines(linea['x'],
                          xmin=inicio,
                          xmax=fin,
                          colors='White',
                          linestyles='-',
                          linewidths=2,
                          )

    # Configuración de ejes
    ax.set_ylabel("Tiempo [ns]")
    ax.set_xlabel("Posición del perfil [m]")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_ylim(yrng)
    ax.set_xlim([min(profilePos), max(profilePos)])

    st.pyplot(fig)


def dibujar_segmentos_radagrama(data):
    # Obtener parámetros de posición desde el header
    info = st.session_state['data_raw'][1]
    dx = float(info['DISTANCE INTERVAL'])

    length = data.shape[1]
    tamano_segmento = 44  # Segmento de 44 columnas

    for i in range(0, length, tamano_segmento):
        col1, col2 = st.columns(2)
        set_0 = 5
        df = data[set_0:set_0+120, i:i+tamano_segmento]

        if df.shape[1] == tamano_segmento:
            resultado = "Asbesto"
            profundidad = 50
            grosor = 10

            with col1:
                fig, ax = plt.subplots()
                img = ax.imshow(df, cmap="gray", aspect="auto")

                # Calcular posiciones reales
                start_pos = i * dx
                end_pos = (i + tamano_segmento - 1) * dx

                # Configurar eje X
                ax.set_xticks([0, tamano_segmento-1])
                ax.set_xticklabels([f"{start_pos:.2f}", f"{end_pos:.2f}"])

                ax.set_ylabel("Tiempo [ns]")
                ax.set_xlabel("Posición del perfil [m]")
                ax.xaxis.tick_top()
                ax.xaxis.set_label_position('top')

                # Líneas horizontales
                ax.hlines(profundidad, xmin=0, xmax=tamano_segmento -
                          1, colors='r', linewidth=1)
                ax.hlines(profundidad + grosor, xmin=0,
                          xmax=tamano_segmento-1, colors='r', linewidth=1)

                st.pyplot(fig)

                if 'df_mapa' in st.session_state:
                    df_mapa = st.session_state['df_mapa']
                    df_mapa = df_mapa[(df_mapa['ID'] >= start_pos) & (
                        df_mapa['ID'] <= end_pos)]
                    try:
                        folium_map = mostrar_mapa(df_mapa)
                        st_folium(folium_map, width=400,
                                  height=150, key=end_pos)
                    except:
                        pass

            with col2:
                text_resultados(f"""Tipo de material: {resultado}
                    Profundidad: {profundidad*0.1:.1f} metros  # Ejemplo de conversión a metros
                    Grosor de la capa: {grosor*0.1:.1f} metros""")

            st.markdown("---")


def mostrar_mapa_segmentos_detectados(segmentos_detecciones):
    if 'df_mapa' not in st.session_state or not segmentos_detecciones:
        return

    df_mapa = st.session_state['df_mapa']

    # Concatenar los segmentos detectados en un único DataFrame
    df_mapa_final = pd.DataFrame()
    for segmento in segmentos_detecciones:
        start_pos = segmento[0]
        end_pos = segmento[1]
        df_segmento = df_mapa[(df_mapa['ID'] >= start_pos)
                              & (df_mapa['ID'] <= end_pos)]
        df_mapa_final = pd.concat(
            [df_mapa_final, df_segmento], ignore_index=True)

    # Ordenar el DataFrame por 'ID' para asegurar el orden correcto
    df_mapa_final = df_mapa_final.sort_values('ID')

    # Centrar el mapa en el promedio de las coordenadas
    map_center = [df_mapa_final['Latitud'].mean(
    ), df_mapa_final['Longitud'].mean()]
    mymap = folium.Map(location=map_center, zoom_start=20)

    # Definir umbral para la diferencia de ID
    umbral_gap = 100

    # Crear listas de coordenadas e IDs
    coordinates = list(
        zip(df_mapa_final['Latitud'], df_mapa_final['Longitud']))
    ids = list(df_mapa_final['ID'])

    # Dividir los puntos en segmentos basados en la diferencia de IDs
    segmentos_linea = []
    segmento_actual = [coordinates[0]]

    for i in range(1, len(coordinates)):
        # Si la diferencia entre IDs es mayor al umbral, se rompe el segmento
        if ids[i] - ids[i-1] > umbral_gap:
            if len(segmento_actual) > 1:
                segmentos_linea.append(segmento_actual)
            segmento_actual = [coordinates[i]]
        else:
            segmento_actual.append(coordinates[i])

    # Agregar el último segmento si es válido
    if len(segmento_actual) > 1:
        segmentos_linea.append(segmento_actual)

    # Dibujar cada segmento en el mapa
    for seg in segmentos_linea:
        folium.PolyLine(locations=seg, color='red', weight=5).add_to(mymap)

    st_folium(mymap, width=700, height=400, key="mapa_segmentos_detectados")
