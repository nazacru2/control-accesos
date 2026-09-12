# backend/app/models/__init__.py
"""
Módulo de modelos SQLAlchemy para el sistema de control de accesos
Sprint 1 - Alineado con checklist
"""

from app.models.persona import Persona
from app.models.rostro import Rostro
from app.models.acceso import Acceso

__all__ = ['Persona', 'Rostro', 'Acceso']