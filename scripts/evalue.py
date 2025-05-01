import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import streamlit as st

name_modelo = "best_model.pth"


class ImprovedCNN(nn.Module):
    def __init__(self, dropout_rate=0.7):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((2, 2)),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 2 * 2, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        return self.fc(self.conv(x))


def load_model():
    model = ImprovedCNN()
    model.load_state_dict(torch.load(name_modelo, map_location="cpu"))
    return model


model = load_model()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def evaluar_imagen_completa(data, df_mapa, segment_width=44*2, stride=44*2, mc_iterations=50):
    # Preprocesamiento
    arr = data[0]
    df_img = pd.DataFrame(arr)
    tensor = torch.tensor(df_img.values.astype(float), dtype=torch.float32)
    mean, std = tensor.mean(), tensor.std()
    img = ((tensor - mean) / std).unsqueeze(0).unsqueeze(0)
    _, _, H, W = img.shape
    n_segments = max(1, (W - segment_width) // stride + 1)

    stats = []
    # Modo inferencia con dropout
    model.train()
    for j in range(n_segments):
        start, end = j * stride, j * stride + segment_width
        seg = img[:, :, :, start:end]
        if seg.shape[3] < segment_width:
            pad = segment_width - seg.shape[3]
            seg = torch.cat([seg, torch.zeros(1, 1, H, pad)], dim=3)

        # Predicción puntual
        with torch.no_grad():
            out0 = model(seg)
            prob0 = torch.softmax(out0, dim=1)[0].cpu().numpy()

        # Monte Carlo Dropout
        mc = []
        with torch.no_grad():
            for _ in range(mc_iterations):
                mc.append(torch.softmax(model(seg), dim=1)[0].cpu().numpy())
        mc = np.stack(mc)
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
            'Prob_no_asbesto': prob0[0],
            'Prob_asbesto': prob0[1],
            'MC_Mean_no_asb': mean_mc[0],
            'MC_Mean_asb': mean_mc[1],
            'MC_Std_no_asb': std_mc[0],
            'MC_Std_asb': std_mc[1],
            'MC_P2.5_no_asb': p025[0],
            'MC_P97.5_no_asb': p975[0],
            'MC_P2.5_asb': p025[1],
            'MC_P97.5_asb': p975[1],
        })

    model.eval()
    # Construir df y merged_segments con solo confianza == 1
    df_stats = pd.DataFrame(stats)
    df_map = df_mapa[['ID', 'Latitud', 'NS', 'Longitud', 'EW']].copy()
    df_map['ID'] = (df_map['ID'].astype(int) // 44)
    df_map = df_map.drop_duplicates('ID')
    df_final = df_stats.merge(
        df_map, left_on='Segmento', right_on='ID', how='left').drop(columns=['ID'])

    merged_segments = [
        ((row.Segmento)*stride, (row.Segmento)*stride+segment_width)
        for _, row in df_stats[df_stats.Predicción_confianza == 1].iterrows()
    ]

    return merged_segments, df_final
