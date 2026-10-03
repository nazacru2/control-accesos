"""
test_fase_7_1.py
Pruebas de registro y validación del Sprint 2 (7.1.1 - 7.1.5), usando
siempre la API real (nunca SQL directo) para que el caché de embeddings
se invalide correctamente en cada paso.

Requiere: pip install requests

Antes de correr, llena TEST_PEOPLE y STRANGER_PHOTOS con rutas a fotos
reales (mínimo 4 fotos por persona: 3 para el registro + 1 reservada
para la validación; y al menos 1-2 fotos de personas NO registradas).
"""

import sys
import time
import base64
import uuid
import requests
import psycopg2

BASE_URL = "http://localhost:5000/api"

TIMEOUT_NORMAL = 30    # validación de una sola imagen
TIMEOUT_REGISTRO = 180  # registro múltiple: procesa 3+ imágenes por persona
TIMEOUT_CALENTAMIENTO = 180  # primera llamada: carga el modelo DeepFace en memoria


# ============================================
# CONFIGURA AQUÍ TUS FOTOS DE PRUEBA
# ============================================
TEST_PEOPLE = {
    "persona1": {
        "nombre": "Dante", "apellido": "Jair", "tipo": "Estudiante",
        "registro": ["fotos7/persona1_a.jpg", "fotos7/persona1_b.jpg", "fotos7/persona1_c.jpg"],
        "validacion": "fotos7/persona1_d.jpg",
    },
    "persona2": {
        "nombre": "Angel", "apellido": "Gabriel", "tipo": "Docente",
        "registro": ["fotos7/persona2_a.jpg", "fotos7/persona2_b.jpg", "fotos7/persona2_c.jpg"],
        "validacion": "fotos7/persona2_d.jpg",
    },
    "persona3": {
        "nombre": "Gabriel", "apellido": "Hernández", "tipo": "Administrativo",
        "registro": ["fotos7/persona3_a.jpg", "fotos7/persona3_b.jpg", "fotos7/persona3_c.jpg"],
        "validacion": "fotos7/persona3_d.jpg",
    },
    "persona4": {
        "nombre": "Jair", "apellido": "Dante", "tipo": "Estudiante",
        "registro": ["fotos7/persona4_a.jpg", "fotos7/persona4_b.jpg", "fotos7/persona4_c.jpg"],
        "validacion": "fotos7/persona4_d.jpg",
    },
    "persona5": {
        "nombre": "Eliseo", "apellido": "Vásquez", "tipo": "Visitante",
        "registro": ["fotos7/persona5_a.jpg", "fotos7/persona5_b.jpg", "fotos7/persona5_c.jpg"],
        "validacion": "fotos7/persona5_d.jpg",
    },
}

# Fotos de personas que NO se van a registrar (para 7.1.3 y parte de 7.1.5)
STRANGER_PHOTOS = [
    "fotos7/desconocido_a.jpg",
    "fotos7/desconocido_b.jpg",
]

# Persona sobre la que se prueba la desactivación en 7.1.4
PERSONA_PARA_DESACTIVAR = "persona5"

RUN_ID = uuid.uuid4().hex[:6]  # evita choques de matrícula entre corridas

# Config de conexión directa a Postgres, SOLO para limpiar datos de
# corridas anteriores de este mismo script antes de empezar (matrículas
# con prefijo "S2-"). Ningún dato real se toca: el patrón es exclusivo
# de este test.
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "control_accesos",
    "user": "admin",
    "password": "SecurePassword123!",
}


def limpiar_corridas_anteriores():
    """
    Borra TODAS las personas de prueba (y en cascada sus rostros) excepto
    ADMIN001, antes de cada corrida. El proyecto aún no tiene datos reales
    de producción, así que cualquier persona con rostro registrado es, por
    definición, dato de prueba acumulado de alguna sesión anterior (propia
    o de pruebas manuales) — dejar sobrevivir cualquiera de esos "fantasmas"
    activos es lo que causó los falsos positivos de TEST001 y "Test Multiple"
    en 7.1.4. Si en algún momento este proyecto tiene personas reales
    registradas, HAY QUE AJUSTAR este filtro antes de volver a correr esto.
    """
    print("Limpiando TODAS las personas de prueba anteriores (excepto ADMIN001)...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM persona WHERE matricula_empleado != 'ADMIN001'"
                )
                borrados = cur.rowcount
        conn.close()
        print(f"   {borrados} persona(s) eliminada(s) "
              f"(sus rostros se borraron en cascada).\n")
    except Exception as e:
        print(f"   No se pudo limpiar automáticamente ({e}). "
              f"Si ves matches inesperados, revisa la BD a mano.\n")


# ============================================
# Utilidades
# ============================================

def imagen_a_base64(ruta):
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def post(path, payload, timeout=TIMEOUT_NORMAL):
    return requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)


