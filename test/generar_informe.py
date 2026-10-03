# generar_informe.py
"""
Test 5.2.4 — Generar informe consolidado de resultados
Lee los JSON de las 3 pruebas anteriores y produce un markdown.
"""
import sys
import json
from datetime import datetime
from pathlib import Path


def cargar_json(nombre):
    """Carga un JSON si existe."""
    p = Path(nombre)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("TEST 5.2.4 — Generar informe de resultados")
    print("=" * 60)

    r_521 = cargar_json('resultados_5.2.1.json')
    r_522 = cargar_json('resultados_5.2.2.json')
    r_523 = cargar_json('resultados_5.2.3.json')

    if not r_521:
        print("\n[WARN] Falta resultados_5.2.1.json (corre test_tiempo_respuesta.py)")
    if not r_522:
        print("[WARN] Falta resultados_5.2.2.json (corre test_precision_corregido.py)")
    if not r_523:
        print("[WARN] Falta resultados_5.2.3.json (corre test_escala_10_personas.py)")

    if not any([r_521, r_522, r_523]):
        print("\nERROR: No hay archivos de resultados. Corre primero las 3 pruebas.")
        return 1

    # Construir informe
    lineas = []
    lineas.append("# Informe de Resultados — Fase 5.2")
    lineas.append("")
    lineas.append("**Sprint 2 — Reconocimiento Facial y Registro Biométrico**")
    lineas.append("")
    lineas.append(f"**Fecha del informe:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append("")
    lineas.append("---")
    lineas.append("")

    # Sección 5.2.1
    lineas.append("## 5.2.1 — Tiempo de Respuesta")
    lineas.append("")
    if r_521:
        cumple = "[CUMPLE]" if r_521.get('cumple_sprint') else "[NO CUMPLE]"
        lineas.append(f"**Estado:** {cumple}")
        lineas.append("")
        lineas.append("| Metrica | Valor | Objetivo | Estado |")
        lineas.append("|---|---|---|---|")
        lineas.append(f"| Promedio | {r_521['promedio_ms']:.0f} ms | < 3000 ms | {'OK' if r_521['promedio_ms'] < 3000 else 'FALLA'} |")
        lineas.append(f"| Mediana | {r_521['mediana_ms']:.0f} ms | < 3000 ms | {'OK' if r_521['mediana_ms'] < 3000 else 'FALLA'} |")
        lineas.append(f"| Percentil 95 | {r_521['p95_ms']:.0f} ms | < 3000 ms | {'OK' if r_521['p95_ms'] < 3000 else 'FALLA'} |")
        lineas.append(f"| Maximo | {r_521['max_ms']:.0f} ms | < 5000 ms | {'OK' if r_521['max_ms'] < 5000 else 'FALLA'} |")
        lineas.append(f"| Minimo | {r_521['min_ms']:.0f} ms | — | — |")
        lineas.append(f"| Desv. est. | {r_521['desv_ms']:.0f} ms | — | — |")
        lineas.append("")
        lineas.append(f"Total de mediciones: **{r_521['mediciones']}** · Exitosos: **{r_521['exitosos']}** · Errores: **{r_521['errores']}**")
    else:
        lineas.append("_Prueba no ejecutada._")
    lineas.append("")

    # Sección 5.2.2 (CORREGIDA)
    lineas.append("## 5.2.2 — Precisión del Reconocimiento")
    lineas.append("")
    if r_522:
        cumple = "[CUMPLE]" if r_522.get('cumple_sprint') else "[NO CUMPLE]"
        lineas.append(f"**Estado:** {cumple}")
        lineas.append("")
        lineas.append("| Metrica | Valor | Objetivo | Estado |")
        lineas.append("|---|---|---|---|")
        lineas.append(f"| Precisión | {r_522['precision_pct']:.2f}% | > 95% | {'OK' if r_522['precision_pct'] > 95 else 'FALLA'} |")
        lineas.append(f"| Aciertos | {r_522.get('aciertos', 0)} | — | — |")
        lineas.append(f"| No match | {r_522.get('no_match', r_522.get('falsos_negativos', 0))} | — | — |")
        lineas.append(f"| Confusiones | {r_522.get('confusiones', r_522.get('falsos_positivos', 0))} | — | — |")
        lineas.append("")
        if 'personas_saltadas' in r_522:
            lineas.append(f"Personas totales: **{r_522.get('personas_totales', 0)}** · "
                          f"Saltadas (sin cara disponible): **{r_522['personas_saltadas']}** · "
                          f"Probadas: **{r_522['total_validaciones']}**")
        else:
            lineas.append(f"Personas probadas: **{r_522.get('personas_probadas', 0)}** · "
                          f"Total de validaciones: **{r_522['total_validaciones']}**")
    else:
        lineas.append("_Prueba no ejecutada._")
    lineas.append("")

    # Sección 5.2.3
    lineas.append("## 5.2.3 — Escala con 10+ Personas")
    lineas.append("")
    if r_523:
        cumple = "[CUMPLE]" if (r_523.get('cumple_objetivo') and r_523.get('tiempo_aceptable')) else "[PARCIAL]"
        lineas.append(f"**Estado:** {cumple}")
        lineas.append("")
        lineas.append(f"- Personas en BD: **{r_523['personas_en_bd']}** (objetivo: {r_523['objetivo']})")
        lineas.append(f"- Tiempo promedio de validación: **{r_523['promedio_ms']:.0f} ms**")
        lineas.append(f"- Tiempo mínimo: {r_523['min_ms']:.0f} ms")
        lineas.append(f"- Tiempo máximo: {r_523['max_ms']:.0f} ms")
        lineas.append(f"- Tiempo aceptable (< 3s): {'SI' if r_523.get('tiempo_aceptable') else 'NO'}")
    else:
        lineas.append("_Prueba no ejecutada._")
    lineas.append("")

    # Conclusión
    lineas.append("---")
    lineas.append("")
    lineas.append("## Conclusiones")
    lineas.append("")

    criterios_cumplidos = []
    if r_521 and r_521.get('cumple_sprint'):
        criterios_cumplidos.append("Tiempo de respuesta < 3 segundos")
    if r_522 and r_522.get('cumple_sprint'):
        criterios_cumplidos.append("Precisión > 95%")
    if r_523 and r_523.get('cumple_objetivo'):
        criterios_cumplidos.append(f"Sistema escala a {r_523['personas_en_bd']}+ personas")

    if criterios_cumplidos:
        lineas.append("### Criterios cumplidos")
        lineas.append("")
        for c in criterios_cumplidos:
            lineas.append(f"- [OK] {c}")
    else:
        lineas.append("_Aun no se cumplen los criterios del Sprint 2._")

    lineas.append("")
    lineas.append("---")
    lineas.append("")
    lineas.append("_Informe generado automáticamente por `generar_informe.py`_")

    # Guardar
    contenido = "\n".join(lineas)
    with open('INFORME_FASE_5.2.md', 'w', encoding='utf-8') as f:
        f.write(contenido)

    print("\n  Informe generado: INFORME_FASE_5.2.md")
    print("\n" + "=" * 60)
    print("PREVIEW DEL INFORME")
    print("=" * 60)
    print(contenido)
    print("=" * 60)

    print(f"\nTEST 5.2.4 COMPLETADO")
    return 0


if __name__ == '__main__':
    sys.exit(main())