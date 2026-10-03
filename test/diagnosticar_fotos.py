"""
diagnosticar_fotos.py
Corre EXACTAMENTE la misma detección que usa el backend
(haarcascade_frontalface_default.xml, detectMultiScale(gray, 1.1, 4))
sobre tus fotos de validación, de dos formas:

  A) Leyendo el archivo directo con cv2.imread()
  B) Simulando el mismo camino que sigue la petición HTTP real:
     archivo -> bytes -> base64 -> base64 decode -> np.frombuffer -> cv2.imdecode

Si A) detecta un rostro pero B) no, hay un bug real en el round-trip.
Si NINGUNA de las dos detecta nada, el problema está en la foto en sí
(ángulo, iluminación, resolución).

Uso:
    python diagnosticar_fotos.py fotos7/p3_d.jpg fotos7/p5_d.jpg
    python diagnosticar_fotos.py fotos7/*.jpg          (en PowerShell: Get-ChildItem fotos7/*.jpg | % { $_.FullName })
"""

import base64
import sys

import cv2
import numpy as np

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detectar(gray):
    return face_cascade.detectMultiScale(gray, 1.1, 4)


def diagnosticar(ruta):
    print(f"\n{'=' * 60}")
    print(f"Archivo: {ruta}")

    # --- A) Lectura directa ---
    img_directa = cv2.imread(ruta)
    if img_directa is None:
        print("   [A] cv2.imread() -> None (archivo no se pudo leer/decodificar)")
        return
    alto, ancho = img_directa.shape[:2]
    print(f"   Dimensiones: {ancho}x{alto} px")

    gray_directa = cv2.cvtColor(img_directa, cv2.COLOR_BGR2GRAY)
    rostros_directa = detectar(gray_directa)
    print(f"   [A] Lectura directa (cv2.imread):      {len(rostros_directa)} rostro(s) detectado(s)")

    # --- B) Round-trip idéntico al de la API (archivo -> base64 -> imdecode) ---
    with open(ruta, "rb") as f:
        crudo = f.read()

    b64 = base64.b64encode(crudo).decode("utf-8")
    # (el servidor primero recorta el prefijo "data:image/...;base64," si existe;
    # aquí no lo agregamos, así que no hace falta recortarlo)
    decodificado = base64.b64decode(b64)
    np_arr = np.frombuffer(decodificado, np.uint8)
    img_b64 = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img_b64 is None:
        print("   [B] Round-trip base64 -> cv2.imdecode() -> None (¡aquí está el bug!)")
        return

    gray_b64 = cv2.cvtColor(img_b64, cv2.COLOR_BGR2GRAY)
    rostros_b64 = detectar(gray_b64)
    print(f"   [B] Round-trip base64 (igual que la API): {len(rostros_b64)} rostro(s) detectado(s)")

    if len(rostros_directa) != len(rostros_b64):
        print("   >>> DISCREPANCIA entre A y B: hay un bug en el round-trip, no es la foto.")
    elif len(rostros_directa) == 0:
        print("   >>> Ninguna de las dos detecta rostro: el problema es la foto (ángulo/luz/resolución).")
    else:
        print("   >>> Ambas detectan correctamente: esta foto debería funcionar en /api/validacion.")


if __name__ == "__main__":
    rutas = sys.argv[1:]
    if not rutas:
        print("Uso: python diagnosticar_fotos.py archivo1.jpg [archivo2.jpg ...]")
        sys.exit(1)

    for ruta in rutas:
        diagnosticar(ruta)