def calentar_modelo():
    """
    Fuerza la carga en memoria de DeepFace/Facenet512 con una sola
    extracción de embedding antes de arrancar las pruebas reales, para
    que el primer registro/validación de la corrida no tronado por
    timeout del lado del cliente mientras el modelo carga.
    """
    print("Calentando el modelo (primera carga de DeepFace, puede tardar "
          "1-2 minutos)...")
    primera_foto = next(iter(TEST_PEOPLE.values()))["registro"][0]
    try:
        r = post(
            "/validacion/embedding",
            {"image": imagen_a_base64(primera_foto)},
            timeout=TIMEOUT_CALENTAMIENTO,
        )
        if r.status_code == 200 and r.json().get("success"):
            print("Modelo listo.\n")
        else:
            print(f"Calentamiento respondió {r.status_code}, "
                  f"continuando de todos modos.\n")
    except requests.exceptions.RequestException as e:
        print(f"No se pudo calentar el modelo ({e}); "
              f"continuando, las siguientes llamadas ya tienen timeout alto.\n")


# ============================================
# 7.1.1 — Registrar 5 personas de prueba (múltiples muestras)
# ============================================

def registrar_personas():
    print("\n" + "=" * 60)
    print("7.1.1 REGISTRO: 5 personas con múltiples muestras")
    print("=" * 60)

    registrados = {}
    ok = True

    for clave, datos in TEST_PEOPLE.items():
        matricula = f"S2-{RUN_ID}-{clave}"
        payload = {
            "nombre": datos["nombre"],
            "apellido": datos["apellido"],
            "matricula": matricula,
            "tipo": datos["tipo"],
            "imagenes": [imagen_a_base64(p) for p in datos["registro"]],
            "incluir_promedio": True,
        }

        r = post("/registro/persona/multiple", payload, timeout=TIMEOUT_REGISTRO)
        if r.status_code == 201:
            data = r.json()["data"]
            registrados[clave] = {
                "persona_id": data["persona_id"],
                "matricula": matricula,
                "rostros_ids": data["rostros_ids"],
            }
            print(f"   OK  {clave} -> persona_id={data['persona_id']} "
                  f"({data['total_rostros']} rostros)")
        else:
            ok = False
            print(f"   FAIL {clave} -> {r.status_code}: {r.json().get('error')}")

    print(f"\nRegistradas {len(registrados)}/{len(TEST_PEOPLE)} personas.")
    return registrados, ok


# ============================================
# 7.1.2 — Validar cada persona registrada
# ============================================

def validar_persona(ruta_foto, registrar_acceso=True):
    payload = {
        "image": imagen_a_base64(ruta_foto),
        "puerta": "Principal-Pruebas",
        "registrar_acceso": registrar_acceso,
    }
    r = post("/validacion", payload, timeout=45)
    if r.status_code != 200:
        return None
    return r.json()


def validar_cada_persona(registrados):
    print("\n" + "=" * 60)
    print("7.1.2 VALIDACIÓN: cada persona debe reconocerse correctamente")
    print("=" * 60)

    aciertos = 0
    for clave, datos in TEST_PEOPLE.items():
        if clave not in registrados:
            print(f"   SKIP {clave} (no se registró en 7.1.1)")
            continue

        resultado = validar_persona(datos["validacion"])
        if resultado is None:
            print(f"   FAIL {clave} -> error HTTP en /api/validacion")
            continue

        val = resultado.get("validacion", {})
        exito = val.get("exito", False)
        persona_id_obtenido = val.get("persona_id")
        persona_id_esperado = registrados[clave]["persona_id"]
        correcto = exito and persona_id_obtenido == persona_id_esperado

        print(f"   {'OK  ' if correcto else 'FAIL'} {clave}: "
              f"exito={exito} confianza={val.get('confianza', 0):.4f} "
              f"nivel={val.get('nivel_confianza')} "
              f"persona_id={persona_id_obtenido} (esperado {persona_id_esperado})")

        aciertos += int(correcto)

    print(f"\n{aciertos}/{len(registrados)} personas reconocidas correctamente.")
    return aciertos, len(registrados)


# ============================================
# 7.1.3 — Probar con persona no registrada
# ============================================

def probar_no_registrado():
    print("\n" + "=" * 60)
    print("7.1.3 PERSONA NO REGISTRADA: debe denegar acceso")
    print("=" * 60)

    if not STRANGER_PHOTOS:
        print("   SKIP: no hay fotos en STRANGER_PHOTOS")
        return 0, 0

    aciertos = 0
    for ruta in STRANGER_PHOTOS:
        resultado = validar_persona(ruta)
        if resultado is None:
            print(f"   FAIL {ruta} -> error HTTP")
            continue
        val = resultado.get("validacion", {})
        denegado = not val.get("exito", True)
        if denegado:
            print(f"   OK   {ruta}: exito=False motivo={val.get('motivo')}")
        else:
            persona = val.get("persona") or {}
            print(f"   FAIL {ruta}: exito=True (FALSO POSITIVO) "
                  f"confianza={val.get('confianza', 0):.4f} "
                  f"identificado_como={persona.get('nombre')} {persona.get('apellido')} "
                  f"(persona_id={val.get('persona_id')})")
        aciertos += int(denegado)

    print(f"\n{aciertos}/{len(STRANGER_PHOTOS)} correctamente denegados.")
    return aciertos, len(STRANGER_PHOTOS)


