# backend/app/routes/validacion.py
"""
Endpoint para validación de rostros
Fase 5.2 - Crear endpoint de validación
"""

from flask import Blueprint, request, jsonify
import base64
import cv2
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Optional, Any
from app.services.face_recognizer import FaceRecognizer
from app import db
from app.models import Persona, Rostro, Acceso
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Crear el blueprint
validacion_bp = Blueprint('validacion', __name__)

# Inicializar el servicio de reconocimiento
_recognizer = None

def get_recognizer():
    """Obtiene o crea una instancia del servicio de reconocimiento"""
    global _recognizer
    if _recognizer is None:
        _recognizer = FaceRecognizer(
            model_name='Facenet512',
            detector_backend='mtcnn',
            threshold=0.6
        )
    return _recognizer


# ============================================
# 5.2.2 Implementar endpoint /api/validacion
# ============================================

@validacion_bp.route('/validacion', methods=['POST'])
def validate_face():
    """
    Valida un rostro contra la base de datos
    POST /api/validacion
    
    Body:
        {
            "image": "base64_encoded_image",
            "umbral": 0.6,  # opcional
            "puerta": "Principal",  # opcional
            "registrar_acceso": true  # opcional
        }
    
    Returns:
        JSON con el resultado de la validación
    """
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({
                'error': 'Se requiere una imagen en base64',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Configurar umbral
        umbral = data.get('umbral', 0.6)
        puerta = data.get('puerta', 'Principal')
        registrar_acceso = data.get('registrar_acceso', True)
        
        # Decodificar imagen
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                'error': 'No se pudo decodificar la imagen',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # ============================================
        # 5.2.3 Implementar lógica de comparación
        # ============================================
        result = _process_validation(image, umbral, puerta, registrar_acceso)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error en /api/validacion: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def _process_validation(image: np.ndarray, 
                        umbral: float, 
                        puerta: str, 
                        registrar_acceso: bool) -> Dict[str, Any]:
    """
    Procesa la validación facial completa
    Fase 5.2.3 - Extraer embedding y comparar con BD
    """
    # 1. Detectar rostro en la imagen
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        return {
            'success': False,
            'message': 'No se detectaron rostros en la imagen',
            'faces_detected': 0,
            'validacion': {
                'exito': False,
                'motivo': 'No se detectó rostro'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # 2. Extraer el primer rostro detectado
    (x, y, w, h) = faces[0]
    face_image = image[y:y+h, x:x+w]
    face_image = cv2.resize(face_image, (160, 160))
    
    # 3. Extraer embedding usando DeepFace
    recognizer = get_recognizer()
    if not recognizer.is_available:
        return {
            'success': False,
            'message': 'Servicio de reconocimiento no disponible',
            'validacion': {
                'exito': False,
                'motivo': 'DeepFace no disponible'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    embedding = recognizer.extract_embedding(face_image)
    if embedding is None:
        return {
            'success': False,
            'message': 'No se pudo extraer el embedding facial',
            'faces_detected': 1,
            'validacion': {
                'exito': False,
                'motivo': 'Error al extraer embedding'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # 4. Buscar coincidencia en la base de datos
    match_result = _find_match_in_db(embedding, umbral)
    
    # 5. Registrar acceso si se solicita
    acceso_id = None
    if registrar_acceso and match_result.get('match', False):
        acceso_id = _registrar_acceso(
            rostro_id=match_result.get('rostro_id'),
            persona_id=match_result.get('persona_id'),
            exito=match_result.get('match', False),
            puerta=puerta,
            confianza=match_result.get('similarity', 0),
        )
    
    # 6. Construir respuesta
    response = {
        'success': True,
        'message': 'Validación completada',
        'faces_detected': 1,
        'validacion': {
            'exito': match_result.get('match', False),
            'confianza': match_result.get('similarity', 0),
            'umbral': umbral,
            'persona': match_result.get('persona'),
            'rostro_id': match_result.get('rostro_id'),
            'persona_id': match_result.get('persona_id')
        },
        'acceso': {
            # FIX: antes esto era simplemente el flag `registrar_acceso` que
            # llegó en el request, así que decía True aunque el guardado
            # hubiera fallado. Ahora refleja si de verdad se guardó.
            'registrado': acceso_id is not None,
            'acceso_id': acceso_id,
            'puerta': puerta
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Añadir motivo si no hay match
    if not match_result.get('match', False):
        if match_result.get('error'):
            response['validacion']['motivo'] = match_result.get('error')
        else:
            response['validacion']['motivo'] = 'No se encontró coincidencia'

    if registrar_acceso and match_result.get('match', False) and acceso_id is None:
        response['acceso']['motivo'] = 'Match encontrado pero el registro de acceso falló (ver logs del backend)'
    
    logger.info(f"Validación completada: match={match_result.get('match', False)}")
    return response


def _find_match_in_db(embedding: np.ndarray, umbral: float) -> Dict[str, Any]:
    """
    Busca una coincidencia en la base de datos usando pgvector
    Fase 5.2.3 - Comparar embedding con BD
    """
    try:
        # Convertir embedding a lista para JSON
        embedding_list = embedding.tolist()
        
        # Buscar usando pgvector directamente (sin depender de una función SQL)
        query = text("""
            SELECT 
                p.id as persona_id,
                p.nombre,
                p.apellido,
                p.matricula_empleado,
                p.tipo,
                r.id as rostro_id,
                r.imagen_respaldo,
                1 - (r.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM Rostro r
            JOIN Persona p ON r.persona_id = p.id
            WHERE p.activo = TRUE AND r.activo = TRUE
                AND 1 - (r.embedding <=> CAST(:embedding AS vector)) >= :umbral
            ORDER BY r.embedding <=> CAST(:embedding AS vector)
            LIMIT 1
        """)
        
        result = db.session.execute(query, {
            'embedding': embedding_list,
            'umbral': umbral
        }).fetchone()
        
        if result:
            return {
                'match': True,
                'persona_id': result.persona_id,
                'rostro_id': result.rostro_id,
                'similarity': float(result.similarity),
                'persona': {
                    'id': result.persona_id,
                    'nombre': result.nombre,
                    'apellido': result.apellido,
                    'matricula': result.matricula_empleado,
                    'tipo': result.tipo
                },
                'imagen_respaldo': result.imagen_respaldo
            }
        else:
            return {
                'match': False,
                'error': 'No se encontró coincidencia en la base de datos'
            }
            
    except Exception as e:
        logger.error(f"Error al buscar en BD: {str(e)}")
        return {
            'match': False,
            'error': f'Error en la base de datos: {str(e)}'
        }


def _registrar_acceso(rostro_id: int,
                       persona_id: int,
                       exito: bool,
                       puerta: str,
                       confianza: float) -> Optional[int]:
    """
    Registra un intento de acceso en la base de datos.

    FIX: antes llamaba a una función de Postgres `registrar_acceso(...)` que
    no existe en la base (psycopg2.errors.UndefinedFunction). Ahora usa el
    mismo modelo ORM `Acceso` que ya usa app/routes/acceso.py y que está
    confirmado funcionando (7.3.4), en vez de SQL crudo contra una función
    que nunca se creó.
    """
    try:
        nuevo_acceso = Acceso(
            rostro_id=rostro_id,
            persona_id=persona_id,
            exito=exito,
            puerta=puerta,
            confianza=confianza,
            imagen_intento=None,
            tiempo_deteccion=None,
            ip_origen=None,
            detalles='Acceso permitido' if exito else 'Acceso denegado - Credenciales no coinciden'
        )

        db.session.add(nuevo_acceso)
        db.session.commit()

        logger.info(f"Acceso registrado: ID={nuevo_acceso.id}, exito={exito}")
        return nuevo_acceso.id

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al registrar acceso: {str(e)}")
        return None


# ============================================
# ENDPOINTS ADICIONALES
# ============================================

@validacion_bp.route('/validacion/embedding', methods=['POST'])
def extract_embedding_endpoint():
    """
    Extrae el embedding de una imagen (sin comparar)
    POST /api/validacion/embedding
    """
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Se requiere una imagen en base64'}), 400
        
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'No se pudo decodificar la imagen'}), 400
        
        recognizer = get_recognizer()
        embedding = recognizer.extract_embedding(image)
        
        if embedding is None:
            return jsonify({
                'success': False,
                'error': 'No se pudo extraer el embedding'
            }), 400
        
        return jsonify({
            'success': True,
            'embedding': embedding.tolist(),
            'embedding_size': len(embedding),
            'model': recognizer.model_name,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /validacion/embedding: {str(e)}")
        return jsonify({'error': str(e)}), 500


@validacion_bp.route('/validacion/compare', methods=['POST'])
def compare_faces_endpoint():
    """
    Compara dos imágenes faciales
    POST /api/validacion/compare
    """
    try:
        data = request.get_json()
        if not data or 'image1' not in data or 'image2' not in data:
            return jsonify({
                'error': 'Se requieren image1 y image2 en base64'
            }), 400
        
        def decode_image(img_data):
            if ',' in img_data:
                img_data = img_data.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            np_array = np.frombuffer(img_bytes, np.uint8)
            return cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        image1 = decode_image(data['image1'])
        image2 = decode_image(data['image2'])
        
        if image1 is None or image2 is None:
            return jsonify({'error': 'No se pudieron decodificar las imágenes'}), 400
        
        recognizer = get_recognizer()
        emb1 = recognizer.extract_embedding(image1)
        emb2 = recognizer.extract_embedding(image2)
        
        if emb1 is None or emb2 is None:
            return jsonify({
                'success': False,
                'error': 'No se pudieron extraer los embeddings'
            }), 400
        
        similarity = recognizer.cosine_similarity(emb1, emb2)
        is_match = similarity >= recognizer.threshold
        
        return jsonify({
            'success': True,
            'similarity': similarity,
            'match': is_match,
            'threshold': recognizer.threshold,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /validacion/compare: {str(e)}")
        return jsonify({'error': str(e)}), 500