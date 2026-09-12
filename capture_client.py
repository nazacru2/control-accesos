"""
capture_client.py
Captura un frame desde la cámara conectada al HOST (Windows) y lo envía
al backend vía POST /api/capture como imagen en base64.

Uso:
    python capture_client.py
    python capture_client.py --index 0 --url http://localhost:5000/api/capture
"""

import argparse
import base64
import sys

import cv2
import requests


def capturar_frame(camera_index: int = 0):
    """Abre la cámara con DirectShow (necesario en Windows) y captura un frame."""
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError(
            f"No se pudo abrir la cámara con índice {camera_index}. "
            "Verifica el índice o los permisos de cámara en Windows."
        )

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("La cámara se abrió pero no se pudo leer un frame.")

    return frame


def frame_a_base64(frame) -> str:
    """Codifica un frame de OpenCV (BGR) a JPEG y luego a base64 (string)."""
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("No se pudo codificar el frame a JPEG.")
    return base64.b64encode(buffer).decode("utf-8")


def enviar_al_backend(imagen_b64: str, url: str) -> dict:
    """Envía la imagen en base64 al endpoint /api/capture del backend."""
    payload = {"image": f"data:image/jpeg;base64,{imagen_b64}"}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Captura y envía un frame al backend.")
    parser.add_argument("--index", type=int, default=0, help="Índice de la cámara (default: 0)")
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:5000/api/capture",
        help="URL del endpoint de captura del backend",
    )
    args = parser.parse_args()

    try:
        print(f"Abriendo cámara (índice {args.index})...")
        frame = capturar_frame(args.index)
        print(f"Frame capturado. Dimensiones: {frame.shape}")

        print("Codificando a base64...")
        imagen_b64 = frame_a_base64(frame)

        print(f"Enviando a {args.url} ...")
        resultado = enviar_al_backend(imagen_b64, args.url)
        print("Respuesta del backend:", resultado)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()