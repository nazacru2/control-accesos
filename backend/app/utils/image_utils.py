# backend/app/utils/image_utils.py
"""
Utilidades para manejo de imágenes
"""

import base64
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from config import Config
import os

def decode_base64_image(base64_string):
    """
    Decodifica una imagen en formato base64 a un array de numpy
    
    Args:
        base64_string: String en formato base64
        
    Returns:
        numpy.ndarray: Imagen decodificada en formato BGR
    """
    try:
        # Remover el prefijo 'data:image/...;base64,' si existe
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decodificar base64
        image_data = base64.b64decode(base64_string)
        np_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        return image
    except Exception as e:
        raise ValueError(f"Error al decodificar imagen: {str(e)}")

def encode_image_to_base64(image, format='.jpg'):
    """
    Codifica una imagen a formato base64
    
    Args:
        image: Imagen en formato numpy.ndarray
        format: Formato de salida ('.jpg', '.png', etc.)
        
    Returns:
        str: Imagen codificada en base64
    """
    try:
        _, buffer = cv2.imencode(format, image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return image_base64
    except Exception as e:
        raise ValueError(f"Error al codificar imagen: {str(e)}")

def save_image(image, directory, prefix='', extension='.jpg'):
    """
    Guarda una imagen en el sistema de archivos
    
    Args:
        image: Imagen en formato numpy.ndarray
        directory: Directorio donde guardar
        prefix: Prefijo para el nombre del archivo
        extension: Extensión del archivo
        
    Returns:
        str: Ruta del archivo guardado
    """
    try:
        # Crear directorio si no existe
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Generar nombre único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{prefix}_{timestamp}{extension}"
        filepath = Path(directory) / filename
        
        # Guardar imagen
        cv2.imwrite(str(filepath), image)
        
        return str(filepath)
    except Exception as e:
        raise ValueError(f"Error al guardar imagen: {str(e)}")

def validate_image_format(image):
    """
    Valida que la imagen tenga un formato válido
    
    Args:
        image: Imagen en formato numpy.ndarray
        
    Returns:
        bool: True si es válida
    """
    if image is None:
        return False
    if not isinstance(image, np.ndarray):
        return False
    if len(image.shape) not in [2, 3]:
        return False
    return True

def get_image_dimensions(image):
    """
    Obtiene las dimensiones de una imagen
    
    Args:
        image: Imagen en formato numpy.ndarray
        
    Returns:
        tuple: (height, width, channels) o (height, width)
    """
    if len(image.shape) == 3:
        height, width, channels = image.shape
        return height, width, channels
    else:
        height, width = image.shape
        return height, width