# test_escala_10_personas.py
"""
Test 5.2.3 — Verificar comportamiento con 10+ personas registradas
Mide tiempo de validacion para verificar que no degrada.
"""
import sys
import time
import json
import requests
from test_utils import capturar_frame, frame_a_data_uri, verificar_backend

API_PERSONAS = "http://localhost:5000/api/personas"
API_VALIDACION = "http://localhost:5000/api/validacion"
OBJETIVO = 10
N_MEDICIONES = 10


def main():
    print("=" * 60)
    print(f"TEST 5.2.3 — Escala con {OBJETIVO}+ personas")
    print("=" * 60)

    if not verificar_backend():
        return 1

    # Contar personas
    r = requests.get(API_PERSONAS, timeout=10)
    total = r.json().get('total', 0)

    print(f"\n  Personas actuales en BD: {total}")
    print(f"  Objetivo:                {OBJETIVO}")

    if total >= OBJETIVO:
        print(f"  [OK] Ya hay suficientes personas")
    else:
        faltan = OBJETIVO - total
        print(f"  [WARN] Faltan {faltan} personas para el objetivo")
        print(f"\n  Registra mas personas con:")
        print(f"    python test_registro_persona.py")
        print(f"  Ejecuta ese comando {faltan} veces y vuelve a correr este test.")

    # Medir tiempo con carga actual
    print(f"\nMidiendo tiempo de validacion con {total} personas...")

    try:
        frame = capturar_frame("Captura para medir con carga")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1
    if frame is None:
        return 1

    payload = {"image": frame_a_data_uri(frame), "registrar_acceso": False}

    tiempos = []
    for i in range(N_MEDICIONES):
        t0 = time.perf_counter()
        r = requests.post(API_VALIDACION, json=payload, timeout=30)
        dt = (time.perf_counter() - t0) * 1000
        tiempos.append(dt)
        print(f"  [{i+1:>2}/{N_MEDICIONES}] {dt:>6.0f}ms  status={r.status_code}")

    promedio = sum(tiempos) / len(tiempos)
    print(f"\n  Tiempo promedio: {promedio:.0f}ms")
    print(f"  Tiempo minimo:   {min(tiempos):.0f}ms")
    print(f"  Tiempo maximo:   {max(tiempos):.0f}ms")

    resultados = {
        'fase': '5.2.3',
        'personas_en_bd': total,
        'objetivo': OBJETIVO,
        'cumple_objetivo': total >= OBJETIVO,
        'mediciones': N_MEDICIONES,
        'promedio_ms': round(promedio, 2),
        'min_ms': round(min(tiempos), 2),
        'max_ms': round(max(tiempos), 2),
        'tiempo_aceptable': promedio < 3000,
    }

    with open('resultados_5.2.3.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: resultados_5.2.3.json")

    if total >= OBJETIVO and promedio < 3000:
        print(f"\nTEST 5.2.3 PASO")
        return 0
    else:
        print(f"\nTEST 5.2.3 INCOMPLETO")
        return 1


if __name__ == '__main__':
    sys.exit(main())