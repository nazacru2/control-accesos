# test_registro_multiple_5.py
"""
Test 3.3.2 — Registro con 5 muestras de rostro
Esperado: HTTP 201 + 5 rostros (promedio omitido por MAX_SAMPLES_PER_PERSON=5)
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
    print("TEST 3.3.2 — Registro multiple (5 muestras, esperado: 201)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    muestras = capturar_muestras(5)
    if len(muestras) < 5:
        print(f"ERROR: Solo se capturaron {len(muestras)} muestras")
        return 1

    timestamp = datetime.now().strftime("%H%M%S")
    matricula = f"MULTI5{timestamp}"

    payload = {
        "nombre": "Test",
        "apellido": "CincoMuestras",
        "matricula": matricula,
        "tipo": "Estudiante",
        "imagenes": muestras,
        "incluir_promedio": True,   # se omitira por limite
    }

    print(f"\n-> POST {API_MULTIPLE}")
    print(f"-> matricula: {matricula}")
    print(f"-> muestras enviadas: {len(muestras)}")

    try:
        r = requests.post(API_MULTIPLE, json=payload, timeout=300)
    except Exception as e:
        print(f"\nERROR en la peticion: {e}")
        return 1

    imprimir_respuesta(r)

    if not validar_status(r, 201, "TEST 3.3.2"):
        return 1

    try:
        data = r.json().get('data', {})
        persona_id = data.get('persona_id')
        total_rostros = data.get('total_rostros')

        print(f"\n   persona_id:     {persona_id}")
        print(f"   total_rostros:  {total_rostros}")

        if total_rostros == 5:
            print(f"\n   [OK] 5 rostros (promedio omitido por limite MAX=5)")
        else:
            print(f"\n   [WARN] Se esperaban 5, se obtuvieron {total_rostros}")

        print(f"\nTEST 3.3.2 COMPLETADO")
        print(f"\nGuarda esto para el SQL de la tarea 3.3.4:")
        print(f"   persona_id = {persona_id}")
        print(f"   matricula  = {matricula}")
        return 0

    except Exception as e:
        print(f"\nERROR parseando respuesta: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())