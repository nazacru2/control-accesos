# backend/app/services/captura.py
"""
Servicio de captura de rostros
Fase 4.1 - Implementar módulo de captura
"""

import cv2
import numpy as np
import os
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

class FaceCapture:
    """
    Clase para la captura y detección de rostros en tiempo real
    Sprint 1 - Módulo de captura de rostros
    """
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        """
        Inicializa el servicio de captura de rostros
        
        Args:
            camera_index: Índice de la cámara (default: 0)
            width: Ancho de la resolución (default: 640)
            height: Alto de la resolución (default: 480)
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.is_capturing = False
        self.face_cascade = None
        self.face_recognizer = None
        
        # Configurar detector de rostros
        self._init_face_detector()
        
        logger.info(f"FaceCapture inicializado: cámara {camera_index}, resolución {width}x{height}")
    
    def _init_face_detector(self):
        """Inicializa el clasificador de rostros de OpenCV"""
        try:
            # Usar el clasificador Haar Cascade de OpenCV
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("No se pudo cargar el clasificador de rostros")
                raise ValueError("No se pudo cargar el clasificador de rostros")
            
            logger.info("Detector de rostros inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar detector: {str(e)}")
            raise
    
    # ============================================
    # 4.1.3 Implementar método start_capture()
    # ============================================
    def start_capture(self) -> bool:
        """
        Inicializa la cámara para captura de video
        Fase 4.1.3 - Inicializa la cámara
        
        Returns:
            bool: True si la cámara se inicializó correctamente
        """
        try:
            # Liberar cámara existente si hay
            if self.cap is not None:
                self.stop_capture()
            
            # Inicializar cámara
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"No se pudo abrir la cámara {self.camera_index}")
                return False
            
            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Verificar configuración
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.is_capturing = True
            logger.info(f"Cámara {self.camera_index} inicializada: {actual_width}x{actual_height}")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar cámara: {str(e)}")
            self.is_capturing = False
            return False
    
    # ============================================
    # 4.1.4 Implementar método capture_frame()
    # ============================================
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[List[Dict]]]:
        """
        Captura un frame y detecta rostros
        Fase 4.1.4 - Captura y detecta rostros
        
        Returns:
            Tuple[bool, np.ndarray, List[Dict]]: 
                - Éxito de la captura
                - Frame capturado
                - Lista de rostros detectados con sus coordenadas
        """
        if not self.is_capturing or self.cap is None:
            logger.error("La cámara no está inicializada")
            return False, None, None
        
        try:
            # Capturar frame
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                logger.warning("No se pudo capturar el frame")
                return False, None, None
            
            # Convertir a escala de grises para detección
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detectar rostros
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Preparar lista de rostros detectados
            faces_list = []
            for (x, y, w, h) in faces:
                faces_list.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': 1.0  # Haar cascade no da confianza
                })
            
            # Dibujar rectángulos en los rostros detectados
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
            logger.debug(f"Frame capturado: {len(faces)} rostros detectados")
            return True, frame, faces_list
            
        except Exception as e:
            logger.error(f"Error al capturar frame: {str(e)}")
            return False, None, None
    
    # ============================================
    # 4.1.5 Implementar método get_face_image()
    # ============================================
    def get_face_image(self, frame: np.ndarray, face_coords: Dict) -> Optional[np.ndarray]:
        """
        Extrae el rostro del frame basado en coordenadas
        Fase 4.1.5 - Extrae el rostro del frame
        
        Args:
            frame: Imagen completa
            face_coords: Diccionario con x, y, width, height del rostro
            
        Returns:
            np.ndarray: Imagen del rostro recortada
        """
        try:
            if frame is None:
                logger.error("Frame nulo")
                return None
            
            if not face_coords or 'x' not in face_coords:
                logger.error("Coordenadas de rostro inválidas")
                return None
            
            x = face_coords.get('x', 0)
            y = face_coords.get('y', 0)
            w = face_coords.get('width', 0)
            h = face_coords.get('height', 0)
            
            # Validar coordenadas
            if w <= 0 or h <= 0:
                logger.error("Dimensiones de rostro inválidas")
                return None
            
            # Extraer el rostro
            face_image = frame[y:y+h, x:x+w]
            
            # Redimensionar para estandarizar
            face_image = cv2.resize(face_image, (160, 160))
            
            logger.debug(f"Rostro extraído: {face_image.shape}")
            return face_image
            
        except Exception as e:
            logger.error(f"Error al extraer rostro: {str(e)}")
            return None
    
    # ============================================
    # 4.1.6 Implementar método save_face_image()
    # ============================================
    def save_face_image(self, face_image: np.ndarray, 
                        person_id: Optional[str] = None,
                        directory: str = 'capturas') -> Optional[str]:
        """
        Guarda la imagen del rostro en disco
        Fase 4.1.6 - Guarda la imagen en disco
        
        Args:
            face_image: Imagen del rostro
            person_id: Identificador de la persona (para el nombre del archivo)
            directory: Directorio donde guardar
            
        Returns:
            str: Ruta del archivo guardado, o None si falló
        """
        try:
            if face_image is None:
                logger.error("Imagen de rostro nula")
                return None
            
            # Crear directorio si no existe
            Path(directory).mkdir(parents=True, exist_ok=True)
            
            # Generar nombre único
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            
            if person_id:
                filename = f"persona_{person_id}_{timestamp}.jpg"
            else:
                filename = f"rostro_{timestamp}.jpg"
            
            filepath = os.path.join(directory, filename)
            
            # Guardar imagen
            cv2.imwrite(filepath, face_image)
            
            logger.info(f"Imagen guardada: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error al guardar imagen: {str(e)}")
            return None
    
    # ============================================
    # 4.1.7 Implementar método stop_capture()
    # ============================================
    def stop_capture(self) -> bool:
        """
        Libera la cámara y recursos
        Fase 4.1.7 - Libera la cámara
        
        Returns:
            bool: True si se liberó correctamente
        """
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                logger.info("Cámara liberada")
            
            self.is_capturing = False
            logger.info("Captura detenida")
            return True
            
        except Exception as e:
            logger.error(f"Error al detener captura: {str(e)}")
            return False
    
    # ============================================
    # MÉTODOS ADICIONALES PARA FUNCIONALIDAD EXTRA
    # ============================================
    
    def capture_multiple(self, num_frames: int = 10, 
                         min_faces: int = 1) -> List[np.ndarray]:
        """
        Captura múltiples frames y extrae rostros
        Útil para obtener varias muestras de una persona
        
        Args:
            num_frames: Número de frames a capturar
            min_faces: Número mínimo de rostros requeridos
            
        Returns:
            List[np.ndarray]: Lista de imágenes de rostros
        """
        faces_collected = []
        
        for i in range(num_frames):
            success, frame, faces = self.capture_frame()
            
            if success and frame is not None and faces:
                # Tomar el primer rostro detectado
                face_image = self.get_face_image(frame, faces[0])
                if face_image is not None:
                    faces_collected.append(face_image)
            
            # Si ya tenemos suficientes rostros, terminar
            if len(faces_collected) >= min_faces:
                break
        
        return faces_collected
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la cámara
        
        Returns:
            Dict: Información de la cámara
        """
        if self.cap is None:
            return {
                'status': 'not_initialized',
                'camera_index': self.camera_index
            }
        
        return {
            'status': 'running' if self.is_capturing else 'stopped',
            'camera_index': self.camera_index,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST)
        }
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Cambia la resolución de la cámara
        
        Args:
            width: Nuevo ancho
            height: Nuevo alto
            
        Returns:
            bool: True si se cambió correctamente
        """
        if self.cap is None:
            logger.error("Cámara no inicializada")
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Resolución cambiada a: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            logger.error(f"Error al cambiar resolución: {str(e)}")
            return False
    
    def __del__(self):
        """Destructor: asegura que la cámara se libere"""
        self.stop_capture()