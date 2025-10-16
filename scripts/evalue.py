import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

# ===================== Configuración básica =====================
# Cambia esto al nombre REAL de tu archivo de pesos:
# name_modelo = "92 [[54  0]  [ 5  6]].pth"
name_modelo = "best_model_export_h.pth"
n_metros = 3

# Dispositivo
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ===================== Arquitectura ORIGINAL (para que calcen los pesos) =====================
class ImprovedCNN(nn.Module):
    """
    Arquitectura original:
      - conv: 3 bloques conv+BN+ReLU, MaxPool en 1 y 2, AdaptiveAvgPool2d(2,2)
      - fc: Flatten -> Linear(64*2*2 -> 128) -> ReLU -> Dropout -> Linear(128 -> 2)
    """

    def __init__(self, dropout=0.5):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(
                16), nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(
                32), nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(
                64), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64*4*4, 256), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(256, 128), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


# ===================== Carga del modelo (robusta) =====================
def _extract_state_dict(blob):
    """
    Acepta:
      - dict con 'model' (y opc. 'optimizer', 'epoch'...)
      - dict con 'state_dict'
      - state_dict directo
    Limpia 'module.' si existe.
    """
    if isinstance(blob, dict):
        if 'state_dict' in blob and isinstance(blob['state_dict'], dict):
            sd = blob['state_dict']
        elif 'model' in blob and isinstance(blob['model'], dict):
            sd = blob['model']
        else:
            # podría ser ya un state_dict o un checkpoint atípico
            sd = {k: v for k, v in blob.items() if isinstance(v, torch.Tensor)}
            if not sd:  # si está vacío, intenta asumir blob completo como state_dict
                sd = blob
    else:
        raise TypeError(
            "El archivo de pesos no es un diccionario reconocible.")

    # quitar prefijo 'module.' si fue entrenado con DataParallel
    cleaned = {}
    for k, v in sd.items():
        new_k = k.replace('module.', '')
        cleaned[new_k] = v
    return cleaned


def load_model():
    """
    Carga los pesos al modelo original y lo envía a CPU/GPU en modo eval.
    Lanza un error legible si las llaves no coinciden.
    """
    model = ImprovedCNN()
    weights_path = Path(name_modelo)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de pesos: {weights_path}")

    checkpoint = torch.load(weights_path, map_location="cpu")
    state_dict = _extract_state_dict(checkpoint)

    # Intenta carga estricta; si falla, muestra llaves que faltan o sobran
    try:
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        # Si strict=False, validamos manualmente que no falten claves críticas
        if missing or unexpected:
            msg = []
            if missing:
                msg.append(f"Faltan llaves en state_dict: {missing}")
            if unexpected:
                msg.append(f"Llaves inesperadas en state_dict: {unexpected}")
            # Si faltan capas 'conv.' o 'fc.', es casi seguro que la arquitectura cambió.
            raise RuntimeError(" | ".join(msg))
    except RuntimeError as e:
        # Reintento con strict=True para un mensaje de PyTorch más detallado
        try:
            model.load_state_dict(state_dict, strict=True)
        except Exception as e2:
            raise RuntimeError(
                "No se pudieron cargar los pesos. Asegúrate de que la "
                "arquitectura sea la ORIGINAL con 'conv' y 'fc', y que el archivo .pth "
                "contenga un state_dict compatible.\n\n"
                f"Detalle del error: {e2}"
            ) from e

    model.to(device)
    model.eval()
    return model


# Instancia global (si usas Streamlit, puedes cachear esto con @st.cache_resource)
model = load_model()


# ===================== Utilidad para MC Dropout =====================
def _enable_dropout_only(m: nn.Module):
    """
    Activa SOLO las capas Dropout en modo train y deja el resto en eval.
    Evita desestabilizar BatchNorm durante MC-Dropout.
    """
    m.eval()
    for module in m.modules():
        if isinstance(module, (nn.Dropout, nn.Dropout1d, nn.Dropout2d)):
            module.train()


