"""
test_fase_7_2.py
Pruebas de estrés del Sprint 2 (7.2.1 - 7.2.3).

Reutiliza las 5 caras reales ya capturadas en fotos7/ (persona1..persona5)
para generar 20+ registros ÚNICOS en la base de datos, con matrículas
distintas. Esto es válido para una prueba de estrés: lo que se mide aquí
es volumen y tiempo de respuesta del sistema, no precisión de
reconocimiento (eso ya se validó a fondo en 7.1 con 100%).

Requiere: pip install requests
"""

import statistics
import sys
import time
import base64
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = "http://localhost:5000/api"

TIMEOUT_NORMAL = 30
TIMEOUT_REGISTRO = 180
TIMEOUT_CALENTAMIENTO = 180

UMBRAL_TIEMPO_RESPUESTA = 3.0  # segundos, según 7.2.2
CANTIDAD_A_REGISTRAR = 20      # 7.2.1: 20+ personas
CONCURRENCIA = 10              # 7.2.3: 10 peticiones simultáneas

# Las mismas 5 caras reales de fotos7/ (deben existir de la Fase 7.1)
PERSONAS_BASE = [
    {"nombre": "Dante", "apellido": "Jair", "tipo": "Estudiante",
     "registro": ["fotos7/persona1_a.jpg", "fotos7/persona1_b.jpg", "fotos7/persona1_c.jpg"],
     "validacion": "fotos7/persona1_d.jpg"},
    {"nombre": "Angel", "apellido": "Gabriel", "tipo": "Docente",
     "registro": ["fotos7/persona2_a.jpg", "fotos7/persona2_b.jpg", "fotos7/persona2_c.jpg"],
     "validacion": "fotos7/persona2_d.jpg"},
    {"nombre": "Gabriel", "apellido": "Hernández", "tipo": "Administrativo",
     "registro": ["fotos7/persona3_a.jpg", "fotos7/persona3_b.jpg", "fotos7/persona3_c.jpg"],
     "validacion": "fotos7/persona3_d.jpg"},
    {"nombre": "Jair", "apellido": "Dante", "tipo": "Estudiante",
     "registro": ["fotos7/persona4_a.jpg", "fotos7/persona4_b.jpg", "fotos7/persona4_c.jpg"],
     "validacion": "fotos7/persona4_d.jpg"},
    {"nombre": "Eliseo", "apellido": "Vásquez", "tipo": "Visitante",
     "registro": ["fotos7/persona5_a.jpg", "fotos7/persona5_b.jpg", "fotos7/persona5_c.jpg"],
     "validacion": "fotos7/persona5_d.jpg"},
]

RUN_ID = uuid.uuid4().hex[:6]


def imagen_a_base64(ruta):
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def post(path, payload, timeout=TIMEOUT_NORMAL):
    return requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)


def calentar_modelo():
    print("Calentando el modelo (primera carga de DeepFace, puede tardar 1-2 minutos)...")
    r = post("/validacion/embedding",
              {"image": imagen_a_base64(PERSONAS_BASE[0]["registro"][0])},
              timeout=TIMEOUT_CALENTAMIENTO)
    print("Modelo listo.\n" if r.status_code == 200 else f"Calentamiento respondió {r.status_code}.\n")


# ============================================
# 7.2.1 — Registrar 20+ personas
# ============================================

def registrar_personas_estres(cantidad=CANTIDAD_A_REGISTRAR):
    print("\n" + "=" * 60)
    print(f"7.2.1 REGISTRO DE VOLUMEN: {cantidad}+ personas")
    print("=" * 60)

    registrados = []
    for i in range(1, cantidad + 1):
        base = PERSONAS_BASE[(i - 1) % len(PERSONAS_BASE)]
        payload = {
            "nombre": f"{base['nombre']}",
            "apellido": f"{base['apellido']} Estres{i:03d}",
            "matricula": f"S2-STRESS-{RUN_ID}-{i:03d}",
            "tipo": base["tipo"],
            "imagenes": [imagen_a_base64(p) for p in base["registro"]],
            "incluir_promedio": True,
        }
        r = post("/registro/persona/multiple", payload, timeout=TIMEOUT_REGISTRO)
        if r.status_code == 201:
            data = r.json()["data"]
            registrados.append({
                "persona_id": data["persona_id"],
                "base_index": (i - 1) % len(PERSONAS_BASE),
            })
            if i % 5 == 0 or i == cantidad:
                print(f"   ... {i}/{cantidad} registradas")
        else:
            print(f"   FAIL #{i} -> {r.status_code}: {r.json().get('error')}")

    print(f"\nRegistradas {len(registrados)}/{cantidad} personas nuevas en esta corrida.")

    # Confirmar el total real en el sistema (puede incluir corridas previas)
    try:
        r = requests.get(f"{BASE_URL}/personas", timeout=15)
        total_sistema = r.json().get("total", "desconocido")
        print(f"Total de personas registradas en todo el sistema: {total_sistema}")
    except requests.exceptions.RequestException:
        pass

    ok = len(registrados) >= 20
    print("PASS - se alcanzaron 20+ personas registradas" if ok else
          "FAIL - no se alcanzaron 20 registros exitosos")
    return registrados


# ============================================
# 7.2.2 — Medir tiempo de respuesta con carga
# ============================================

