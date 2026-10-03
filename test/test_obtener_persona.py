# test_obtener_persona.py
"""
Test 4.2.2 — Obtener persona por ID
Esperado: HTTP 200 con datos de la persona + total_rostros
"""
import sys
import requests
import json


API_BASE = "http://localhost:5000/api"


def main():
    print("=" * 60)
    print("TEST 4.2.2 — Obtener persona por ID (esperado: 200)")
    print("=" * 60)

    persona_id = input("\nID de persona a consultar (ej. 9): ").strip()
    if not persona_id.isdigit():
        print("ERROR: debe ser un numero entero")
        return 1

    persona_id = int(persona_id)

    # Probar caso exitoso
    try:
        r = requests.get(f"{API_BASE}/persona/{persona_id}", timeout=10)
    except Exception as e:
        print(f"ERROR en la peticion: {e}")
        return 1

    print(f"\nStatus HTTP: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    if r.status_code != 200:
        print(f"\nFALLO (esperado 200, recibido {r.status_code})")
        return 1

    data = r.json().get('data', {})
    print(f"\n   Persona: {data.get('nombre')} {data.get('apellido')}")
    print(f"   Matricula: {data.get('matricula_empleado')}")
    print(f"   Total rostros: {data.get('total_rostros')}")
    print(f"   Rostros activos: {data.get('rostros_activos')}")

    # Probar caso 404 (persona inexistente)
    print("\n--- Probando persona inexistente (esperado 404) ---")
    r404 = requests.get(f"{API_BASE}/persona/99999", timeout=10)
    print(f"Status HTTP: {r404.status_code}")

    if r404.status_code == 404:
        print("   [OK] 404 devuelto correctamente")
    else:
        print(f"   [WARN] Se esperaba 404, se obtuvo {r404.status_code}")

    print(f"\nTEST 4.2.2 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())