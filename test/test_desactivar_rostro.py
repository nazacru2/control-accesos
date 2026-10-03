# test_desactivar_rostro.py
"""
Test 4.2.4 — Desactivar un rostro
Esperado: HTTP 200 con activo=False
"""
import sys
import requests
import json


API_BASE = "http://localhost:5000/api"


def main():
    print("=" * 60)
    print("TEST 4.2.4 — Desactivar rostro (esperado: 200)")
    print("=" * 60)

    rostro_id = input("\nID de rostro a desactivar (ej. 6): ").strip()
    if not rostro_id.isdigit():
        print("ERROR: debe ser un numero entero")
        return 1

    rostro_id = int(rostro_id)

    # 1) Desactivar
    print(f"\nPaso 1: desactivar rostro {rostro_id}")
    try:
        r = requests.put(f"{API_BASE}/rostro/{rostro_id}/desactivar", timeout=10)
    except Exception as e:
        print(f"ERROR en la peticion: {e}")
        return 1

    print(f"Status HTTP: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    if r.status_code != 200:
        print(f"\nFALLO (esperado 200, recibido {r.status_code})")
        return 1

    data = r.json().get('data', {})
    if data.get('activo') is False:
        print(f"\n   [OK] Rostro {rostro_id} desactivado correctamente")
    else:
        print(f"\n   [FALLO] El rostro no quedo inactivo")
        return 1

    # 2) Idempotencia (desactivar de nuevo)
    print(f"\nPaso 2: desactivar de nuevo (idempotencia)")
    r2 = requests.put(f"{API_BASE}/rostro/{rostro_id}/desactivar", timeout=10)
    print(f"   Status: {r2.status_code}")
    print(f"   Message: {r2.json().get('message')}")

    # 3) 404 con ID inexistente
    print(f"\nPaso 3: desactivar rostro inexistente (esperado 404)")
    r404 = requests.put(f"{API_BASE}/rostro/99999/desactivar", timeout=10)
    print(f"   Status: {r404.status_code}")
    if r404.status_code == 404:
        print("   [OK] 404 devuelto correctamente")
    else:
        print(f"   [WARN] Se esperaba 404, se obtuvo {r404.status_code}")

    # 4) Reactivar para dejar la BD como estaba
    print(f"\nPaso 4: restaurar el rostro a activo")
    r3 = requests.put(f"{API_BASE}/rostro/{rostro_id}/activar", timeout=10)
    print(f"   Status: {r3.status_code}")

    print(f"\nTEST 4.2.4 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())