# backend/app/services/__init__.py
"""
Módulo de servicios de la aplicación
Contiene la lógica de negocio
"""

from app.services.captura import FaceCapture
from app.services.face_recognizer import FaceRecognizer

__all__ = [
    'FaceCapture',
    'FaceRecognizer'
]