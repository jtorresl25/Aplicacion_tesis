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

# ------------ Utilidades de filtrado ------------


def _uniform_filter1d_np(x, size, axis=0):
    if size <= 1:
        return x
    kernel = np.ones(size, dtype=np.float32) / float(size)
    return np.apply_along_axis(lambda v: np.convolve(v, kernel, mode='same'), axis, x)


def _gaussian_blur(x, sigma):
    if sigma <= 0:
        return x
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(x, sigma=sigma)
    except Exception:
        k = max(1, int(2 * sigma + 1))
        x1 = _uniform_filter1d_np(x, k, axis=0)
        x2 = _uniform_filter1d_np(x1, k, axis=1)
        return x2


def _dewow(data, win_samp=0):
    if win_samp and win_samp > 1:
        try:
            from scipy.ndimage import uniform_filter1d
            baseline = uniform_filter1d(
                data, size=win_samp, axis=0, mode='nearest')
        except Exception:
            baseline = _uniform_filter1d_np(data, size=win_samp, axis=0)
        return data - baseline
    return data


def _agc(data, win_samp=0, eps=1e-6):
    if not win_samp or win_samp <= 1:
        return data
    sq = data**2
    try:
        from scipy.ndimage import uniform_filter1d
        rms = np.sqrt(uniform_filter1d(
            sq, size=win_samp, axis=0, mode='nearest') + eps)
    except Exception:
        rms = np.sqrt(_uniform_filter1d_np(sq, size=win_samp, axis=0) + eps)
    return data / rms


def _unsharp_mask(x, sigma=0.0, amount=0.0):
    if sigma <= 0 or amount == 0:
        return x
    blur = _gaussian_blur(x, sigma=sigma)
    return x + amount * (x - blur)

# ------------ Función principal ------------


