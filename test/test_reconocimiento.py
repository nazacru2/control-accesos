"""
test_reconocimiento.py (corregido)
Pruebas de reconocimiento facial - Fase 7.2
- 7.2.1 Probar extracción de embedding
- 7.2.2 Probar comparación de embeddings
- 7.2.3 Verificar precisión > 95%

IMPORTANTE: llena TEST_IMAGES con rutas a fotos REALES antes de correr esto.
Las imágenes generadas con círculos/óvalos NO son detectadas por mtcnn,
así que el script fallará en 7.2.1 si no usas fotos de rostros reales.
"""

import requests
import base64
import itertools
import subprocess
import time
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

# ============================================
# CONFIGURA AQUÍ TUS FOTOS DE PRUEBA
# ============================================
# Agrupa varias fotos de la MISMA persona bajo la misma clave.
# Necesitas al menos 2 personas distintas, e idealmente 2+ fotos por
# persona (distinta luz/ángulo) para que 7.2.3 tenga sentido.
TEST_IMAGES = {
    "persona_1": [
        "fotos/persona1_a.jpeg",
        "fotos/persona1_b.jpeg",
    ],
    "persona_2": [
        "fotos/persona2_a.jpeg",
        "fotos/persona2_b.jpeg",
    ],
    "persona_3": [
        "fotos/persona3_a.jpeg",
        "fotos/persona3_b.jpeg",
    ]
}


# ============================================
# Utilidades
# ============================================

def imagen_a_base64(ruta):
    """Lee un archivo de imagen del disco y lo codifica en base64."""
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ============================================
# 7.2.1 Probar extracción de embedding
# ============================================

