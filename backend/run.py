# backend/run.py
"""
Punto de entrada de la aplicación Flask
Sistema de Control de Accesos - Sprint 1
"""

from app import create_app
from app import db
from config import Config

# Crear la aplicación
app = create_app(Config)

if __name__ == '__main__':
    # Ejecutar la aplicación en modo desarrollo
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )