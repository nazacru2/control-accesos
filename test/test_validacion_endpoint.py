"""
test_validacion_endpoint.py
Prueba rápida de 7.3.3: POST /api/validacion con una foto real.
"""

import base64
import requests

BASE_URL = "http://localhost:5000/api"

def probar(ruta_foto):
    with open(ruta_foto, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        f"{BASE_URL}/validacion",
        json={"image": img_b64, "puerta": "Principal", "registrar_acceso": True},
        timeout=30,
    )
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    import sys
    ruta = sys.argv[1] if len(sys.argv) > 1 else "fotos/persona1_a.jpeg"
    probar(ruta)