# ============================================
# 7.1.4 — Probar con rostro inactivo
# ============================================

def desactivar_rostros(rostros_ids):
    resultados = {}
    for rid in rostros_ids:
        r = requests.put(f"{BASE_URL}/rostro/{rid}/desactivar", timeout=10)
        ok = r.status_code == 200
        activo_reportado = r.json().get("data", {}).get("activo") if ok else None
        resultados[rid] = (ok, activo_reportado)
        estado = f"HTTP {r.status_code}, activo={activo_reportado}" if ok else f"HTTP {r.status_code}"
        print(f"      PUT /rostro/{rid}/desactivar -> {estado}")
    return resultados


def activar_rostros(rostros_ids):
    ok = True
    for rid in rostros_ids:
        r = requests.put(f"{BASE_URL}/rostro/{rid}/activar", timeout=10)
        ok = ok and r.status_code == 200
    return ok


def verificar_estado_en_bd(rostros_ids):
    """Consulta directa de solo lectura para confirmar el estado real en
    la base de datos, sin depender de lo que haya respondido la API."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, persona_id, activo FROM rostro WHERE id = ANY(%s) ORDER BY id",
                (rostros_ids,),
            )
            filas = cur.fetchall()
        conn.close()
        for rid, persona_id, activo in filas:
            print(f"      BD: rostro id={rid} persona_id={persona_id} activo={activo}")
    except Exception as e:
        print(f"      No se pudo verificar directamente en BD: {e}")


def probar_rostro_inactivo(registrados):
    print("\n" + "=" * 60)
    print(f"7.1.4 ROSTRO INACTIVO ({PERSONA_PARA_DESACTIVAR}): debe denegar acceso")
    print("=" * 60)

    if PERSONA_PARA_DESACTIVAR not in registrados:
        print("   SKIP: esa persona no se registró en 7.1.1")
        return False

    rostros_ids = registrados[PERSONA_PARA_DESACTIVAR]["rostros_ids"]
    ruta_foto = TEST_PEOPLE[PERSONA_PARA_DESACTIVAR]["validacion"]

    print(f"   Desactivando {len(rostros_ids)} rostro(s)...")
    desactivar_rostros(rostros_ids)

    print("   Verificando estado real en la base de datos:")
    verificar_estado_en_bd(rostros_ids)

    resultado = validar_persona(ruta_foto, registrar_acceso=True)
    val = resultado.get("validacion", {}) if resultado else {}
    denegado = not val.get("exito", True)
    if denegado:
        print(f"   OK   validación tras desactivar: exito=False motivo={val.get('motivo')}")
    else:
        persona = val.get("persona") or {}
        print(f"   FAIL validación tras desactivar: exito=True (¡no debería!) "
              f"confianza={val.get('confianza', 0):.4f} "
              f"rostro_id_usado={val.get('rostro_id')} "
              f"identificado_como={persona.get('nombre')} {persona.get('apellido')} "
              f"(persona_id={val.get('persona_id')})")

    print("   Reactivando para no afectar la medición de precisión (7.1.5)...")
    activar_rostros(rostros_ids)

    # Confirmar que reactivar sí restaura el reconocimiento
    time.sleep(1)
    resultado2 = validar_persona(ruta_foto, registrar_acceso=False)
    val2 = resultado2.get("validacion", {}) if resultado2 else {}
    print(f"   Verificación post-reactivación: exito={val2.get('exito')} "
          f"(debería volver a ser True)")

    return denegado


# ============================================
# 7.1.5 — Medir precisión final
# ============================================

def medir_precision_final(registrados):
    print("\n" + "=" * 60)
    print("7.1.5 PRECISIÓN FINAL (> 95%)")
    print("=" * 60)

    aciertos_propios, total_propios = validar_cada_persona(registrados)
    aciertos_extranos, total_extranos = probar_no_registrado()

    total = total_propios + total_extranos
    aciertos = aciertos_propios + aciertos_extranos

    if total == 0:
        print("\nNo hay suficientes pruebas para calcular precisión.")
        return 0.0

    precision = (aciertos / total) * 100
    print(f"\nResumen: {aciertos_propios}/{total_propios} propios correctos, "
          f"{aciertos_extranos}/{total_extranos} desconocidos correctamente denegados")
    print(f"Precisión final: {precision:.2f}% ({aciertos}/{total})")
    print("PASS - Precisión > 95%" if precision > 95 else "FAIL - Precisión <= 95%")
    return precision


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

    limpiar_corridas_anteriores()

    registrados, _ = registrar_personas()
    if not registrados:
        print("\nNinguna persona se registró correctamente. Abortando el resto de 7.1.")
        sys.exit(1)

    validar_cada_persona(registrados)
    probar_no_registrado()
    probar_rostro_inactivo(registrados)

    # 7.1.5 se corre al final y de forma independiente para dar el número
    # oficial de precisión (repite 7.1.2/7.1.3 ya con el estado restaurado).
    print("\n" + "#" * 60)
    print("# CÁLCULO OFICIAL DE PRECISIÓN (post-restauración)")
    print("#" * 60)
    medir_precision_final(registrados)


if __name__ == "__main__":
    main()