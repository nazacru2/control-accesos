"""
Servicio de reconocimiento facial
Fase 5.1 - Implementar módulo de reconocimiento facial
"""

import cv2
import numpy as np
import os
import logging
from typing import Optional, Tuple, List, Dict, Any, Union
from pathlib import Path
import time
import json

# Importar DeepFace
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logging.warning("DeepFace no está disponible. Instalar con: pip install deepface")

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """
    Clase para el reconocimiento facial usando DeepFace
    Sprint 1 - Módulo de reconocimiento facial
    
    Características:
    - Extracción de embeddings faciales
    - Comparación de similitud (coseno)
    - Validación de rostros contra base de datos
    """
    
    def __init__(self, 
                 model_name: str = 'Facenet',
                 detector_backend: str = 'mtcnn',
                 distance_metric: str = 'cosine',
                 threshold: float = 0.6):
        """
        Inicializa el servicio de reconocimiento facial
        
        Args:
            model_name: Modelo de DeepFace ('Facenet', 'Facenet512', 'VGG-Face', etc.)
            detector_backend: Detector de rostros ('mtcnn', 'opencv', 'retinaface')
            distance_metric: Métrica de distancia ('cosine', 'euclidean', 'euclidean_l2')
            threshold: Umbral de similitud (0-1) para considerar un match
        """
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric
        self.threshold = threshold
        self.is_available = DEEPFACE_AVAILABLE
        
        if not self.is_available:
            logger.error("DeepFace no está disponible. El reconocimiento facial no funcionará.")
        else:
            logger.info(f"FaceRecognizer inicializado: model={model_name}, detector={detector_backend}")
            
        # Cache de embeddings para optimización
        self.embedding_cache = {}
        self.cache_size = 1000
    
    # ============================================
    # 5.1.3 Implementar método extract_embedding()
    # ============================================
    def extract_embedding(self, 
                          face_image: np.ndarray,
                          enforce_detection: bool = True,
                          align: bool = True) -> Optional[np.ndarray]:
        """
        Extrae el embedding facial de una imagen de rostro usando DeepFace
        Fase 5.1.3 - Usa DeepFace para extraer embedding
        
        Args:
            face_image: Imagen del rostro en formato numpy.ndarray (BGR)
            enforce_detection: Si debe forzar la detección de rostro
            align: Si debe alinear el rostro antes de extraer
            
        Returns:
            np.ndarray: Vector de embedding (128 o 512 dimensiones) o None si falla
        """
        if not self.is_available:
            logger.error("DeepFace no está disponible")
            return None
        
        if face_image is None:
            logger.error("Imagen de rostro nula")
            return None
        
        try:
            # Convertir BGR a RGB si es necesario (DeepFace usa RGB)
            if len(face_image.shape) == 3 and face_image.shape[2] == 3:
                # Asumimos que la imagen está en BGR (OpenCV)
                face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            else:
                face_rgb = face_image
            
            # Extraer embedding usando DeepFace
            start_time = time.time()
            
            embeddings = DeepFace.represent(
                img_path=face_rgb,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=enforce_detection,
                align=align
            )
            
            elapsed_time = (time.time() - start_time) * 1000  # ms
            
            if not embeddings or len(embeddings) == 0:
                logger.warning("No se pudo extraer embedding")
                return None
            
            # Obtener el primer embedding
            embedding = np.array(embeddings[0]['embedding'])
            
            logger.debug(f"Embedding extraído: {len(embedding)} dimensiones, tiempo: {elapsed_time:.2f}ms")
            return embedding
            
        except Exception as e:
            logger.error(f"Error al extraer embedding: {str(e)}")
            return None
    
    def extract_embedding_from_file(self, 
                                    image_path: str,
                                    enforce_detection: bool = True) -> Optional[np.ndarray]:
        """
        Extrae el embedding facial de un archivo de imagen
        
        Args:
            image_path: Ruta al archivo de imagen
            enforce_detection: Si debe forzar la detección de rostro
            
        Returns:
            np.ndarray: Vector de embedding o None si falla
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Archivo no encontrado: {image_path}")
                return None
            
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"No se pudo cargar la imagen: {image_path}")
                return None
            
            return self.extract_embedding(image, enforce_detection)
            
        except Exception as e:
            logger.error(f"Error al extraer embedding de archivo: {str(e)}")
            return None
    
    def extract_embedding_from_base64(self, 
                                      base64_string: str,
                                      enforce_detection: bool = True) -> Optional[np.ndarray]:
        """
        Extrae el embedding facial de una imagen en base64
        
        Args:
            base64_string: Imagen codificada en base64
            enforce_detection: Si debe forzar la detección de rostro
            
        Returns:
            np.ndarray: Vector de embedding o None si falla
        """
        try:
            import base64
            import cv2
            import numpy as np
            
            # Decodificar base64
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_bytes = base64.b64decode(base64_string)
            np_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("No se pudo decodificar la imagen base64")
                return None
            
            return self.extract_embedding(image, enforce_detection)
            
        except Exception as e:
            logger.error(f"Error al extraer embedding de base64: {str(e)}")
            return None
    
    # ============================================
    # 5.1.4 Implementar método cosine_similarity()
    # ============================================
    def cosine_similarity(self, 
                          embedding1: np.ndarray, 
                          embedding2: np.ndarray) -> float:
        """
        Calcula la similitud del coseno entre dos embeddings
        Fase 5.1.4 - Calcula similitud entre vectores
        
        Args:
            embedding1: Primer vector de embedding
            embedding2: Segundo vector de embedding
            
        Returns:
            float: Similitud del coseno (0-1), donde 1 es idéntico
        """
        try:
            if embedding1 is None or embedding2 is None:
                logger.error("Embeddings nulos")
                return 0.0
            
            # Convertir a numpy arrays si no lo son
            if not isinstance(embedding1, np.ndarray):
                embedding1 = np.array(embedding1)
            if not isinstance(embedding2, np.ndarray):
                embedding2 = np.array(embedding2)
            
            # Verificar dimensiones
            if len(embedding1) != len(embedding2):
                logger.error(f"Dimensiones diferentes: {len(embedding1)} vs {len(embedding2)}")
                return 0.0
            
            # Calcular similitud del coseno
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                logger.warning("Norma cero en embeddings")
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Asegurar que el valor esté en el rango [0, 1]
            similarity = max(0.0, min(1.0, similarity))
            
            # FIX: dot_product/norm1/norm2 son numpy.float64. Sin este cast,
            # cualquier comparación posterior (similarity >= threshold) da
            # numpy.bool_, que Flask/json NO puede serializar
            # ("Object of type bool_ is not JSON serializable"). Con float()
            # nativo, esa comparación ya da un bool normal de Python.
            similarity = float(similarity)
            
            logger.debug(f"Similitud calculada: {similarity:.4f}")
            return similarity
            
        except Exception as e:
            logger.error(f"Error al calcular similitud: {str(e)}")
            return 0.0
    
    def euclidean_distance(self, 
                          embedding1: np.ndarray, 
                          embedding2: np.ndarray) -> float:
        """
        Calcula la distancia euclidiana entre dos embeddings
        
        Args:
            embedding1: Primer vector de embedding
            embedding2: Segundo vector de embedding
            
        Returns:
            float: Distancia euclidiana
        """
        try:
            if embedding1 is None or embedding2 is None:
                return float('inf')
            
            return np.linalg.norm(embedding1 - embedding2)
            
        except Exception as e:
            logger.error(f"Error al calcular distancia euclidiana: {str(e)}")
            return float('inf')
    
    # ============================================
    # MÉTODOS ADICIONALES PARA FUNCIONALIDAD EXTRA
    # ============================================
    
    def compare_faces(self, 
                      embedding1: np.ndarray, 
                      embedding2: np.ndarray,
                      method: str = 'cosine') -> Dict[str, Any]:
        """
        Compara dos embeddings y devuelve el resultado completo
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
            method: Método de comparación ('cosine', 'euclidean')
            
        Returns:
            Dict: Resultados de la comparación
        """
        result = {
            'similarity': 0.0,
            'distance': 0.0,
            'match': False,
            'method': method,
            'threshold': self.threshold
        }
        
        if method == 'cosine':
            similarity = self.cosine_similarity(embedding1, embedding2)
            result['similarity'] = similarity
            result['distance'] = 1 - similarity
            result['match'] = similarity >= self.threshold
            
        elif method == 'euclidean':
            distance = self.euclidean_distance(embedding1, embedding2)
            result['distance'] = distance
            # Convertir distancia a similitud aproximada
            result['similarity'] = max(0, 1 - (distance / 2))
            # FIX: antes tenía un umbral hardcodeado (0.8) que ignoraba
            # self.threshold, inconsistente con la rama 'cosine'.
            result['match'] = result['similarity'] >= self.threshold
            
        return result
    
    def find_best_match(self, 
                        embedding: np.ndarray, 
                        embeddings_list: List[np.ndarray],
                        ids_list: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Encuentra el mejor match entre un embedding y una lista de embeddings
        
        Args:
            embedding: Embedding a buscar
            embeddings_list: Lista de embeddings para comparar
            ids_list: Lista de IDs correspondientes a los embeddings
            
        Returns:
            Dict: Mejor match encontrado
        """
        # FIX: "not embedding" truena con ValueError en numpy arrays
        # ("the truth value of an array with more than one element is
        # ambiguous"). Hay que comparar explícitamente contra None.
        if embedding is None or not embeddings_list:
            return {
                'match': False,
                'similarity': 0.0,
                'index': -1,
                'id': None
            }
        
        best_match = {
            'match': False,
            'similarity': 0.0,
            'index': -1,
            'id': None
        }
        
        for i, emb in enumerate(embeddings_list):
            similarity = self.cosine_similarity(embedding, emb)
            
            if similarity > best_match['similarity']:
                best_match['similarity'] = similarity
                best_match['index'] = i
                if ids_list and i < len(ids_list):
                    best_match['id'] = ids_list[i]
        
        # Verificar si cumple con el umbral
        if best_match['similarity'] >= self.threshold:
            best_match['match'] = True
        
        return best_match
    
    def verify_face(self, 
                    face_image1: np.ndarray, 
                    face_image2: np.ndarray) -> Dict[str, Any]:
        """
        Verifica si dos imágenes corresponden a la misma persona
        
        Args:
            face_image1: Primera imagen de rostro
            face_image2: Segunda imagen de rostro
            
        Returns:
            Dict: Resultado de la verificación
        """
        try:
            # Extraer embeddings
            emb1 = self.extract_embedding(face_image1)
            if emb1 is None:
                return {'verified': False, 'error': 'No se pudo extraer embedding 1'}
            
            emb2 = self.extract_embedding(face_image2)
            if emb2 is None:
                return {'verified': False, 'error': 'No se pudo extraer embedding 2'}
            
            # Comparar
            result = self.compare_faces(emb1, emb2)
            result['verified'] = result['match']
            result['similarity'] = result['similarity']
            
            return result
            
        except Exception as e:
            logger.error(f"Error en verify_face: {str(e)}")
            return {'verified': False, 'error': str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información del modelo de reconocimiento facial
        
        Returns:
            Dict: Información del modelo
        """
        return {
            'available': self.is_available,
            'model_name': self.model_name,
            'detector_backend': self.detector_backend,
            'distance_metric': self.distance_metric,
            'threshold': self.threshold,
            'embedding_size': self.get_embedding_size()
        }
    
    def get_embedding_size(self) -> int:
        """
        Obtiene el tamaño del embedding según el modelo
        
        Returns:
            int: Tamaño del embedding
        """
        if self.model_name == 'Facenet512':
            return 512
        elif self.model_name == 'Facenet':
            return 128
        elif self.model_name == 'VGG-Face':
            return 4096
        elif self.model_name == 'OpenFace':
            return 128
        else:
            return 128  # Default
    
    def batch_extract_embeddings(self, 
                                 images: List[np.ndarray],
                                 progress_callback: Optional[callable] = None) -> List[Optional[np.ndarray]]:
        """
        Extrae embeddings de múltiples imágenes en lote
        
        Args:
            images: Lista de imágenes de rostros
            progress_callback: Función de callback para progreso
            
        Returns:
            List[np.ndarray]: Lista de embeddings (puede contener None)
        """
        embeddings = []
        total = len(images)
        
        for i, img in enumerate(images):
            emb = self.extract_embedding(img)
            embeddings.append(emb)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return embeddings
    
    def clear_cache(self):
        """Limpia el caché de embeddings"""
        self.embedding_cache = {}
        logger.info("Caché de embeddings limpiado")
    
    def __del__(self):
        """Destructor: limpia recursos"""
        self.clear_cache()