def mostrar_radagrama(
    file_name, file_name_rad,
    profundidad, grosor, velocidad=0.1889, cero=7,
    # ---- nuevos parámetros opcionales ----
    yrng=25,
    cmap="gray",
    intensity_mode="Contraste (±σ/contraste)",  # o "Percentiles"
    contrast=3.0,
    pmin=None, pmax=None,
    use_bg=True,
    dewow_ns=10.0,
    agc_ns=0.0,
    gauss_sigma=0.0,
    unsharp_sigma=0.0,
    unsharp_amount=0.0
):
    """
    profundidad, grosor: en cm (desde el nuevo cero)
    velocidad: m/ns
    cero: ns desde donde empiezas a mostrar (aire cortado)
    """

    # --- Carga y tiempo ---
    data_raw = readMALA(file_name, file_name_rad)
    st.session_state['data_raw'] = data_raw
    data = data_raw[0]  # [SAMPLES x TRACES]

    twtt = np.linspace(
        0, float(data_raw[1]["TIMEWINDOW"]), int(data_raw[1]['SAMPLES']))
    i0 = int(np.searchsorted(twtt, cero, side="left"))
    if i0 >= len(twtt):
        st.warning(
            "El valor 'cero' es mayor o igual al tiempo máximo del registro. No hay datos que mostrar.")
        return

    twtt_win = twtt[i0:]
    # 🔧 Forzar ndarray para permitir keepdims en mean, etc.
    data_win = np.asarray(data[i0:, :], dtype=float)

    # --- Filtros (orden recomendado) ---
    if use_bg:
        # Resta traza media (a lo largo de TRACES) → media por fila (tiempo)
        mean_trace = np.mean(data_win, axis=1, keepdims=True)
        data_win = data_win - mean_trace

    if dewow_ns and dewow_ns > 0:
        dt_ns = (twtt[1] - twtt[0]) if len(twtt) >= 2 else 1.0
        win_dw = max(1, int(round(dewow_ns / dt_ns)))
        data_win = _dewow(data_win, win_samp=win_dw)

    if agc_ns and agc_ns > 0:
        dt_ns = (twtt[1] - twtt[0]) if len(twtt) >= 2 else 1.0
        win_agc = max(1, int(round(agc_ns / dt_ns)))
        data_win = _agc(data_win, win_samp=win_agc)

    if gauss_sigma > 0:
        data_win = _gaussian_blur(data_win, sigma=gauss_sigma)

    if unsharp_sigma > 0 and unsharp_amount != 0:
        data_win = _unsharp_mask(
            data_win, sigma=unsharp_sigma, amount=unsharp_amount)

    # --- Ejes ---
    # Asumimos 44 trazas por metro (puedes parametrizar si lo necesitas)
    profilePos = np.arange(data.shape[1]) / 44.0
    if len(profilePos) >= 4:
        dx = profilePos[3] - profilePos[2]
    elif len(profilePos) >= 2:
        dx = profilePos[1] - profilePos[0]
    else:
        dx = 0.0

    if len(twtt_win) >= 4:
        dt = twtt_win[3] - twtt_win[2]
    elif len(twtt_win) >= 2:
        dt = twtt_win[1] - twtt_win[0]
    else:
        dt = 0.0

    # --- Intensidad ---
    if intensity_mode.startswith("Contraste"):
        stdcont = float(np.nanmax(np.abs(data_win)))
        vmin = -stdcont / float(contrast if contrast else 3.0)
        vmax = stdcont / float(contrast if contrast else 3.0)
    else:
        pmin_eff = 2.0 if pmin is None else pmin
        pmax_eff = 98.0 if pmax is None else pmax
        vmin = np.percentile(data_win, pmin_eff)
        vmax = np.percentile(data_win, pmax_eff)
        if vmin == vmax:
            stdcont = float(np.nanmax(np.abs(data_win)))
            vmin, vmax = -stdcont/3.0, stdcont/3.0

    # --- Dibujo ---
    fig, ax = plt.subplots()
    ax.imshow(
        data_win, cmap=cmap,
        extent=[profilePos[0] - dx/2.0,
                profilePos[-1] + dx/2.0,
                max(twtt_win) + dt/2.0,
                min(twtt_win) - dt/2.0],
        aspect="auto", vmin=vmin, vmax=vmax
    )

    ax.set_ylabel("Tiempo [ns]")
    ax.set_xlabel("Posición del perfil [m]")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    # Ventana vertical fija: [cero, cero+yrng] (arriba->abajo; superficie arriba)
    y_top = cero
    y_bot = min(cero + yrng, twtt[-1])
    ax.set_ylim(y_bot, y_top)

    # --- Conversiones relativas al NUEVO cero ---
    def t_ns_to_depth_cm_rel(t_ns):
        dt_rel = max(t_ns - cero, 0.0)
        return (velocidad * dt_rel / 2.0) * 100.0

    def depth_cm_rel_to_t_ns_abs(depth_cm):
        return cero + (2.0 * (depth_cm / 100.0)) / velocidad

    # Eje secundario en cm (desde cero)
    sec = ax.twinx()
    sec.set_ylim(ax.get_ylim())
    sec.set_yticks(ax.get_yticks())
    sec.set_yticklabels(
        [f"{t_ns_to_depth_cm_rel(t):.0f}" for t in ax.get_yticks()])
    sec.set_ylabel("Profundidad [cm] (desde cero)")

    # Líneas de profundidad y grosor (desde el nuevo cero)
    t_prof_abs = depth_cm_rel_to_t_ns_abs(profundidad)
    t_grosor_abs = depth_cm_rel_to_t_ns_abs(profundidad + grosor)

    y_min_vis, y_max_vis = min(ax.get_ylim()), max(ax.get_ylim())
    def visible(t): return (t >= y_min_vis) and (t <= y_max_vis)

    if visible(t_prof_abs):
        ax.axhline(y=t_prof_abs, linewidth=2.0)
    if visible(t_grosor_abs):
        ax.axhline(y=t_grosor_abs, linewidth=2.0, linestyle="--")

    st.pyplot(fig)
# def mostrar_radagrama(file_name, file_name_rad, profundidad, grosor, velocidad=0.1889, cero=7):
#     """
#     profundidad, grosor: en cm (medidos desde el nuevo cero)
#     velocidad: en m/ns (p.ej. 0.1889 m/ns)
#     cero: tiempo (ns) desde el cual se desea comenzar a mostrar (nuevo 0 de profundidad)
#     """
#     yrng = 25        # ventana vertical en ns por debajo de 'cero'
#     contrast = 3.0
#     color = "gray"

#     data_raw = readMALA(file_name, file_name_rad)
#     st.session_state['data_raw'] = data_raw
#     data = data_raw[0]