# ===================== Función principal (mantiene el mismo nombre) =====================
def evaluar_imagen_completa(data, df_mapa, segment_width=44*n_metros, stride=44*n_metros, mc_iterations=25):
    """
    Evalúa una imagen completa (radargrama) con ventanas deslizantes y MC-Dropout.

    Parámetros
    ----------
    data : list/tuple
        data[0] debe ser un array 2D (radargrama) de forma [H, W].
    df_mapa : pd.DataFrame
        Columnas requeridas: ['ID', 'Latitud', 'NS', 'Longitud', 'EW'].
        'ID' corresponde al índice de columna del radargrama (0..W-1).
    segment_width : int
        Ancho del segmento en columnas (por defecto 44*n_metros).
    stride : int
        Salto de la ventana en columnas (por defecto 44*n_metros).
    mc_iterations : int
        Número de muestras para MC-Dropout (25-50 recomendado).

    Retorna
    -------
    merged_segments : list[tuple]
        (col_start, col_end) de segmentos con MC_Mean_asb > 0.5.
    df_final : pd.DataFrame
        Estadísticos por segmento + coordenadas (si existen).
    df_distribucion : pd.DataFrame
        Distribución completa MC con columnas ['no_asb','asb','Segmento'].
    """
    # -------- Preprocesamiento --------
    arr = data[0]
    df_img = pd.DataFrame(arr)
    t = torch.tensor(df_img.values, dtype=torch.float32)  # [H, W]

    mean = t.mean()
    std = t.std()
    if not torch.isfinite(std) or std.item() < 1e-8:
        std = torch.tensor(1.0, dtype=torch.float32)

    img = ((t - mean) / std).unsqueeze(0).unsqueeze(0)  # [1,1,H,W]
    H, W = img.shape[-2], img.shape[-1]

    if stride <= 0:
        raise ValueError("stride debe ser > 0")
    n_segments = max(1, math.floor(max(W - segment_width, 0) / stride) + 1)

    # -------- Progreso en Streamlit (opcional) --------
    progress = None
    try:
        import streamlit as st  # noqa: F401
        progress = st.progress(0.0, text="Evaluando segmentos…")
    except Exception:
        pass

    stats = []
    df_distribucion = pd.DataFrame()

    for j in range(n_segments):
        start = j * stride
        end = start + segment_width
        seg = img[:, :, :, start:end]  # [1,1,H,segW]

        # Padding a la derecha si falta ancho
        segW = seg.shape[-1]
        if segW < segment_width:
            pad_r = segment_width - segW
            seg = F.pad(seg, (0, pad_r, 0, 0))  # (left,right,top,bottom)

        seg = seg.to(device)

        # ---- Predicción puntual (sin dropout) ----
        model.eval()
        with torch.inference_mode():
            out0 = model(seg)
            prob0 = torch.softmax(out0, dim=1)[0].detach().cpu().numpy()

        # ---- MC-Dropout (activando solo Dropout) ----
        _enable_dropout_only(model)
        seg_rep = seg.repeat(mc_iterations, 1, 1, 1)  # [mc,1,H,W]

        with torch.inference_mode():
            if device.type == "cuda":
                from torch.cuda.amp import autocast
                with autocast():
                    out = model(seg_rep)  # [mc,2]
            else:
                out = model(seg_rep)
            mc_probs = torch.softmax(
                out, dim=1).detach().cpu().numpy()  # [mc,2]

        # Estadísticos MC
        mc = mc_probs
        mean_mc = mc.mean(axis=0)
        std_mc = mc.std(axis=0)
        p025, p975 = np.percentile(mc, [2.5, 97.5], axis=0)

        # Lógica de intervalos
        if p975[0] < p025[1]:
            conf_pred = 1   # hay asbesto
        elif p975[1] < p025[0]:
            conf_pred = 0   # no hay asbesto
        else:
            conf_pred = 2   # inconcluso

        stats.append({
            'Segmento': j,
            'Predicción_confianza': conf_pred,
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

        # Guardar distribución completa por segmento
        df_mc = pd.DataFrame(mc, columns=['no_asb', 'asb'])
        df_mc['Segmento'] = j
        df_distribucion = pd.concat(
            [df_distribucion, df_mc], axis=0, ignore_index=True)

        if progress is not None:
            progress.progress((j + 1) / n_segments,
                              text=f"Evaluando segmento {j+1}/{n_segments}")

    # Restablecer eval
    model.eval()

    # -------- Construcción de df_final con coordenadas --------
    df_stats = pd.DataFrame(stats)

    # Mapa por metro (ID//44) y merge por "metro central" del segmento
    df_map = df_mapa[['ID', 'Latitud', 'NS', 'Longitud', 'EW']].copy()
    df_map['Metro'] = (df_map['ID'].astype(int) // 44)
    df_map = df_map.drop_duplicates('Metro')

    df_stats['Metro'] = (df_stats['Segmento'] * n_metros) + (n_metros // 2)

    df_final = df_stats.merge(
        df_map.drop(columns=['ID']),
        on='Metro',
        how='left'
    ).drop(columns=['Metro'])

    # -------- Segmentos positivos por media MC --------
    merged_segments = [
        (int(j * stride), int(j * stride + segment_width))
        for j, row in df_stats.iterrows()
        if row['MC_Mean_asb'] > 0.5
    ]

    return merged_segments, df_final, df_distribucion
