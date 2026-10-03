# test_umbral_dinamico.py
"""
Verificación de Fase 5.1.3 — Umbral dinámico
Captura un rostro y valida. La respuesta debe incluir:
  - nivel_confianza (alta/media/baja/ninguna)
  - requiere_verificacion (bool)
  - umbrales (dict con low y high)
"""
import sys
import requests
import json
from test_utils import capturar_frame, frame_a_data_uri, verificar_backend

API = "http://localhost:5000/api/validacion"


def main():
    print("=" * 60)
    print("TEST — Umbral dinámico (Fase 5.1.3)")
    print("=" * 60)

    if not verificar_backend():
        return 1

    try:
        frame = capturar_frame("Captura para validar")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1
    if frame is None:
        print("Cancelado")
        return 1

    payload = {
        "image": frame_a_data_uri(frame),
        "registrar_acceso": False,
    }

    r = requests.post(API, json=payload, timeout=120)
    print(f"\nStatus: {r.status_code}")
    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Verificar campos nuevos
    validacion = data.get('validacion', {})
    tiene_nivel = 'nivel_confianza' in validacion
    tiene_requiere = 'requiere_verificacion' in validacion
    tiene_umbrales = 'umbrales' in validacion

    print("\n" + "=" * 60)
    print("VERIFICACION DE CAMPOS FASE 5.1.3")
    print("=" * 60)
    print(f"  nivel_confianza:      {'OK' if tiene_nivel else 'FALTA'}")
    print(f"  requiere_verificacion: {'OK' if tiene_requiere else 'FALTA'}")
    print(f"  umbrales:             {'OK' if tiene_umbrales else 'FALTA'}")

    if tiene_nivel:
        print(f"\n  Nivel detectado: {validacion.get('nivel_confianza')}")
        print(f"  Confianza: {validacion.get('confianza'):.4f}")
        print(f"  Requiere verificacion: {validacion.get('requiere_verificacion')}")
        print(f"  Umbrales: {validacion.get('umbrales')}")

    if tiene_nivel and tiene_requiere and tiene_umbrales:
        print(f"\nTEST PASO")
        return 0
    else:
        print(f"\nTEST FALLO — faltan campos")
        return 1


if __name__ == '__main__':
    sys.exit(main())