def medir_tiempo_respuesta(registrados, muestras=15):
    print("\n" + "=" * 60)
    print(f"7.2.2 TIEMPO DE RESPUESTA (< {UMBRAL_TIEMPO_RESPUESTA}s), "
          f"con {len(registrados)}+ personas en la base")
    print("=" * 60)

    tiempos = []
    for i in range(muestras):
        base = PERSONAS_BASE[i % len(PERSONAS_BASE)]
        payload = {
            "image": imagen_a_base64(base["validacion"]),
            "puerta": "Estres-7.2.2",
            "registrar_acceso": False,
        }
        inicio = time.perf_counter()
        try:
            r = post("/validacion", payload, timeout=30)
            duracion = time.perf_counter() - inicio
            ok_http = r.status_code == 200
        except requests.exceptions.RequestException:
            duracion = time.perf_counter() - inicio
            ok_http = False

        tiempos.append(duracion)
        estado = "OK" if ok_http else "ERROR HTTP"
        print(f"   Petición {i + 1:2d}/{muestras}: {duracion:.3f}s [{estado}]")

    print(f"\nPromedio: {statistics.mean(tiempos):.3f}s | "
          f"Mediana: {statistics.median(tiempos):.3f}s | "
          f"Mínimo: {min(tiempos):.3f}s | Máximo: {max(tiempos):.3f}s")

    dentro_umbral = sum(1 for t in tiempos if t < UMBRAL_TIEMPO_RESPUESTA)
    print(f"{dentro_umbral}/{len(tiempos)} peticiones por debajo de {UMBRAL_TIEMPO_RESPUESTA}s")

    ok = dentro_umbral == len(tiempos)
    print(f"PASS - todas las peticiones < {UMBRAL_TIEMPO_RESPUESTA}s" if ok else
          f"FAIL - {len(tiempos) - dentro_umbral} petición(es) superaron el umbral")
    return tiempos


# ============================================
# 7.2.3 — Probar concurrencia
# ============================================

def _una_validacion(indice):
    base = PERSONAS_BASE[indice % len(PERSONAS_BASE)]
    payload = {
        "image": imagen_a_base64(base["validacion"]),
        "puerta": "Estres-7.2.3",
        "registrar_acceso": False,
    }
    inicio = time.perf_counter()
    try:
        r = post("/validacion", payload, timeout=60)
        duracion = time.perf_counter() - inicio
        return indice, duracion, r.status_code == 200, r.status_code
    except requests.exceptions.RequestException as e:
        duracion = time.perf_counter() - inicio
        return indice, duracion, False, str(e)


def probar_concurrencia(n=CONCURRENCIA):
    print("\n" + "=" * 60)
    print(f"7.2.3 CONCURRENCIA: {n} peticiones simultáneas")
    print("=" * 60)

    inicio_total = time.perf_counter()
    resultados = []
    with ThreadPoolExecutor(max_workers=n) as executor:
        futuros = [executor.submit(_una_validacion, i) for i in range(n)]
        for fut in as_completed(futuros):
            resultados.append(fut.result())
    duracion_total = time.perf_counter() - inicio_total

    resultados.sort(key=lambda x: x[0])
    exitosas = 0
    for indice, duracion, ok, detalle in resultados:
        estado = "OK" if ok else f"ERROR ({detalle})"
        print(f"   Petición {indice + 1:2d}: {duracion:.3f}s [{estado}]")
        exitosas += int(ok)

    tiempos = [d for _, d, _, _ in resultados]
    print(f"\nTiempo total para las {n} peticiones: {duracion_total:.3f}s")
    print(f"Suma de tiempos individuales: {sum(tiempos):.3f}s")
    print(f"Peticiones exitosas: {exitosas}/{n}")

    # Si el servidor procesa en paralelo de verdad, el tiempo TOTAL debería
    # acercarse al tiempo de UNA sola petición, no a la suma de las 10.
    # Si Flask corre sin threaded=True, las peticiones se atienden una por
    # una y el total se acerca a la SUMA -> es una limitación conocida del
    # servidor de desarrollo, no necesariamente un error de tu código.
    if duracion_total < sum(tiempos) * 0.6:
        print("El tiempo total sugiere procesamiento en paralelo real.")
    else:
        print("El tiempo total sugiere que las peticiones se atendieron "
              "en serie (una por una). Si esto no es lo esperado, revisa "
              "que app.run() en main.py tenga threaded=True, o que el "
              "backend corra bajo un servidor WSGI con varios workers "
              "(gunicorn) en vez del servidor de desarrollo de Flask.")

    ok = exitosas == n
    print("PASS - las 10 peticiones se resolvieron sin error" if ok else
          f"FAIL - {n - exitosas} petición(es) fallaron")
    return resultados


# ============================================
# Main
# ============================================

def main():
    try:
        salud = requests.get(f"{BASE_URL}/health", timeout=3)
        if salud.status_code != 200:
            print("El servidor no está disponible.")
            return
    except requests.exceptions.RequestException:
        print("No se puede conectar al servidor (docker-compose up -d backend).")
        return

    calentar_modelo()

    registrados = registrar_personas_estres()
    if len(registrados) < 20:
        print("\nAdvertencia: no se alcanzaron 20 registros; 7.2.2 y 7.2.3 "
              "de todos modos continúan con lo que haya en el sistema.")

    medir_tiempo_respuesta(registrados)
    probar_concurrencia()


if __name__ == "__main__":
    main()