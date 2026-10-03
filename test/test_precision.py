# test_precision_corregido.py
"""
Test 5.2.2 (corregido) — Precision del reconocimiento facial

Correcciones vs. version anterior:
  - 1 captura por persona (no 3).
  - Permite SALTAR personas cuya cara no tienes.
  - Documenta que el test mide precision real con personas unicas.
"""
import sys
import json
import requests
from test_utils import capturar_frame, frame_a_data_uri, verificar_backend

API_VALIDACION = "http://localhost:5000/api/validacion"
API_PERSONAS = "http://localhost:5000/api/personas"
API_ROSTROS = "http://localhost:5000/api/rostros"


def obtener_personas_con_rostros():
    """Retorna personas con al menos 1 rostro activo."""
    r = requests.get(API_PERSONAS, timeout=10)
    if r.status_code != 200:
        return []
    personas = r.json().get('data', [])
    resultado = []
    for p in personas:
        pid = p['id']
        rr = requests.get(f"{API_ROSTROS}/{pid}?activo=true", timeout=10)
        if rr.status_code == 200 and rr.json().get('total', 0) > 0:
            resultado.append({
                'id': pid,
                'nombre': f"{p['nombre']} {p['apellido']}",
                'matricula': p['matricula_empleado'],
                'rostros_activos': rr.json().get('total', 0),
            })
    return resultado


def main():
    print("=" * 60)
    print("TEST 5.2.2 — Precisión del reconocimiento (corregido)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    personas = obtener_personas_con_rostros()
    if not personas:
        print("ERROR: No hay personas con rostros activos")
        return 1

    print(f"\nPersonas con rostros activos: {len(personas)}")
    print(f"\n{'ID':<5} {'Matrícula':<15} {'Nombre':<25} {'Rostros':<8}")
    print("-" * 60)
    for p in personas:
        print(f"{p['id']:<5} {p['matricula']:<15} {p['nombre']:<25} {p['rostros_activos']:<8}")

    print("\n[INSTRUCCIONES]")
    print("Para cada persona, se te pedirá:")
    print("  1. Capturar su rostro real (si lo tienes)")
    print("  2. O presionar 's' para SALTAR (si no tienes su cara)")

    resultados = []
    aciertos = 0
    no_match = 0
    confusion = 0
    saltadas = 0

    for persona in personas:
        print(f"\n--- Persona {persona['id']}: {persona['nombre']} ({persona['matricula']}) ---")
        print(f"    Rostros activos: {persona['rostros_activos']}")

        resp = input("    ¿Tienes la cara de esta persona? [ENTER=si / s=saltar]: ").strip().lower()
        if resp == 's':
            saltadas += 1
            print(f"    [SKIP] Persona saltada")
            continue

        try:
            frame = capturar_frame(f"Captura de {persona['nombre']}")
        except RuntimeError as e:
            print(f"    ERROR cámara: {e}")
            continue
        if frame is None:
            print(f"    [SKIP] Captura cancelada")
            continue

        payload = {"image": frame_a_data_uri(frame), "registrar_acceso": False}
        try:
            r = requests.post(API_VALIDACION, json=payload, timeout=30)
        except Exception as e:
            print(f"    ERROR conexión: {e}")
            continue

        if r.status_code != 200:
            print(f"    ERROR HTTP {r.status_code}")
            continue

        v = r.json().get('validacion', {})
        exito = v.get('exito', False)
        detectado = v.get('persona_id')
        confianza = v.get('confianza', 0)
        nivel = v.get('nivel_confianza', '?')

        if exito and detectado == persona['id']:
            aciertos += 1
            print(f"    [OK]    Detectado {detectado}  conf={confianza:.3f}  nivel={nivel}")
        elif not exito:
            no_match += 1
            print(f"    [NM]    No match (esperaba {persona['id']})")
        else:
            confusion += 1
            print(f"    [CONF]  Detectó {detectado} (esperaba {persona['id']})")

        resultados.append({
            'esperado': persona['id'],
            'esperado_nombre': persona['nombre'],
            'detectado': detectado,
            'exito': exito,
            'correcto': exito and detectado == persona['id'],
            'confianza': confianza,
            'nivel': nivel,
        })

    # Estadísticas
    total = len(resultados)
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    if total == 0:
        print(f"\n  No hubo validaciones (todas saltadas o canceladas).")
        print(f"  Saltadas: {saltadas}")
        return 1

    precision = (aciertos / total) * 100

    print(f"\n  Personas totales:      {len(personas)}")
    print(f"  Personas saltadas:     {saltadas}")
    print(f"  Validaciones reales:   {total}")
    print(f"\n  Aciertos:              {aciertos}")
    print(f"  No match:              {no_match}")
    print(f"  Confusiones:           {confusion}")
    print(f"\n  PRECISIÓN:             {precision:.2f}%")

    cumple = precision > 95.0
    print(f"\n  Criterio Sprint (>95%): {'[OK]' if cumple else '[FALLO]'}")

    # Guardar
    resumen = {
        'fase': '5.2.2',
        'version': 'corregida',
        'personas_totales': len(personas),
        'personas_saltadas': saltadas,
        'total_validaciones': total,
        'aciertos': aciertos,
        'no_match': no_match,
        'confusiones': confusion,
        'precision_pct': round(precision, 2),
        'cumple_sprint': cumple,
        'detalle': resultados,
        'nota': 'Test corregido: 1 captura por persona, permite saltar',
    }

    with open('resultados_5.2.2.json', 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: resultados_5.2.2.json")

    if cumple:
        print(f"\nTEST 5.2.2 PASÓ")
        return 0
    else:
        print(f"\nTEST 5.2.2 FALLÓ")
        return 1


if __name__ == '__main__':
    sys.exit(main())