# test_registro_duplicado.py
"""
Test 2.3.2 — Registro con matrícula duplicada
Esperado: HTTP 409
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
    print("TEST 2.3.2 — Registro duplicado (esperado: 409)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    # Pedir la matrícula existente (o generar una y registrarla primero)
    print("\nOpciones:")
    print("  1. Usar una matrícula existente (debes registrarla antes)")
    print("  2. Registrar primero y luego intentar duplicar (recomendado)")

    matricula = input("\nMatrícula a duplicar (o ENTER para registrar una ahora): ").strip()

    if not matricula:
        # Registrar una nueva primero
        print("\n→ Registrando una nueva persona para luego duplicarla...")
        try:
            frame = capturar_frame("Captura para el primer registro")
        except RuntimeError as e:
            print(f" {e}")
            return 1

        if frame is None:
            print("  Cancelado")
            return 1

        timestamp = datetime.now().strftime("%H%M%S")
        matricula = f"DUP{timestamp}"

        payload_inicial = {
            "nombre": "Duplicado",
            "apellido": "Base",
            "matricula": matricula,
            "tipo": "Estudiante",
            "imagen": frame_a_data_uri(frame),
        }

        r_inicial = post_registro(payload_inicial)
        print(f"\n→ Registro inicial: {r_inicial.status_code}")
        if r_inicial.status_code != 201:
            print(" No se pudo hacer el registro inicial")
            imprimir_respuesta(r_inicial)
            return 1
        print(f"    Persona base registrada con matrícula {matricula}")

    # Ahora intentar duplicar
    print(f"\n→ Intentando duplicar matrícula: {matricula}")
    try:
        frame2 = capturar_frame("Captura para el intento duplicado")
    except RuntimeError as e:
        print(f" {e}")
        return 1

    if frame2 is None:
        print("  Cancelado")
        return 1

    payload_dup = {
        "nombre": "Duplicado",
        "apellido": "Intento",
        "matricula": matricula,
        "tipo": "Estudiante",
        "imagen": frame_a_data_uri(frame2),
    }

    try:
        r = post_registro(payload_dup)
    except Exception as e:
        print(f"\n Error en la petición: {e}")
        return 1

    imprimir_respuesta(r)

    if not validar_status(r, 409, "TEST 2.3.2"):
        return 1

    # Verificar mensaje
    try:
        error = r.json().get('error', '')
        if "Ya existe" in error or "duplicad" in error.lower():
            print(f"\n   Mensaje correcto: '{error}'")
        else:
            print(f"\n    Mensaje inesperado: '{error}'")
    except Exception:
        pass

    print(f"\n TEST 2.3.2 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())