import folium
import pandas as pd
import streamlit as st


def leer_archivo_cor(ruta_archivo):
    df = pd.read_csv(ruta_archivo, sep='\t', header=None)
    df.columns = ['ID', 'Fecha', 'Hora', 'Latitud', 'NS',
                  'Longitud', 'EW', 'Profundidad', 'Tipo', 'Dato_Adicional']
    df['Latitud'] = pd.to_numeric(df['Latitud'])
    df['Longitud'] = pd.to_numeric(-df['Longitud'])
    df['Profundidad'] = pd.to_numeric(df['Profundidad'])

    st.session_state['df_mapa'] = df

    return df


def mostrar_mapa(df):
    # Crear un mapa centrado en el promedio de las coordenadas
    map_center = [df['Latitud'].mean(), df['Longitud'].mean()]
    mymap = folium.Map(location=map_center, zoom_start=17)

    # Agregar trazado de las coordenadas
    coordinates = list(zip(df['Latitud'], df['Longitud']))
    folium.PolyLine(locations=coordinates, color='blue',
                    weight=5).add_to(mymap)

    return mymap
