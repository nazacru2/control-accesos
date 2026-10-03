# backend/app/routes/__init__.py
"""
Módulo de rutas de la API
Exporta los blueprints para cada endpoint
"""

from app.routes.health import health_bp
from app.routes.captura import captura_bp
from app.routes.validacion import validacion_bp
from app.routes.acceso import acceso_bp
from app.routes.registro import registro_bp     # Sprint 2 - Fase 2.2
from app.routes.personas import personas_bp     # 🆕 Sprint 2 - Fase 4.1

__all__ = [
    'health_bp',
    'captura_bp',
    'validacion_bp',
    'acceso_bp',
    'registro_bp',      # Sprint 2 - Fase 2.2
    'personas_bp',      # Sprint 2 - Fase 4.1
]