import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

velocidad = 0.1889


def mostrar_radagrama_cajas_aleatorias(
    data_raw,
    *,
    box_height_rows=4,      # alto de la caja en filas
    box_width_cols=132,     # ancho de la caja en columnas
    prob=0.5,               # probabilidad de pintar cada caja
    max_rows=40,            # nº de filas a mostrar DESDE min_time_ns hacia abajo
    # solo mostrar/dibujar por debajo de este tiempo (ns)
    min_time_ns=7.5,
    color="red",
    alpha=0.30
):
    """
    Dibuja el radargrama con la misma convención de ejes que usas,
    y superpone cajas (box_width_cols x box_height_rows) de forma aleatoria,
    únicamente por debajo de min_time_ns. El recorte vertical visible abarca
    como máximo 'max_rows' filas a partir de min_time_ns.
    """
    contrast = 3.0
    cmap = "gray"

    data = data_raw[0]  # matriz HxW
    info = data_raw[1]

    # Ejes físicos (tiempo y posición) como en tu gráfico original
    twtt = np.linspace(0, float(info["TIMEWINDOW"]), int(info["SAMPLES"]))
    profilePos = float(info["DISTANCE INTERVAL"]) * np.arange(0, data.shape[1])

    dx = profilePos[3] - profilePos[2]
    dt = twtt[3] - twtt[2]
    stdcont = np.nanmax(np.abs(data)[:])

    # --------- Render base del radargrama (igual a tu función) ---------
    fig, ax = plt.subplots()
    ax.imshow(
        data,
        cmap=cmap,
        extent=[
            float(np.min(profilePos)) - dx / 2.0,
            float(np.max(profilePos)) + dx / 2.0,
            float(np.max(twtt)) + dt / 2.0,
            float(np.min(twtt)) - dt / 2.0,
        ],
        aspect="auto",
        vmin=-stdcont / contrast,
        vmax=stdcont / contrast,
    )

    # --------- Segmentación a partir de min_time_ns ---------
    H, W = data.shape
    # fila de inicio (primera con tiempo >= min_time_ns)
    r_start = int(np.searchsorted(twtt, float(min_time_ns), side="left"))
    r_end = H  # límite inferior visible
    if r_start >= r_end:
        # si no hay filas suficientes bajo min_time_ns, no dibujamos nada
        ax.set_ylabel("Tiempo [ns]")
        ax.set_xlabel("Posición del perfil [m]")
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        # centra la vista alrededor de min_time_ns (ventana de 20 ns por defecto)
        y_top = float(min_time_ns)
        y_bot = min(y_top + 20.0, float(twtt[-1]))
        ax.set_ylim(y_bot, y_top)
        ax.set_xlim([float(np.min(profilePos)), float(np.max(profilePos))])
        st.pyplot(fig)
        return

    # Rejilla de cajas solo dentro de [r_start, r_end)
    h = int(box_height_rows)
    w = int(box_width_cols)
    rng = np.random.default_rng(None)

    for r0 in range(r_start, r_end, h):
        r1 = min(r0 + h, r_end)
        y_top_ns = twtt[r0]
        y_bot_ns = twtt[r1 - 1] if (r1 - 1) < len(twtt) else twtt[-1]

        for c0 in range(0, W, w):
            c1 = min(c0 + w, W)
            if rng.random() >= float(prob):
                continue

            # Caja en coordenadas físicas (m/ns), alineada con tu extent
            x_left = profilePos[c0] - dx / 2.0
            x_right = profilePos[c1 - 1] + dx / 2.0
            width_m = x_right - x_left
            height_ns = y_bot_ns - y_top_ns

            rect = plt.Rectangle(
                (x_left, y_top_ns),
                width_m,
                height_ns,
                linewidth=1.5,
                edgecolor=color,
                facecolor=color,
                alpha=alpha,
            )
            ax.add_patch(rect)

    # --------- Ejes exactamente como los tienes ---------
    ax.set_ylabel("Tiempo [ns]")
    ax.set_xlabel("Posición del perfil [m]")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    # Ventana vertical: desde min_time_ns hasta min_time_ns+20 ns (o lo que alcance el registro)
    y_top = float(min_time_ns)
    y_bot = min(y_top + 20.0, float(twtt[-1]))
    ax.set_ylim(y_bot, y_top)

    ax.set_xlim([float(np.min(profilePos)), float(np.max(profilePos))])

    st.pyplot(fig)
