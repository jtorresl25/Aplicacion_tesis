# scripts/evalue_vertical.py
from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# ===================== Config por defecto (clon de tu job) =====================
NAME_MODELO = "best_model_export_v.pth"

# Preprocesamiento
# ns a recortar desde arriba (aquí no lo aplicamos por falta de NS_PER_SAMPLE)
SET_ZERO_NS = 0.0
# NO normalizar, para replicar exactamente el dataset de segmentos
APPLY_ZSCORE = False

# Segmentación vertical
VERT_MAX_ROWS = 40         # usar solo primeras 40 filas
VERT_HEIGHT = 8          # alto del parche
VERT_STRIDE = 8          # salto vertical (sin solape)
# 1-based -> usamos SOLO la banda vertical #5 (índice 4)
ASBESTO_VERT_IDX = 5

# Segmentación horizontal
HORIZ_WIDTH = 3 * 44     # ancho del parche (columnas)
HORIZ_STRIDE = HORIZ_WIDTH  # salto horizontal (sin solape)

# MC-Dropout
MC_ITERATIONS = 25
MC_POSITIVE_THRESHOLD = 0.5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ===================== Modelo (pooling solo en ancho) =====================
class ImprovedCNN(nn.Module):
    def __init__(self, dropout: float = 0.5):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(
                16), nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2)),
            nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(
                32), nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2)),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(
                64), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64*4*4, 256), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(256, 128), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(128, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.classifier(x)
        return x


def _extract_state_dict(blob) -> Dict[str, torch.Tensor]:
    if isinstance(blob, dict):
        if 'state_dict' in blob and isinstance(blob['state_dict'], dict):
            sd = blob['state_dict']
        elif 'model' in blob and isinstance(blob['model'], dict):
            sd = blob['model']
        else:
            sd = {k: v for k, v in blob.items() if isinstance(v, torch.Tensor)}
            if not sd:
                sd = blob
    else:
        raise TypeError(
            "El archivo de pesos no es un diccionario reconocible.")

    return {k.replace('module.', ''): v for k, v in sd.items()}


def load_model(weights_path: str | Path = NAME_MODELO) -> nn.Module:
    model = ImprovedCNN()
    weights_path = Path(weights_path)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de pesos: {weights_path}")
    checkpoint = torch.load(weights_path, map_location="cpu")
    state_dict = _extract_state_dict(checkpoint)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing or unexpected:
        # deja caer excepción con detalle si no calza
        model.load_state_dict(state_dict, strict=True)
    model.to(DEVICE).eval()
    return model


def _maybe_zscore(arr: np.ndarray) -> np.ndarray:
    if not APPLY_ZSCORE:
        return arr
    m, s = arr.mean(), arr.std()
    s = 1.0 if (not np.isfinite(s) or s < 1e-8) else s
    return (arr - m) / s


@torch.inference_mode()
def evaluar_imagen_vertical(
    data,
    df_mapa: pd.DataFrame | None = None,
    *,
    weights_path: str | Path = NAME_MODELO,
    vert_max_rows: int = VERT_MAX_ROWS,
    vert_height: int = VERT_HEIGHT,
    vert_stride: int = VERT_STRIDE,
    horiz_width: int = HORIZ_WIDTH,
    horiz_stride: int = HORIZ_STRIDE,
    asbesto_vert_idx: int = ASBESTO_VERT_IDX,   # 1-based
    mc_iterations: int = MC_ITERATIONS,
    positive_threshold: float = MC_POSITIVE_THRESHOLD,
):
    """
    Replica la rejilla de segmentos de tu pipeline:
      - Recorta a las primeras `vert_max_rows` filas.
      - Ventanas verticales de tamaño `vert_height`, stride `vert_stride` SIN padding.
      - Toma SOLO la banda vertical #asbesto_vert_idx (1-based).
      - Ventanas horizontales de `horiz_width`, stride `horiz_stride` SIN padding.
    """
    # --- extrae matriz [H,W] ---
    arr = data[0] if isinstance(data, (list, tuple)) else data
    if isinstance(arr, tuple) and len(arr) == 2 and isinstance(arr[0], np.ndarray):
        arr = arr[0]
    assert isinstance(
        arr, np.ndarray) and arr.ndim == 2, "Se espera un radargrama 2D [H,W]."

    # --- recorte a primeras N filas ---
    H0, W0 = arr.shape
    if vert_max_rows is not None:
        arr = arr[:min(int(vert_max_rows), H0), :]

    # --- normalización (si se activa explícitamente) ---
    arr = _maybe_zscore(arr).astype(np.float32, copy=False)
    arr = np.ascontiguousarray(arr)

    t = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # [1,1,H,W] float32
    H, W = int(t.shape[-2]), int(t.shape[-1])

    # --- modelo ---
    model = load_model(weights_path)

    # --- calcula nº de bandas verticales sin padding ---
    # solo ventanas completas
    if vert_height <= 0 or vert_stride <= 0:
        raise ValueError("vert_height y vert_stride deben ser > 0")
    if horiz_width <= 0 or horiz_stride <= 0:
        raise ValueError("horiz_width y horiz_stride deben ser > 0")

    n_vert = (H - vert_height) // vert_stride + 1 if H >= vert_height else 0
    n_horz = (W - horiz_width) // horiz_stride + 1 if W >= horiz_width else 0

    # índice 0-based de la banda solicitada
    iv_target = int(asbesto_vert_idx) - 1
    if not (0 <= iv_target < n_vert):
        # si no existe esa banda con el H actual, no hay parches
        return [], pd.DataFrame(), pd.DataFrame()

    # --- bucle SOLO por la banda iv_target, sin padding ---
    stats_rows: List[dict] = []
    df_distribucion = pd.DataFrame()
    positive_boxes: List[Tuple[int, int, int, int]] = []

    # progreso opcional
    progress = None
    try:
        import streamlit as st  # noqa
        progress = st.progress(0.0, text="Evaluando parches (vertical)…")
    except Exception:
        pass

    total = n_horz
    for ih in range(n_horz):
        r0 = iv_target * vert_stride
        r1 = r0 + vert_height
        c0 = ih * horiz_stride
        c1 = c0 + horiz_width
        # ventanas completas garantizadas por n_horz/n_vert, así que no hay padding

        patch = t[:, :, r0:r1, c0:c1].to(DEVICE, non_blocking=True)

        # predicción puntual
        out0 = model(patch)
        prob0 = torch.softmax(out0, dim=1)[0].detach().cpu().numpy()

        # MC-Dropout
        for m in model.modules():
            if isinstance(m, (nn.Dropout, nn.Dropout1d, nn.Dropout2d)):
                m.train()
        rep = patch.repeat(int(mc_iterations), 1, 1, 1)
        out = model(rep)
        mc = torch.softmax(out, dim=1).detach().cpu().numpy()

        mean_mc = mc.mean(axis=0)
        std_mc = mc.std(axis=0)
        p025, p975 = np.percentile(mc, [2.5, 97.5], axis=0)

        if p975[0] < p025[1]:
            conf_pred = 1
        elif p975[1] < p025[0]:
            conf_pred = 0
        else:
            conf_pred = 2

        stats_rows.append({
            'IdxV': int(iv_target), 'IdxH': int(ih),
            'r0': int(r0), 'r1': int(r1), 'c0': int(c0), 'c1': int(c1),
            'Predicción_confianza': int(conf_pred),
            'Prob_no_asbesto': float(prob0[0]),
            'Prob_asbesto': float(prob0[1]),
            'MC_Mean_no_asb': float(mean_mc[0]),
            'MC_Mean_asb': float(mean_mc[1]),
            'MC_Std_no_asb': float(std_mc[0]),
            'MC_Std_asb': float(std_mc[1]),
            'MC_P2.5_no_asb': float(p025[0]),
            'MC_P97.5_no_asb': float(p975[0]),
            'MC_P2.5_asb': float(p025[1]),
            'MC_P97.5_asb': float(p975[1]),
        })

        df_mc = pd.DataFrame(mc, columns=['no_asb', 'asb'])
        df_mc['IdxV'] = int(iv_target)
        df_mc['IdxH'] = int(ih)
        df_distribucion = pd.concat(
            [df_distribucion, df_mc], axis=0, ignore_index=True)

        if float(mean_mc[1]) >= float(positive_threshold):
            positive_boxes.append((int(r0), int(r1), int(c0), int(c1)))

        if progress is not None:
            progress.progress((ih + 1) / total,
                              text=f"Evaluando parche {ih+1}/{total}")

    model.eval()

    df_final = pd.DataFrame(stats_rows)

    # --- merge de coordenadas por columna central del parche ---
    if df_mapa is not None and not df_mapa.empty and all(
        col in df_mapa.columns for col in ['ID', 'Latitud', 'NS', 'Longitud', 'EW']
    ):
        df_final['Col_centro'] = (
            (df_final['c0'] + df_final['c1']) // 2).astype('int64', copy=False)
        df_final['Metro'] = (df_final['Col_centro'] //
                             44).astype('int64', copy=False)

        df_map = df_mapa[['ID', 'Latitud', 'NS', 'Longitud', 'EW']].copy()
        df_map['Metro'] = (df_map['ID'].astype('int64') // 44)
        df_map = df_map.drop_duplicates('Metro')

        df_final = df_final.merge(df_map.drop(
            columns=['ID']), on='Metro', how='left').drop(columns=['Metro'])
    else:
        df_final['Col_centro'] = (
            (df_final['c0'] + df_final['c1']) // 2).astype('int64', copy=False)

    return positive_boxes, df_final, df_distribucion
