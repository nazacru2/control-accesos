# backend/app/routes/captura.py
"""
Endpoint para captura de rostros
Fase 4.2 - Crear endpoint de captura
"""

from flask import Blueprint, request, jsonify
import base64
import cv2
import numpy as np
from datetime import datetime
import os
import logging
from app.services.captura import FaceCapture
from app import db
from app.models import Persona, Rostro

logger = logging.getLogger(__name__)

# Crear el blueprint
captura_bp = Blueprint('captura', __name__)

# Inicializar el servicio de captura (se crea cuando se necesita)
_capturer = None

def get_capturer():
    """Obtiene o crea una instancia del servicio de captura"""
    global _capturer
    if _capturer is None:
        _capturer = FaceCapture(camera_index=0, width=640, height=480)
    return _capturer


# ============================================
# 4.2.2 Implementar endpoint /api/capture
# ============================================

@captura_bp.route('/capture', methods=['POST'])
def capture_face():
    """
    Captura un rostro desde una imagen en base64 o desde la cámara
    POST /api/capture
    
    Body (opción 1 - imagen en base64):
        {
            "image": "base64_encoded_image",
            "persona_id": 1,  # opcional
            "save": true      # opcional, guardar en disco
        }
    
    Body (opción 2 - capturar desde cámara):
        {
            "from_camera": true,
            "persona_id": 1,  # opcional
            "save": true      # opcional, guardar en disco
        }
    
    Returns:
        JSON con el resultado de la captura
    """
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Se requieren datos en el cuerpo de la solicitud'
            }), 400
        
        # Opción 1: Capturar desde imagen en base64
        if 'image' in data:
            return _capture_from_image(data)
        
        # Opción 2: Capturar desde cámara
        elif data.get('from_camera', False):
            return _capture_from_camera(data)
        
        else:
            return jsonify({
                'error': 'Se requiere "image" o "from_camera": true'
            }), 400
            
    except Exception as e:
        logger.error(f"Error en /api/capture: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def _capture_from_image(data):
    """
    Procesa captura desde una imagen en base64
    """
    try:
        # Decodificar imagen
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        np_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                'error': 'No se pudo decodificar la imagen'
            }), 400
        
        # Detectar rostros
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return jsonify({
                'success': False,
                'message': 'No se detectaron rostros en la imagen',
                'faces_detected': 0
            }), 200
        
        # Procesar cada rostro detectado
        face_images = []
        saved_paths = []
        save = data.get('save', False)
        persona_id = data.get('persona_id')
        
        for i, (x, y, w, h) in enumerate(faces):
            # Extraer rostro
            face = image[y:y+h, x:x+w]
            
            # Redimensionar para estandarizar
            face_resized = cv2.resize(face, (160, 160))
            
            face_info = {
                'id': i + 1,
                'bbox': [int(x), int(y), int(w), int(h)],
                'width': int(w),
                'height': int(h),
                'size': int(w * h)
            }
            
            # Guardar si se solicita
            if save:
                # Crear directorio si no existe
                capturas_dir = 'capturas'
                os.makedirs(capturas_dir, exist_ok=True)
                
                # Generar nombre único
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                if persona_id:
                    filename = f"{capturas_dir}/persona_{persona_id}_{timestamp}_face_{i}.jpg"
                else:
                    filename = f"{capturas_dir}/rostro_{timestamp}_face_{i}.jpg"
                
                cv2.imwrite(filename, face_resized)
                saved_paths.append(filename)
                face_info['saved_path'] = filename
            
            face_images.append(face_info)
        
        # Si hay persona_id, verificar que existe
        persona_info = None
        if persona_id:
            persona = Persona.query.get(persona_id)
            if persona:
                persona_info = {
                    'id': persona.id,
                    'nombre': persona.nombre,
                    'apellido': persona.apellido,
                    'matricula': persona.matricula_empleado
                }
            else:
                return jsonify({
                    'error': f'Persona con ID {persona_id} no encontrada'
                }), 404
        
        return jsonify({
            'success': True,
            'message': f'Se detectaron {len(faces)} rostros',
            'faces_detected': len(faces),
            'faces': face_images,
            'persona': persona_info,
            'saved': save,
            'saved_paths': saved_paths if save else [],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en _capture_from_image: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def _capture_from_camera(data):
    """
    Procesa captura desde la cámara
    """
    try:
        # Obtener capturer
        capturer = get_capturer()
        
        # Iniciar cámara si no está activa
        if not capturer.is_capturing:
            if not capturer.start_capture():
                return jsonify({
                    'error': 'No se pudo iniciar la cámara'
                }), 500
        
        # Capturar frame
        success, frame, faces = capturer.capture_frame()
        
        if not success or frame is None:
            return jsonify({
                'error': 'No se pudo capturar el frame'
            }), 500
        
        if len(faces) == 0:
            return jsonify({
                'success': False,
                'message': 'No se detectaron rostros en el frame',
                'faces_detected': 0
            }), 200
        
        # Procesar rostros
        face_images = []
        saved_paths = []
        save = data.get('save', False)
        persona_id = data.get('persona_id')
        
        for i, face_coords in enumerate(faces):
            # Extraer rostro
            face_image = capturer.get_face_image(frame, face_coords)
            
            if face_image is not None:
                face_info = {
                    'id': i + 1,
                    'bbox': [face_coords['x'], face_coords['y'], 
                            face_coords['width'], face_coords['height']],
                    'width': face_coords['width'],
                    'height': face_coords['height']
                }
                
                # Guardar si se solicita
                if save:
                    filepath = capturer.save_face_image(
                        face_image,
                        person_id=str(persona_id) if persona_id else None,
                        directory='capturas'
                    )
                    if filepath:
                        saved_paths.append(filepath)
                        face_info['saved_path'] = filepath
                
                face_images.append(face_info)
        
        # Información de persona
        persona_info = None
        if persona_id:
            persona = Persona.query.get(persona_id)
            if persona:
                persona_info = {
                    'id': persona.id,
                    'nombre': persona.nombre,
                    'apellido': persona.apellido,
                    'matricula': persona.matricula_empleado
                }
        
        return jsonify({
            'success': True,
            'message': f'Se detectaron {len(faces)} rostros',
            'faces_detected': len(faces),
            'faces': face_images,
            'persona': persona_info,
            'saved': save,
            'saved_paths': saved_paths if save else [],
            'camera_info': capturer.get_camera_info(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en _capture_from_camera: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# ============================================
# ENDPOINTS ADICIONALES
# ============================================

@captura_bp.route('/capture/start', methods=['POST'])
def start_camera():
    """
    Inicia la cámara
    POST /api/capture/start
    """
    try:
        capturer = get_capturer()
        if capturer.start_capture():
            return jsonify({
                'success': True,
                'message': 'Cámara iniciada correctamente',
                'camera_info': capturer.get_camera_info(),
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo iniciar la cámara'
            }), 500
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@captura_bp.route('/capture/stop', methods=['POST'])
def stop_camera():
    """
    Detiene la cámara
    POST /api/capture/stop
    """
    try:
        global _capturer
        if _capturer:
            _capturer.stop_capture()
            _capturer = None
        
        return jsonify({
            'success': True,
            'message': 'Cámara detenida correctamente',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@captura_bp.route('/capture/status', methods=['GET'])
def camera_status():
    """
    Obtiene el estado de la cámara
    GET /api/capture/status
    """
    try:
        global _capturer
        if _capturer:
            info = _capturer.get_camera_info()
            info['is_capturing'] = _capturer.is_capturing
            return jsonify({
                'success': True,
                'status': info
            }), 200
        else:
            return jsonify({
                'success': True,
                'status': {
                    'initialized': False,
                    'is_capturing': False,
                    'message': 'Cámara no inicializada'
                }
            }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500