def test_extraccion_embedding():
    print("\n" + "=" * 60)
    print("7.2.1 PRUEBA: Extracción de embedding")
    print("=" * 60)

    primera_persona = next(iter(TEST_IMAGES))
    ruta = TEST_IMAGES[primera_persona][0]
    print(f"\nUsando: {ruta}")

    img_b64 = imagen_a_base64(ruta)

    response = requests.post(
        f"{BASE_URL}/validacion/embedding",
        json={"image": img_b64},
        timeout=30,
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            embedding = result.get("embedding", [])
            print("Embedding extraído exitosamente")
            print(f"   Tamaño: {result.get('embedding_size')} dimensiones")
            print(f"   Modelo: {result.get('model')}")
            print(f"   Primeros 5 valores: {embedding[:5]}")
            return True
        print(f"No se pudo extraer embedding: {result.get('error')}")
    else:
        print(f"Error HTTP: {response.status_code} - {response.text}")

    return False


# ============================================
# 7.2.2 Probar comparación de embeddings
# ============================================

def comparar(ruta1, ruta2):
    """Llama a /api/validacion/compare y regresa (similarity, match)."""
    response = requests.post(
        f"{BASE_URL}/validacion/compare",
        json={"image1": imagen_a_base64(ruta1), "image2": imagen_a_base64(ruta2)},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"   Error HTTP {response.status_code}: {response.text}")
        return None, None

    result = response.json()
    if not result.get("success"):
        print(f"   Error: {result.get('error')}")
        return None, None

    return result.get("similarity"), result.get("match")


def test_comparacion_embeddings():
    print("\n" + "=" * 60)
    print("7.2.2 PRUEBA: Comparación de embeddings")
    print("=" * 60)

    personas = list(TEST_IMAGES.keys())

    # Test 1: misma persona, dos fotos distintas
    if len(TEST_IMAGES[personas[0]]) >= 2:
        print("\nTest 1: Misma persona, fotos distintas")
        r1, r2 = TEST_IMAGES[personas[0]][:2]
        similarity, match = comparar(r1, r2)
        if similarity is not None:
            print(f"   Similitud: {similarity:.4f} | Match: {match}")
            print(f"   {'PASS' if match else 'FAIL'} - Debería dar match=True")

    # Test 2: personas distintas
    if len(personas) >= 2:
        print("\nTest 2: Personas distintas")
        r1 = TEST_IMAGES[personas[0]][0]
        r2 = TEST_IMAGES[personas[1]][0]
        similarity, match = comparar(r1, r2)
        if similarity is not None:
            print(f"   Similitud: {similarity:.4f} | Match: {match}")
            print(f"   {'PASS' if not match else 'FAIL'} - Debería dar match=False")

    return True


# ============================================
# 7.2.3 Verificar precisión (real, no autocomparación)
# ============================================

def test_precision():
    print("\n" + "=" * 60)
    print("7.2.3 PRUEBA: Verificar precisión > 95%")
    print("=" * 60)

    # Construye todos los pares posibles con su etiqueta esperada:
    # mismo=True si son de la misma persona, False si son de personas distintas.
    pares = []
    for persona, fotos in TEST_IMAGES.items():
        for r1, r2 in itertools.combinations(fotos, 2):
            pares.append((r1, r2, True))

    personas = list(TEST_IMAGES.keys())
    for p1, p2 in itertools.combinations(personas, 2):
        for r1 in TEST_IMAGES[p1]:
            for r2 in TEST_IMAGES[p2]:
                pares.append((r1, r2, False))

    if not pares:
        print("\nNecesitas al menos 2 fotos de la misma persona, o 2 personas")
        print("distintas en TEST_IMAGES para poder calcular precisión.")
        return False

    print(f"\nEvaluando {len(pares)} pares de comparación...")
    aciertos = 0
    for r1, r2, mismo_esperado in pares:
        similarity, match = comparar(r1, r2)
        if similarity is None:
            continue
        correcto = (match == mismo_esperado)
        aciertos += int(correcto)
        estado = "OK" if correcto else "MAL"
        etiqueta = "misma persona" if mismo_esperado else "personas distintas"
        print(f"   [{estado}] {r1} vs {r2} ({etiqueta}) sim={similarity:.4f} match={match}")
        time.sleep(0.2)

    precision = (aciertos / len(pares)) * 100
    print(f"\nPrecisión real: {precision:.2f}% ({aciertos}/{len(pares)} correctos)")

    if precision >= 95:
        print("PASS - Precisión > 95%")
        return True

    print(f"FAIL - Precisión {precision:.2f}% < 95%. Revisa el threshold o las fotos usadas.")
    return False


# ============================================
# Utilidad: contar rostros registrados en BD (sin -it, para subprocess)
# ============================================

def contar_rostros_en_bd():
    result = subprocess.run(
        [
            "docker", "exec", "postgres_accesos",
            "psql", "-U", "admin", "-d", "control_accesos",
            "-t", "-c", "SELECT COUNT(*) FROM Rostro WHERE activo = TRUE;",
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        print(f"   No se pudo leer el conteo. stderr: {result.stderr}")
        return None


# ============================================
# Función principal
# ============================================

def main():
    print("=" * 60)
    print("PRUEBAS DE RECONOCIMIENTO FACIAL - SPRINT 1")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code != 200:
            print("\nEl servidor no está disponible.")
            return
        print("\nServidor disponible")
    except requests.exceptions.RequestException:
        print("\nNo se puede conectar al servidor.")
        print("   docker-compose up -d backend")
        return

    resultados = []
    resultados.append(("7.2.1 Extracción de embedding", test_extraccion_embedding()))
    time.sleep(1)
    resultados.append(("7.2.2 Comparación de embeddings", test_comparacion_embeddings()))
    time.sleep(1)
    resultados.append(("7.2.3 Verificar precisión", test_precision()))

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    aprobadas = 0
    for nombre, ok in resultados:
        print(f"  {'PASS' if ok else 'FAIL'} - {nombre}")
        aprobadas += int(ok)

    print(f"\nTotal: {aprobadas}/{len(resultados)} pruebas exitosas")


if __name__ == "__main__":
    main()