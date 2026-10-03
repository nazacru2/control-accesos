# backend/app/routes/registro.py
"""
Endpoints de registro biométrico
Fase 2.2 - Crear endpoint de registro de personas

Responsable: Ramírez Cruz Nazario
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from app.services.registro import RegistroService
from app.services.cache import get_embedding_cache   # 5.1.2

logger = logging.getLogger(__name__)

# Crear el blueprint
registro_bp = Blueprint('registro', __name__)

# Singleton del servicio
_service = None


def get_service() -> RegistroService:
    """Obtiene o crea la instancia del RegistroService."""
    global _service
    if _service is None:
        _service = RegistroService()
    return _service


# ============================================
# 2.2.2 — Endpoint POST /api/registro/persona
# ============================================
@registro_bp.route('/registro/persona', methods=['POST'])
def registrar_persona():
    """
    Registra una nueva persona con su primer rostro.

    POST /api/registro/persona

    Body (JSON):
        {
            "nombre": "Juan",
            "apellido": "Pérez",
            "matricula": "20240001",
            "tipo": "Estudiante",
            "imagen": "data:image/jpeg;base64,...",
            "correo": "juan@ejemplo.com",
            "telefono": "9511234567"
        }

    Responses:
        201 -> Registro exitoso
        400 -> Datos faltantes, tipo inválido, o sin rostro detectable
        409 -> Matrícula duplicada
        500 -> Error interno
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return _error("Cuerpo JSON requerido", 400)

        # 2.2.3 — Validación de campos requeridos
        campos_requeridos = ['nombre', 'apellido', 'matricula', 'tipo', 'imagen']
        faltantes = [c for c in campos_requeridos if not data.get(c)]

        if faltantes:
            return _error(
                f"Faltan campos requeridos: {', '.join(faltantes)}",
                400
            )

        nombre = str(data['nombre']).strip()
        apellido = str(data['apellido']).strip()
        matricula = str(data['matricula']).strip()
        tipo = str(data['tipo']).strip()
        imagen_b64 = data['imagen']
        correo = data.get('correo')
        telefono = data.get('telefono')

        if not nombre or not apellido or not matricula or not tipo:
            return _error("Los campos no pueden estar vacíos", 400)

        service = get_service()

        # NOTA: la validación de 'tipo' contra el CHECK constraint de la BD
        # ya NO se hace aquí. Vive una sola vez en RegistroService.validar_tipo(),
        # y la llaman tanto registrar_persona() como
        # registrar_persona_con_multiples_rostros(). Antes solo el endpoint
        # /multiple la tenía, por lo que un tipo inválido en este endpoint
        # simple caía al CHECK de Postgres y salía como error 500 en vez de 400.

        # 2.2.4 — Decodificación de imagen base64
        try:
            imagen = service.decodificar_base64(imagen_b64)
        except ValueError as e:
            return _error(f"Imagen inválida: {e}", 400)

        validacion = service.validar_imagen(imagen)
        if not validacion['valido']:
            return _error(validacion['mensaje'], 400)

        # 2.2.5 — Extracción del embedding con FaceRecognizer
        embedding = service.recognizer.extract_embedding(
            imagen, enforce_detection=True, align=True
        )

        if embedding is None:
            return _error(
                "No se pudo extraer el embedding facial. "
                "Verifique que el rostro sea claro y esté bien iluminado.",
                400
            )

        # 2.2.6 / 2.2.7 — Registro y manejo de errores
        try:
            resultado = service.registrar_persona(
                nombre=nombre,
                apellido=apellido,
                matricula=matricula,
                tipo=tipo,
                embedding=embedding,
                imagen_bgr=imagen,
                correo=correo,
                telefono=telefono,
            )
        except ValueError as e:
            mensaje = str(e)
            if "Ya existe" in mensaje:
                return _error(mensaje, 409)
            return _error(mensaje, 400)

        # 5.1.2 — Invalidar caché tras nuevo registro
        get_embedding_cache().invalidate('rostros_activos_count')

        logger.info(
            f"Registro exitoso: persona_id={resultado['persona_id']} "
            f"matricula={matricula}"
        )

        return jsonify({
            'success': True,
            'message': 'Persona registrada exitosamente',
            'data': resultado,
            'timestamp': datetime.utcnow().isoformat()
        }), 201

    except Exception as e:
        logger.exception(f"Error en /api/registro/persona: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 3.2 — Endpoint POST /api/registro/persona/multiple
# ============================================
@registro_bp.route('/registro/persona/multiple', methods=['POST'])
def registrar_persona_multiple():
    """
    Registra una nueva persona con múltiples muestras de rostro.

    POST /api/registro/persona/multiple

    Body (JSON):
        {
            "nombre": "Juan",
            "apellido": "Pérez",
            "matricula": "20240001",
            "tipo": "Estudiante",
            "imagenes": [
                "data:image/jpeg;base64,...",
                "data:image/jpeg;base64,...",
                "data:image/jpeg;base64,..."
            ],
            "correo": "juan@ejemplo.com",
            "telefono": "9511234567",
            "incluir_promedio": true
        }

    Responses:
        201 -> Registro exitoso
        400 -> Datos faltantes, tipo inválido, menos de 3 imágenes, o embedding inválido
        409 -> Matrícula duplicada
        500 -> Error interno
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return _error("Cuerpo JSON requerido", 400)

        # 3.2.2 — Validar campos requeridos
        campos_requeridos = ['nombre', 'apellido', 'matricula', 'tipo', 'imagenes']
        faltantes = [c for c in campos_requeridos if not data.get(c)]

        if faltantes:
            return _error(
                f"Faltan campos requeridos: {', '.join(faltantes)}",
                400
            )

        nombre = str(data['nombre']).strip()
        apellido = str(data['apellido']).strip()
        matricula = str(data['matricula']).strip()
        tipo = str(data['tipo']).strip()
        imagenes_b64 = data['imagenes']
        correo = data.get('correo')
        telefono = data.get('telefono')
        incluir_promedio = data.get('incluir_promedio', True)

        if not isinstance(imagenes_b64, list):
            return _error("El campo 'imagenes' debe ser una lista", 400)

        # 3.2.2 — Validar mínimo 3 muestras
        if len(imagenes_b64) < 3:
            return _error(
                f"Se requieren al menos 3 muestras de rostro, "
                f"se recibieron {len(imagenes_b64)}",
                400
            )

        # NOTA: la validación de 'tipo' ya no se duplica aquí — vive una sola
        # vez en RegistroService.validar_tipo() (ver comentario equivalente
        # en registrar_persona()).

        service = get_service()

        # 3.2.3 — Extraer embedding de cada imagen
        embeddings = []
        imagenes_bgr = []
        errores_muestras = []

        for i, img_b64 in enumerate(imagenes_b64):
            try:
                imagen = service.decodificar_base64(img_b64)
            except ValueError as e:
                errores_muestras.append(f"Muestra {i+1}: imagen inválida ({e})")
                continue

            embedding = service.recognizer.extract_embedding(
                imagen, enforce_detection=True, align=True
            )

            if embedding is None:
                errores_muestras.append(
                    f"Muestra {i+1}: no se detectó rostro o falló la extracción"
                )
                continue

            embeddings.append(embedding)
            imagenes_bgr.append(imagen)

        if len(embeddings) < 3:
            return _error(
                f"Solo {len(embeddings)} de {len(imagenes_b64)} muestras "
                f"fueron válidas. Se requieren al menos 3. "
                f"Errores: {'; '.join(errores_muestras)}",
                400
            )

        # 3.2.4 — Registrar persona + múltiples rostros en transacción única
        try:
            resultado = service.registrar_persona_con_multiples_rostros(
                nombre=nombre,
                apellido=apellido,
                matricula=matricula,
                tipo=tipo,
                embeddings=embeddings,
                imagenes_bgr=imagenes_bgr,
                correo=correo,
                telefono=telefono,
                incluir_promedio=incluir_promedio,
            )
        except ValueError as e:
            mensaje = str(e)
            if "Ya existe" in mensaje:
                return _error(mensaje, 409)
            return _error(mensaje, 400)

        # 5.1.2 — Invalidar caché tras nuevo registro
        get_embedding_cache().invalidate('rostros_activos_count')

        logger.info(
            f"Registro múltiple exitoso: persona_id={resultado['persona_id']} "
            f"matricula={matricula} rostros={resultado['total_rostros']}"
        )

        return jsonify({
            'success': True,
            'message': f"Persona registrada con {resultado['total_rostros']} rostros",
            'data': resultado,
            'timestamp': datetime.utcnow().isoformat()
        }), 201

    except Exception as e:
        logger.exception(f"Error en /api/registro/persona/multiple: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# Utilidad de error uniforme
# ============================================
def _error(mensaje: str, codigo: int):
    """Construye una respuesta JSON de error uniforme."""
    return jsonify({
        'success': False,
        'error': mensaje,
        'timestamp': datetime.utcnow().isoformat()
    }), codigo