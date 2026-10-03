# test_activar_rostro.py
"""
Test 4.2.3 — Activar un rostro
Esperado: HTTP 200 con activo=True
"""
import sys
import requests
import json


API_BASE = "http://localhost:5000/api"


def main():
    print("=" * 60)
    print("TEST 4.2.3 — Activar rostro (esperado: 200)")
    print("=" * 60)

    rostro_id = input("\nID de rostro a activar (ej. 4): ").strip()
    if not rostro_id.isdigit():
        print("ERROR: debe ser un numero entero")
        return 1

    rostro_id = int(rostro_id)

    # 1) Primero desactivar para asegurar el caso (opcional)
    print(f"\nPaso 1: desactivar rostro {rostro_id} para preparar el test")
    r_off = requests.put(f"{API_BASE}/rostro/{rostro_id}/desactivar", timeout=10)
    print(f"   Status: {r_off.status_code}")

    # 2) Activar
    print(f"\nPaso 2: activar rostro {rostro_id}")
    try:
        r = requests.put(f"{API_BASE}/rostro/{rostro_id}/activar", timeout=10)
    except Exception as e:
        print(f"ERROR en la peticion: {e}")
        return 1

    print(f"Status HTTP: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    if r.status_code != 200:
        print(f"\nFALLO (esperado 200, recibido {r.status_code})")
        return 1

    data = r.json().get('data', {})
    if data.get('activo') is True:
        print(f"\n   [OK] Rostro {rostro_id} activo correctamente")
    else:
        print(f"\n   [FALLO] El rostro no quedo activo")
        return 1

    # 3) Idempotencia (activar de nuevo)
    print(f"\nPaso 3: activar de nuevo (idempotencia)")
    r2 = requests.put(f"{API_BASE}/rostro/{rostro_id}/activar", timeout=10)
    print(f"   Status: {r2.status_code}")
    print(f"   Message: {r2.json().get('message')}")

    # 4) 404 con ID inexistente
    print(f"\nPaso 4: activar rostro inexistente (esperado 404)")
    r404 = requests.put(f"{API_BASE}/rostro/99999/activar", timeout=10)
    print(f"   Status: {r404.status_code}")
    if r404.status_code == 404:
        print("   [OK] 404 devuelto correctamente")
    else:
        print(f"   [WARN] Se esperaba 404, se obtuvo {r404.status_code}")

    print(f"\nTEST 4.2.3 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())