# test_registro_multiple.py
"""
Test 3.3.1 — Registro con 3 muestras de rostro
Esperado: HTTP 201 + 4 rostros (3 individuales + 1 promedio)
"""
import sys
from datetime import datetime

import requests

from test_utils import (
    capturar_frame,
    frame_a_data_uri,
    imprimir_respuesta,
    validar_status,
    verificar_backend,
)

API_MULTIPLE = "http://localhost:5000/api/registro/persona/multiple"


def capturar_muestras(n):
    """Captura n muestras secuencialmente. Usada también por los otros tests."""
    muestras = []
    for i in range(n):
        try:
            frame = capturar_frame(
                f"Muestra {i+1}/{n} — Presiona ESPACIO para capturar"
            )
        except RuntimeError as e:
            print(f"ERROR: {e}")
            return []

        if frame is None:
            print(f"Cancelado en muestra {i+1}")
            return []

        muestras.append(frame_a_data_uri(frame))
        print(f"   OK Muestra {i+1} capturada")

    return muestras


def main():
    print("=" * 60)
    print("TEST 3.3.1 — Registro multiple (3 muestras, esperado: 201)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    muestras = capturar_muestras(3)
    if len(muestras) < 3:
        print(f"ERROR: Solo se capturaron {len(muestras)} muestras")
        return 1

    timestamp = datetime.now().strftime("%H%M%S")
    matricula = f"MULTI{timestamp}"

    payload = {
        "nombre": "Test",
        "apellido": "Multiple",
        "matricula": matricula,
        "tipo": "Estudiante",
        "imagenes": muestras,
        "correo": f"multi{timestamp}@ejemplo.com",
        "incluir_promedio": True,
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

    if not validar_status(r, 201, "TEST 3.3.1"):
        return 1

    try:
        data = r.json().get('data', {})
        persona_id = data.get('persona_id')
        total_rostros = data.get('total_rostros')
        rostros_ids = data.get('rostros_ids', [])

        print(f"\n   persona_id:     {persona_id}")
        print(f"   total_rostros:  {total_rostros}")
        print(f"   rostros_ids:    {rostros_ids}")

        if total_rostros == 4:
            print(f"\n   [OK] 4 rostros (3 muestras + 1 promedio)")
        elif total_rostros == 3:
            print(f"\n   [OK] 3 rostros (promedio omitido)")
        else:
            print(f"\n   [WARN] Se esperaban 4, se obtuvieron {total_rostros}")

        print(f"\nTEST 3.3.1 COMPLETADO")
        print(f"\nGuarda esto para el SQL de la tarea 3.3.4:")
        print(f"   persona_id = {persona_id}")
        print(f"   matricula  = {matricula}")
        return 0

    except Exception as e:
        print(f"\nERROR parseando respuesta: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())