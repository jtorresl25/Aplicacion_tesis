import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import streamlit as st


class SimpleCNN(nn.Module):
    def __init__(self, dropout_rate=0.5):
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
# 2. Cargar el modelo entrenado (con caché para no cargar en cada interacción)


def load_model():
    model = SimpleCNN()
    model.load_state_dict(torch.load(
        "93.pth", map_location="cpu"))
    model.eval()  # Modo evaluación
    return model


model = load_model()

# Asegúrate de que el modelo se inicialice antes de cargar los pesos
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def evaluar_imagen_completa(data, segment_width=88, stride=88):
    # Asumimos que data es una lista y tomamos el primer elemento
    data = data[0]
    data = pd.DataFrame(data)
    # Convertir los datos a tensor y normalizar
    full_image = torch.tensor(data.values, dtype=torch.float32)
    mean = full_image.mean(dim=(0, 1), keepdim=True)
    std = full_image.std(dim=(0, 1), keepdim=True)
    full_image = (full_image - mean) / std

    # Añadir dimensión de canal (1 canal)
    full_image = full_image.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

    # Obtener dimensiones (se espera H = 256)
    _, _, H, W = full_image.shape
    print("Dimensiones de la imagen completa:", H, W)

    # Calcular el número de segmentos a lo largo de las columnas
    n_segments = (W - segment_width) // stride + 1
    print("Número de segmentos:", n_segments)

    predictions = []
    probabilities = []

    # Recorrer la imagen segmentándola por columnas
    for j in range(n_segments):
        start = j * stride
        end = start + segment_width
        segment = full_image[:, :, :, start:end]

        # Si el segmento es menor al ancho deseado, se rellena con ceros
        if segment.shape[3] < segment_width:
            padding = torch.zeros((1, 1, H, segment_width - segment.shape[3]))
            segment = torch.cat([segment, padding], dim=3)

        # Evaluar el segmento con el modelo
        with torch.no_grad():
            output = model(segment)
            prob = torch.softmax(output, dim=1)
            _, pred = torch.max(output, 1)

        predictions.append(pred.item())
        probabilities.append(prob.numpy()[0])

    # Crear una lista de segmentos donde la predicción fue 1.
    # Cada segmento se define por su posición de inicio y fin en la dimensión de columnas.
    detection_segments = []
    for j, pred in enumerate(predictions):
        if pred == 1:
            seg_start = j * stride
            seg_end = j * stride + segment_width
            detection_segments.append((seg_start, seg_end))

    # Fusionar segmentos contiguos (o que se solapan)
    merged_segments = []
    if detection_segments:
        current_start, current_end = detection_segments[0]
        for seg in detection_segments[1:]:
            seg_start, seg_end = seg
            # Si el inicio del siguiente segmento es menor o igual que el final del actual,
            # se consideran contiguos y se fusionan.
            if seg_start <= current_end:
                current_end = seg_end
            else:
                merged_segments.append((current_start, current_end))
                current_start, current_end = seg_start, seg_end
        merged_segments.append((current_start, current_end))

    print("Segmentos de detección:", merged_segments)
    prediction_array = np.array(predictions)
    probability_array = np.array(probabilities)
    return merged_segments
