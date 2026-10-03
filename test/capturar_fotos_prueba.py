"""
capturar_fotos_prueba.py
Captura N fotos consecutivas con la cámara del host y las guarda en
fotos7/ con el nombre que espera test_fase_7_1.py.

Uso:
    python capturar_fotos_prueba.py persona1          # 4 fotos: p1_a..p1_d
    python capturar_fotos_prueba.py persona1 --count 4
    python capturar_fotos_prueba.py desconocido --count 2 --prefix desconocido

Controles durante la captura:
    ESPACIO -> tomar la foto actual
    ESC     -> cancelar
"""

import argparse
import os
import string
import sys

import cv2

SUFIJOS = list(string.ascii_lowercase)  # a, b, c, d, ...


def capturar(nombre_base, cantidad, carpeta="fotos7"):
    os.makedirs(carpeta, exist_ok=True)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("No se pudo abrir la cámara (índice 0, CAP_DSHOW).")
        sys.exit(1)

    print(f"\nCapturando {cantidad} foto(s) para '{nombre_base}'.")
    print("Coloca el rostro frente a la cámara.")
    print("ESPACIO = capturar | ESC = cancelar\n")

    tomadas = 0
    while tomadas < cantidad:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo leer el frame de la cámara.")
            break

        vista = frame.copy()
        texto = f"Foto {tomadas + 1}/{cantidad} para '{nombre_base}' - ESPACIO=capturar, ESC=salir"
        cv2.putText(vista, texto, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Captura de fotos de prueba", vista)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            print("Cancelado por el usuario.")
            break
        if key == 32:  # ESPACIO
            sufijo = SUFIJOS[tomadas]
            ruta = os.path.join(carpeta, f"{nombre_base}_{sufijo}.jpg")
            cv2.imwrite(ruta, frame)
            print(f"   Guardada: {ruta}")
            tomadas += 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nListo: {tomadas}/{cantidad} fotos guardadas en {carpeta}/.")


def main():
    parser = argparse.ArgumentParser(description="Captura fotos de prueba para el Sprint 2.")
    parser.add_argument("nombre_base", help="Prefijo del archivo, ej. persona1, desconocido")
    parser.add_argument("--count", type=int, default=4, help="Cuántas fotos capturar (default: 4)")
    parser.add_argument("--carpeta", default="fotos7", help="Carpeta destino (default: fotos7)")
    args = parser.parse_args()

    if args.count > len(SUFIJOS):
        print(f"Máximo {len(SUFIJOS)} fotos por corrida.")
        sys.exit(1)

    capturar(args.nombre_base, args.count, args.carpeta)


if __name__ == "__main__":
    main()