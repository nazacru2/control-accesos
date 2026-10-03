"""
seed_test_persona.py
Registra una persona de prueba en la BD (Persona + Rostro con embedding real)
para poder probar 7.3.3 (/api/validacion) y 7.3.4 (/api/acceso/registrar)
de punta a punta.

Requiere: pip install psycopg2-binary requests

Uso:
    python seed_test_persona.py --foto fotos/persona1_a.jpeg --matricula TEST001
    python seed_test_persona.py --foto fotos/persona1_a.jpeg --matricula TEST001 --tipo Estudiante
"""

import argparse
import base64
import sys

import psycopg2
import requests

BASE_URL = "http://localhost:5000/api"

# Ajusta si tu docker-compose usa otros valores
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "control_accesos",
    "user": "admin",
    "password": "SecurePassword123!",  # el default de tu docker-compose.yml
}


def obtener_embedding(ruta_foto: str):
    """Llama a /api/validacion/embedding para obtener el embedding real de la foto."""
    with open(ruta_foto, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        f"{BASE_URL}/validacion/embedding",
        json={"image": img_b64},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if not result.get("success"):
        raise RuntimeError(f"No se pudo extraer embedding: {result.get('error')}")

    return result["embedding"]


def registrar_persona_y_rostro(embedding, matricula: str, imagen_respaldo: str, tipo: str):
    """Inserta directamente por SQL una Persona y su Rostro con el embedding."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # 1. Insertar (o reusar) la persona
            cur.execute(
                """
                INSERT INTO persona (nombre, apellido, matricula_empleado, tipo, activo, fecha_registro)
                VALUES (%s, %s, %s, %s, TRUE, NOW())
                ON CONFLICT (matricula_empleado) DO UPDATE SET nombre = EXCLUDED.nombre
                RETURNING id;
                """,
                ("Prueba", "Sprint1", matricula, tipo),
            )
            persona_id = cur.fetchone()[0]

            # 2. Insertar el rostro con el embedding real (cast explícito a vector)
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            cur.execute(
                """
                INSERT INTO rostro (persona_id, embedding, imagen_respaldo, fecha_captura, activo)
                VALUES (%s, %s::vector, %s, NOW(), TRUE)
                RETURNING id;
                """,
                (persona_id, embedding_str, imagen_respaldo),
            )
            rostro_id = cur.fetchone()[0]

        conn.commit()
        return persona_id, rostro_id
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Registra una persona de prueba con embedding real.")
    parser.add_argument("--foto", required=True, help="Ruta a la foto de la persona")
    parser.add_argument("--matricula", default="TEST001", help="Matrícula única de prueba")
    parser.add_argument(
        "--tipo",
        default="Estudiante",
        choices=["Estudiante", "Profesor", "Administrativo", "Visitante"],
        help="Tipo de persona (según el check constraint de la tabla)",
    )
    args = parser.parse_args()

    try:
        print(f"Extrayendo embedding de {args.foto} vía /api/validacion/embedding...")
        embedding = obtener_embedding(args.foto)
        print(f"Embedding obtenido: {len(embedding)} dimensiones")

        print("Insertando Persona + Rostro en la base de datos...")
        persona_id, rostro_id = registrar_persona_y_rostro(embedding, args.matricula, args.foto, args.tipo)

        print(f"\nListo. persona_id={persona_id}, rostro_id={rostro_id}")
        print("\nAhora puedes probar 7.3.3 mandando /api/validacion con esta MISMA foto")
        print("(o una foto distinta de la misma persona) y debería dar match=True.")
        print(f"\nY 7.3.4 con: {{'persona_id': {persona_id}, 'rostro_id': {rostro_id}, 'exito': true}}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()