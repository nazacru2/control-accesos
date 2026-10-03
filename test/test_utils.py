# test_utils.py
"""
Utilidades compartidas para los scripts de prueba del Sprint 2.
Evita duplicar la lógica de captura + codificación base64 en cada test.
"""
import base64
import json
import cv2
import requests


API_BASE = "http://localhost:5000/api"
API_REGISTRO = f"{API_BASE}/registro/persona"


def capturar_frame(mensaje="Presiona ESPACIO para capturar, ESC para cancelar"):
    """
    Captura un frame de la cámara del host.
    Versión mejorada con:
    - Ventana forzada al frente (topmost)
    - waitKey más largo (30ms) para mejor respuesta al teclado
    - Instrucciones visibles en pantalla
    - Contador en vivo
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(
            "No se pudo abrir la cámara. "
            "Verifica que no esté en uso por otra app (Zoom, Teams, etc.)"
        )

    # Configurar resolución (opcional, ayuda a algunas cámaras)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    window_name = "Captura - ESPACIO=capturar | ESC=cancelar"

    # Crear ventana explícitamente y traerla al frente
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    print(f"\n {mensaje}")
    print("   La ventana debería estar al frente.")
    print("   Si NO responde: haz clic en la ventana y prueba de nuevo.\n")

    frame = None
    intentos = 0

    # Primer frame para inicializar la ventana
    ret, img = cap.read()

    while True:
        ret, img = cap.read()
        if not ret:
            print("  No se pudo leer frame de la cámara")
            break

        # Instrucciones superpuestas en el video
        display = img.copy()
        cv2.putText(
            display,
            "ESPACIO = Capturar  |  ESC = Cancelar",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            display,
            f"Frame: {intentos}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1,
        )

        # Traer la ventana al frente (una vez cada 30 frames)
        if intentos % 30 == 0:
            try:
                cv2.setWindowProperty(
                    window_name,
                    cv2.WND_PROP_TOPMOST,
                    1,
                )
            except Exception:
                pass

        cv2.imshow(window_name, display)
        intentos += 1

        #  CLAVE: 30ms es suficiente para procesar eventos de teclado
        key = cv2.waitKey(30) & 0xFF

        if key == 32:      # ESPACIO
            frame = img    # frame sin texto superpuesto
            print(" Captura realizada")
            break
        elif key == 27:    # ESC
            print("  Cancelado por el usuario")
            break
        elif key == ord('q') or key == ord('Q'):
            print("  Cancelado (q)")
            break
        # Detectar si el usuario cerró la ventana con la X
        elif cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("  Ventana cerrada")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Dar tiempo a que se cierre la ventana antes de continuar
    for _ in range(5):
        cv2.waitKey(1)

    return frame


def frame_a_data_uri(frame):
    """Convierte un frame OpenCV a data URI base64."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{img_b64}"


def post_registro(payload, timeout=60):
    """Hace POST al endpoint de registro y devuelve la respuesta."""
    return requests.post(API_REGISTRO, json=payload, timeout=timeout)


def imprimir_respuesta(r):
    """Imprime status + JSON de la respuesta."""
    print(f"\n Status HTTP: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)


def validar_status(r, esperado, test_nombre):
    """
    Compara el status code y devuelve True/False, con mensaje uniforme.
    """
    if r.status_code == esperado:
        print(f"\n {test_nombre} PASÓ (status {esperado})")
        return True
    else:
        print(f"\n {test_nombre} FALLÓ "
              f"(esperado {esperado}, recibido {r.status_code})")
        return False


def verificar_backend():
    """Verifica que el backend esté arriba antes de empezar."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code == 200:
            print(f" Backend activo: {API_BASE}")
            return True
        print(f"  Backend responde {r.status_code} en /health")
        return False
    except requests.exceptions.ConnectionError:
        print(f" No se pudo conectar al backend en {API_BASE}")
        print("   ¿Está corriendo 'docker-compose up -d'?")
        return False