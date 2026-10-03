# Informe de Resultados — Fase 5.2

**Sprint 2 — Reconocimiento Facial y Registro Biométrico**

**Fecha del informe:** 2026-09-17 12:12:15

---

## 5.2.1 — Tiempo de Respuesta

**Estado:** [CUMPLE]

| Metrica | Valor | Objetivo | Estado |
|---|---|---|---|
| Promedio | 1116 ms | < 3000 ms | OK |
| Mediana | 1118 ms | < 3000 ms | OK |
| Percentil 95 | 1246 ms | < 3000 ms | OK |
| Maximo | 1472 ms | < 5000 ms | OK |
| Minimo | 910 ms | — | — |
| Desv. est. | 131 ms | — | — |

Total de mediciones: **20** · Exitosos: **20** · Errores: **0**

## 5.2.2 — Precisión del Reconocimiento

**Estado:** [CUMPLE]

| Metrica | Valor | Objetivo | Estado |
|---|---|---|---|
| Precisión | 100.00% | > 95% | OK |
| Aciertos | 1 | — | — |
| No match | 0 | — | — |
| Confusiones | 0 | — | — |

Personas totales: **3** · Saltadas (sin cara disponible): **2** · Probadas: **1**

## 5.2.3 — Escala con 10+ Personas

**Estado:** [CUMPLE]

- Personas en BD: **10** (objetivo: 10)
- Tiempo promedio de validación: **1217 ms**
- Tiempo mínimo: 840 ms
- Tiempo máximo: 2799 ms
- Tiempo aceptable (< 3s): SI

---

## Conclusiones

### Criterios cumplidos

- [OK] Tiempo de respuesta < 3 segundos
- [OK] Precisión > 95%
- [OK] Sistema escala a 10+ personas

---

_Informe generado automáticamente por `generar_informe.py`_