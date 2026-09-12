# backend/app/utils/__init__.py
"""
Módulo de utilidades de la aplicación
Funciones auxiliares para el sistema
"""

from app.utils.image_utils import (
    decode_base64_image,
    encode_image_to_base64,
    save_image,
    validate_image_format,
    get_image_dimensions
)

from app.utils.validators import (
    validate_matricula,
    validate_tipo_persona,
    validate_puerta,
    validate_confidence
)

__all__ = [
    'decode_base64_image',
    'encode_image_to_base64',
    'save_image',
    'validate_image_format',
    'get_image_dimensions',
    'validate_matricula',
    'validate_tipo_persona',
    'validate_puerta',
    'validate_confidence'
]