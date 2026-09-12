# backend/app/routes/__init__.py
"""
Módulo de rutas de la API
Exporta los blueprints para cada endpoint
"""

from app.routes.health import health_bp
from app.routes.captura import captura_bp
from app.routes.validacion import validacion_bp
from app.routes.acceso import acceso_bp

__all__ = [
    'health_bp',
    'captura_bp',
    'validacion_bp',
    'acceso_bp'
]