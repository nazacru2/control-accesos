# test_tiempo_respuesta.py
"""
Test 5.2.1 — Medir tiempo de respuesta del endpoint /api/validacion
Ejecuta N validaciones y calcula estadisticas.
Objetivo Sprint 2: cada peticion < 3 segundos
"""
import sys
import time
import json
import statistics
import requests
from test_utils import capturar_frame, frame_a_data_uri, verificar_backend

API = "http://localhost:5000/api/validacion"
N_MEDICIONES = 20


def main():
    print("=" * 60)
    print(f"TEST 5.2.1 — Tiempo de respuesta ({N_MEDICIONES} mediciones)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    print("\nCaptura UNA imagen que se reusara en todas las mediciones.")
    print("Asi medimos SOLO el tiempo del backend.")
    try:
        frame = capturar_frame("Captura para medicion de tiempo")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1
    if frame is None:
        print("Cancelado")
        return 1

    imagen_b64 = frame_a_data_uri(frame)
    payload = {"image": imagen_b64, "registrar_acceso": False}

    tiempos = []
    exitos = 0
    errores = []

    print(f"\nEjecutando {N_MEDICIONES} validaciones...\n")

    for i in range(N_MEDICIONES):
        t0 = time.perf_counter()
        try:
            r = requests.post(API, json=payload, timeout=30)
            dt = (time.perf_counter() - t0) * 1000
            tiempos.append(dt)

            if r.status_code == 200:
                data = r.json()
                exito = data.get('validacion', {}).get('exito', False)
                confianza = data.get('validacion', {}).get('confianza', 0)
                nivel = data.get('validacion', {}).get('nivel_confianza', '?')
                if exito:
                    exitos += 1
                print(f"  [{i+1:>2}/{N_MEDICIONES}] {dt:>6.0f}ms  "
                      f"exito={exito}  conf={confianza:.3f}  nivel={nivel}")
            else:
                errores.append(f"#{i+1}: HTTP {r.status_code}")
                print(f"  [{i+1:>2}/{N_MEDICIONES}] ERROR HTTP {r.status_code}")
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000
            tiempos.append(dt)
            errores.append(f"#{i+1}: {e}")
            print(f"  [{i+1:>2}/{N_MEDICIONES}] EXCEPCION {e}")

    # Estadisticas
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    if not tiempos:
        print("No hay mediciones validas")
        return 1

    tiempos_sorted = sorted(tiempos)
    minimo = min(tiempos)
    maximo = max(tiempos)
    promedio = statistics.mean(tiempos)
    mediana = statistics.median(tiempos)
    p95 = tiempos_sorted[int(len(tiempos_sorted) * 0.95) - 1]
    desv = statistics.stdev(tiempos) if len(tiempos) > 1 else 0

    print(f"\n  Mediciones:          {len(tiempos)}/{N_MEDICIONES}")
    print(f"  Validaciones match:  {exitos}/{len(tiempos)}")
    print(f"  Errores:             {len(errores)}")
    print(f"\n  Tiempo minimo:       {minimo:>7.0f} ms")
    print(f"  Tiempo maximo:       {maximo:>7.0f} ms")
    print(f"  Tiempo promedio:     {promedio:>7.0f} ms")
    print(f"  Mediana:             {mediana:>7.0f} ms")
    print(f"  Percentil 95:        {p95:>7.0f} ms")
    print(f"  Desv. estandar:      {desv:>7.0f} ms")

    # Criterios del Sprint
    print("\n" + "=" * 60)
    print("CRITERIOS SPRINT 2 (< 3000 ms)")
    print("=" * 60)

    cumple_promedio = promedio < 3000
    cumple_p95 = p95 < 3000
    cumple_maximo = maximo < 5000

    print(f"  Promedio < 3000ms:   {'[OK]' if cumple_promedio else '[FALLO]'}  ({promedio:.0f}ms)")
    print(f"  P95 < 3000ms:        {'[OK]' if cumple_p95 else '[FALLO]'}  ({p95:.0f}ms)")
    print(f"  Maximo < 5000ms:     {'[OK]' if cumple_maximo else '[FALLO]'}  ({maximo:.0f}ms)")

    # Guardar
    resultados = {
        'fase': '5.2.1',
        'mediciones': len(tiempos),
        'exitosos': exitos,
        'errores': len(errores),
        'min_ms': round(minimo, 2),
        'max_ms': round(maximo, 2),
        'promedio_ms': round(promedio, 2),
        'mediana_ms': round(mediana, 2),
        'p95_ms': round(p95, 2),
        'desv_ms': round(desv, 2),
        'cumple_sprint': cumple_promedio and cumple_p95,
    }

    with open('resultados_5.2.1.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: resultados_5.2.1.json")

    if cumple_promedio and cumple_p95:
        print(f"\nTEST 5.2.1 PASO")
        return 0
    else:
        print(f"\nTEST 5.2.1 FALLO")
        return 1


if __name__ == '__main__':
    sys.exit(main())