#     # Vector de tiempo (Two-Way Travel Time) en ns
#     twtt = np.linspace(
#         0, float(data_raw[1]["TIMEWINDOW"]), int(data_raw[1]['SAMPLES']))

#     # --- Recorte según 'cero' ---
#     i0 = int(np.searchsorted(twtt, cero, side="left"))
#     if i0 >= len(twtt):
#         st.warning(
#             "El valor 'cero' es mayor o igual al tiempo máximo del registro. No hay datos que mostrar.")
#         return

#     twtt_win = twtt[i0:]      # tiempos visibles (>= cero)
#     data_win = data[i0:, :]   # recorte de filas

#     # Eje X como distancia (m) asumiendo 44 trazas por metro
#     profilePos = np.arange(data.shape[1]) / 44.0
#     dx = (profilePos[3] - profilePos[2]) if data.shape[1] >= 4 else (
#         profilePos[1] - profilePos[0] if data.shape[1] >= 2 else 0.0)
#     dt = (twtt_win[3] - twtt_win[2]) if len(twtt_win) >= 4 else (
#         twtt_win[1] - twtt_win[0] if len(twtt_win) >= 2 else 0.0)

#     stdcont = np.nanmax(np.abs(data_win))

#     fig, ax = plt.subplots()

#     # Imagen (superficie arriba)
#     img = ax.imshow(
#         data_win, cmap=color,
#         extent=[profilePos[0] - dx/2.0,
#                 profilePos[-1] + dx/2.0,
#                 max(twtt_win) + dt/2.0,
#                 min(twtt_win) - dt/2.0],
#         aspect="auto",
#         vmin=-stdcont/contrast,
#         vmax=stdcont/contrast
#     )

#     ax.set_ylabel("Tiempo [ns]")
#     ax.set_xlabel("Posición del perfil [m]")
#     ax.xaxis.tick_top()
#     ax.xaxis.set_label_position('top')

#     # Ventana vertical: [cero, cero+yrng] (arriba->abajo)
#     y_top = cero
#     y_bot = min(cero + yrng, twtt[-1])
#     ax.set_ylim(y_bot, y_top)

#     # ===== Conversiones con respecto al NUEVO cero =====
#     # t(ns) -> profundidad(cm) relativa al nuevo cero:
#     #   Δt = max(t - cero, 0)
#     #   d = (v * Δt) / 2  [m]  => *100 para [cm]
#     def t_ns_to_depth_cm_rel(t_ns):
#         dt_rel = max(t_ns - cero, 0.0)
#         return (velocidad * dt_rel / 2.0) * 100.0

#     # profundidad(cm) relativa al nuevo cero -> tiempo(ns) absoluto para el eje:
#     #   Δt = (2 * d[m]) / v = (2 * (d_cm/100)) / v
#     #   t_abs = cero + Δt
#     def depth_cm_rel_to_t_ns_abs(depth_cm):
#         return cero + (2.0 * (depth_cm / 100.0)) / velocidad

#     # ===== EJE SECUNDARIO EN PROFUNDIDAD (cm, relativo a 'cero') =====
#     sec = ax.twinx()
#     sec.set_ylim(ax.get_ylim())
#     sec.set_yticks(ax.get_yticks())
#     sec.set_yticklabels(
#         [f"{t_ns_to_depth_cm_rel(tick):.0f}" for tick in ax.get_yticks()])
#     sec.set_ylabel("Profundidad [cm] (desde cero)")

#     # ===== LÍNEAS DE PROFUNDIDAD Y GROSOR (desde el nuevo cero) =====
#     t_prof_abs = depth_cm_rel_to_t_ns_abs(profundidad)
#     t_grosor_abs = depth_cm_rel_to_t_ns_abs(profundidad + grosor)

#     # Dibujar solo si caen dentro de la ventana mostrada
#     y_min_vis, y_max_vis = min(ax.get_ylim()), max(ax.get_ylim())

#     def visible(t):  # recuerda: y_min_vis < y < y_max_vis en valores numéricos
#         return (t >= y_min_vis) and (t <= y_max_vis)

#     if visible(t_prof_abs):
#         ax.axhline(y=t_prof_abs, linewidth=2.0)                 # profundidad
#     if visible(t_grosor_abs):
#         ax.axhline(y=t_grosor_abs, linewidth=2.0,
#                    linestyle="--")  # profundidad + grosor

#     st.pyplot(fig)


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
