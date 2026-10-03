# test_registro_multiple_error.py
"""
Test 3.3.3 — Registro con menos de 3 muestras
Esperado: HTTP 400 con mensaje claro
"""
import sys
from datetime import datetime

import requests

from test_utils import (
    imprimir_respuesta,
    validar_status,
    verificar_backend,
)
from test_registro_multiple import capturar_muestras

API_MULTIPLE = "http://localhost:5000/api/registro/persona/multiple"


def main():
    print("=" * 60)
    print("TEST 3.3.3 — Menos de 3 muestras (esperado: 400)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    print("\nNOTA: este test captura solo 2 muestras para provocar el error")
    muestras = capturar_muestras(2)
    if len(muestras) < 2:
        print(f"ERROR: Solo se capturaron {len(muestras)} muestras")
        return 1

    timestamp = datetime.now().strftime("%H%M%S")
    payload = {
        "nombre": "Test",
        "apellido": "PocasMuestras",
        "matricula": f"ERR{timestamp}",
        "tipo": "Estudiante",
        "imagenes": muestras,   # solo 2
    }

    print(f"\n-> POST {API_MULTIPLE}")
    print(f"-> muestras enviadas: {len(muestras)} (se requieren 3)")

    try:
        r = requests.post(API_MULTIPLE, json=payload, timeout=60)
    except Exception as e:
        print(f"\nERROR en la peticion: {e}")
        return 1

    imprimir_respuesta(r)

    if not validar_status(r, 400, "TEST 3.3.3"):
        return 1

    try:
        error = r.json().get('error', '')
        print(f"\n   Mensaje del backend: '{error}'")
    except Exception:
        pass

    print(f"\nTEST 3.3.3 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())