"""
test_acceso_endpoint.py
Prueba rápida de 7.3.4: POST /api/acceso/registrar
"""

import requests

BASE_URL = "http://localhost:5000/api"

def probar(persona_id, rostro_id, exito=True, puerta="Principal"):
    response = requests.post(
        f"{BASE_URL}/acceso/registrar",
        json={
            "persona_id": persona_id,
            "rostro_id": rostro_id,
            "exito": exito,
            "puerta": puerta,
        },
        timeout=10,
    )
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    import sys
    persona_id = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rostro_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    probar(persona_id, rostro_id)