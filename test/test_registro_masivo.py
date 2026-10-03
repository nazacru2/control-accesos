# test_registro_masivo.py
"""
Registra N personas con capturas rapidas.
Util para pruebas de escala (Fase 5.2.3).
"""
import sys
from datetime import datetime
import requests
from test_utils import capturar_frame, frame_a_data_uri, verificar_backend

API = "http://localhost:5000/api/registro/persona"


def main():
    print("=" * 60)
    print("REGISTRO MASIVO — 6 personas para escala")
    print("=" * 60)

    if not verificar_backend():
        return 1

    print("\nSe registraran 6 personas con capturas rapidas.")
    print("Captura la misma cara con diferentes angulos/expresiones.")

    for i in range(6):
        print(f"\n--- Persona {i+1}/6 ---")
        input("Presiona ENTER para capturar (o Ctrl+C para cancelar)...")

        try:
            frame = capturar_frame(f"Captura persona {i+1}/6")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            continue
        if frame is None:
            print(f"[SKIP] Persona {i+1} cancelada")
            continue

        timestamp = datetime.now().strftime("%H%M%S")
        matricula = f"ESC{i+1}{timestamp}"

        payload = {
            "nombre": f"Escala{i+1}",
            "apellido": "Test",
            "matricula": matricula,
            "tipo": "Estudiante",
            "imagen": frame_a_data_uri(frame),
        }

        try:
            r = requests.post(API, json=payload, timeout=60)
        except Exception as e:
            print(f"ERROR conexion: {e}")
            continue

        print(f"Status: {r.status_code}")
        if r.status_code == 201:
            data = r.json().get('data', {})
            print(f"OK: persona_id={data.get('persona_id')} matricula={matricula}")
        else:
            print(f"FALLO: {r.text[:300]}")

    print("\nListo. Corre test_escala_10_personas.py de nuevo.")
    return 0


if __name__ == '__main__':
    sys.exit(main())