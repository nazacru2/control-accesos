# test_listar_personas.py
"""
Test 4.2.1 — Listar personas
Esperado: HTTP 200 + lista de personas
"""
import sys
import requests
import json


API_BASE = "http://localhost:5000/api"


def main():
    print("=" * 60)
    print("TEST 4.2.1 — Listar personas (esperado: 200)")
    print("=" * 60)

    try:
        r = requests.get(f"{API_BASE}/personas", timeout=10)
    except Exception as e:
        print(f"ERROR en la peticion: {e}")
        return 1

    print(f"\nStatus HTTP: {r.status_code}")

    if r.status_code != 200:
        print(f"FALLO (esperado 200, recibido {r.status_code})")
        print(r.text)
        return 1

    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

    total = data.get('total', 0)
    print(f"\n   Total de personas: {total}")

    if total < 1:
        print("\n   [WARN] No hay personas en la BD")
    else:
        print(f"\n   [OK] {total} personas listadas")

    print(f"\nTEST 4.2.1 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())