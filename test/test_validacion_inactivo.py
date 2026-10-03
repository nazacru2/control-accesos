# test_validacion_inactivo.py
"""
Test 4.2.5 — Verificar que rostros inactivos NO se usan en validación

Estrategia concluyente:
  1. Capturar imagen de la persona
  2. Validar con TODOS los rostros activos (baseline → match=True)
  3. Desactivar TODOS los rostros activos de la persona
  4. Validar de nuevo (→ match=False, nadie la reconoce)
  5. Reactivar todos los rostros que desactivamos
"""
import sys

import requests

from test_utils import (
    capturar_frame,
    frame_a_data_uri,
    imprimir_respuesta,
    verificar_backend,
)

API_BASE = "http://localhost:5000/api"


def main():
    print("=" * 60)
    print("TEST 4.2.5 — Rostro inactivo no se usa en validacion")
    print("=" * 60)

    if not verificar_backend():
        return 1

    persona_id = input("\nID de la persona a probar (ej. 9): ").strip()
    if not persona_id.isdigit():
        print("ERROR: debe ser un numero entero")
        return 1
    persona_id = int(persona_id)

    # Obtener rostros
    r_rostros = requests.get(f"{API_BASE}/rostros/{persona_id}", timeout=10)
    if r_rostros.status_code != 200:
        print(f"ERROR: no se pudo listar rostros ({r_rostros.status_code})")
        return 1

    rostros = r_rostros.json().get('data', [])
    if not rostros:
        print(f"ERROR: la persona {persona_id} no tiene rostros")
        return 1

    print(f"\nRostros de persona {persona_id}:")
    for r in rostros:
        tipo = "PROMEDIO" if r.get('es_promedio') else "normal"
        estado = "activo" if r['activo'] else "inactivo"
        print(f"   id={r['id']:>3}  {tipo:<8}  {estado}")

    rostros_a_desactivar = [r for r in rostros if r['activo']]
    if not rostros_a_desactivar:
        print(f"\nERROR: la persona {persona_id} no tiene rostros activos")
        print("Reactiva al menos uno antes de correr este test")
        return 1

    print(f"\nSe desactivaran {len(rostros_a_desactivar)} rostros: "
          f"{[r['id'] for r in rostros_a_desactivar]}")

    input("\nPresiona ENTER para capturar la imagen...")

    # Capturar
    try:
        frame = capturar_frame("Captura para validar contra la persona")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1
    if frame is None:
        print("Cancelado")
        return 1

    imagen_b64 = frame_a_data_uri(frame)
    payload_valid = {
        "image": imagen_b64,
        "umbral": 0.6,
        "registrar_acceso": False,
    }

    # PASO 1: Validar ANTES (baseline)
    print("\n" + "-" * 60)
    print("PASO 1: Validar con TODOS los rostros ACTIVOS")
    print("-" * 60)

    r_antes = requests.post(f"{API_BASE}/validacion", json=payload_valid, timeout=120)
    imprimir_respuesta(r_antes)

    validacion_antes = r_antes.json().get('validacion', {})
    match_antes = validacion_antes.get('exito', False)
    persona_antes = (validacion_antes.get('persona') or {}).get('id')

    print(f"\n   Match: {match_antes}")
    print(f"   Persona detectada: {persona_antes}")

    if not match_antes or persona_antes != persona_id:
        print(f"\n   [WARN] No hubo match con persona {persona_id}.")
        print("   El test no puede continuar sin un baseline valido.")
        return 1

    # PASO 2: Desactivar TODOS los rostros activos
    print("\n" + "-" * 60)
    print(f"PASO 2: Desactivar TODOS los {len(rostros_a_desactivar)} rostros")
    print("-" * 60)

    for r in rostros_a_desactivar:
        rr = requests.put(f"{API_BASE}/rostro/{r['id']}/desactivar", timeout=10)
        print(f"   Rostro {r['id']}: status={rr.status_code}")

    # PASO 3: Validar DESPUES
    print("\n" + "-" * 60)
    print("PASO 3: Validar SIN rostros activos (match debe ser False)")
    print("-" * 60)

    r_despues = requests.post(f"{API_BASE}/validacion", json=payload_valid, timeout=120)
    imprimir_respuesta(r_despues)

    validacion_despues = r_despues.json().get('validacion', {})
    match_despues = validacion_despues.get('exito', False)
    persona_despues = (validacion_despues.get('persona') or {}).get('id')

    print(f"\n   Match: {match_despues}")
    print(f"   Persona detectada: {persona_despues}")

    # PASO 4: Reactivar todos
    print("\n" + "-" * 60)
    print(f"PASO 4: Reactivar los {len(rostros_a_desactivar)} rostros")
    print("-" * 60)

    for r in rostros_a_desactivar:
        rr = requests.put(f"{API_BASE}/rostro/{r['id']}/activar", timeout=10)
        print(f"   Rostro {r['id']}: status={rr.status_code}")

    # RESULTADO
    print("\n" + "=" * 60)
    print("RESULTADO DEL TEST 4.2.5")
    print("=" * 60)

    if match_despues and persona_despues == persona_id:
        print(f"\n   [FALLO] Match con persona {persona_id} SIN rostros activos.")
        print("   El sistema uso un rostro inactivo.")
        return 1
    else:
        print(f"\n   [OK] Sin rostros activos, NO hubo match con persona {persona_id}.")
        print("   El sistema respeta el campo 'activo'.")
        if match_despues:
            print(f"   (Detecto otra persona: {persona_despues})")
        print(f"\nTEST 4.2.5 COMPLETADO")
        return 0


if __name__ == '__main__':
    sys.exit(main())