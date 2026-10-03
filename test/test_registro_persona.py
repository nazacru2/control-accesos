# test_registro_persona.py
"""
Test 2.3.1 — Registro exitoso de persona
Esperado: HTTP 201 + datos de la persona registrada
"""
import sys
from datetime import datetime

from test_utils import (
    capturar_frame,
    frame_a_data_uri,
    post_registro,
    imprimir_respuesta,
    validar_status,
    verificar_backend,
)


def main():
    print("=" * 60)
    print("TEST 2.3.1 — Registro exitoso (esperado: 201)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    # Capturar rostro
    try:
        frame = capturar_frame()
    except RuntimeError as e:
        print(f"\n {e}")
        return 1

    if frame is None:
        print("\n  Captura cancelada por el usuario")
        return 1

    # Generar matrícula única con timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    matricula = f"TEST{timestamp}"

    payload = {
        "nombre": "Test",
        "apellido": "Exitoso",
        "matricula": matricula,
        "tipo": "Estudiante",
        "imagen": frame_a_data_uri(frame),
        "correo": f"test{timestamp}@ejemplo.com",
    }

    print(f"\n→ POST /api/registro/persona")
    print(f"→ matrícula: {matricula}")

    try:
        r = post_registro(payload)
    except Exception as e:
        print(f"\n Error en la petición: {e}")
        return 1

    imprimir_respuesta(r)

    if not validar_status(r, 201, "TEST 2.3.1"):
        return 1

    # Verificaciones adicionales del contenido
    try:
        data = r.json().get('data', {})
        persona_id = data.get('persona_id')
        rostro_id = data.get('rostro_id')
        matricula_devuelta = data.get('matricula')

        print(f"\n   persona_id:  {persona_id}")
        print(f"   rostro_id:   {rostro_id}")
        print(f"   matrícula:   {matricula_devuelta}")

        if not persona_id or not rostro_id:
            print("\n  La respuesta no incluye persona_id/rostro_id")
            return 1
    except Exception as e:
        print(f"\n  Error parseando respuesta: {e}")
        return 1

    print(f"\n TEST 2.3.1 COMPLETADO")
    print(f"   Guarda esta matrícula para el siguiente test: {matricula}")
    return 0


if __name__ == '__main__':
    sys.exit(main())