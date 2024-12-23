import torch
import torch.nn as nn
import numpy as np

# 4. Crear el modelo


class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            # Ajustar al tamaño final de la salida
            nn.Linear(32 * 61 * 61, 128),
            nn.ReLU(),
            nn.Linear(128, 2)  # 2 clases
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        return x


# Asegúrate de que el modelo se inicialice antes de cargar los pesos
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleCNN().to(device)

# Cargar los pesos entrenados
model.load_state_dict(torch.load("scripts\modelo_ladrillo.pth"))
model.eval()

# Preprocesar la matriz de test


def preprocess_test_matrix(test_matrix):
    """
    Normaliza y ajusta la matriz de test para la evaluación.

    Args:
        test_matrix (np.ndarray or torch.Tensor): Matriz de test.

    Returns:
        torch.Tensor: Matriz normalizada lista para evaluación.
    """
    # Convertir a tensor si es necesario
    if isinstance(test_matrix, np.ndarray):
        test_matrix = torch.tensor(test_matrix, dtype=torch.float32)

    # Normalizar (igual que en el entrenamiento)
    test_matrix = (test_matrix - test_matrix.mean()) / test_matrix.std()

    # Añadir dimensión de canal para PyTorch (N, C, H, W)
    test_matrix = test_matrix.unsqueeze(0).unsqueeze(0)  # Añade batch y canal
    return test_matrix

# Evaluar la matriz


def evaluate_test_matrix(test_matrix, model, device):
    """
    Evalúa una matriz con el modelo entrenado y retorna las predicciones.

    Args:
        test_matrix (torch.Tensor): Matriz preprocesada.
        model (nn.Module): Modelo entrenado.
        device (torch.device): Dispositivo para la evaluación.

    Returns:
        torch.Tensor: Predicción de la clase.
    """
    model.eval()
    with torch.no_grad():
        test_matrix = test_matrix.to(device)
        outputs = model(test_matrix)
        _, predicted = torch.max(outputs, 1)  # Clase con mayor probabilidad
    return predicted.cpu().item()


def evaluar_imagen(df):
    print(df)
    # Preprocesar la matriz de test
    test_tensor = preprocess_test_matrix(df)

    # Configurar dispositivo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Evaluar la matriz
    prediction = evaluate_test_matrix(test_tensor, model, device)

    # Mostrar el resultado
    # Ajusta según las etiquetas
    class_labels = {0: "Ladrillo", 1: "No Ladrillo"}
    print(f"Predicción: {class_labels[prediction]}")
    return class_labels[prediction]
