# test_registro_invalido.py
"""
Test 2.3.3 — Registro con imagen inválida
Esperado: HTTP 400
"""
import sys
from datetime import datetime

from test_utils import (
    post_registro,
    imprimir_respuesta,
    validar_status,
    verificar_backend,
)


def main():
    print("=" * 60)
    print("TEST 2.3.3 — Imagen inválida (esperado: 400)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    timestamp = datetime.now().strftime("%H%M%S")

    # Caso 1: base64 basura
    payload = {
        "nombre": "Invalido",
        "apellido": "Test",
        "matricula": f"INV{timestamp}",
        "tipo": "Estudiante",
        "imagen": "esto_no_es_una_imagen_base64_valida!!!",
    }

    print(f"\n→ Caso: cadena base64 inválida")
    print(f"→ POST /api/registro/persona")

    try:
        r = post_registro(payload, timeout=30)
    except Exception as e:
        print(f"\n Error en la petición: {e}")
        return 1

    imprimir_respuesta(r)

    if not validar_status(r, 400, "TEST 2.3.3"):
        return 1

    # Verificar mensaje de error
    try:
        error = r.json().get('error', '')
        print(f"\n   Mensaje: '{error}'")
    except Exception:
        pass

    print(f"\n TEST 2.3.3 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())