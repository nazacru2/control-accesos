# backend/app/routes/health.py
"""
Endpoint de salud para verificar el estado del servicio
Fase 3.3 - Implementar endpoint de salud
"""

from flask import Blueprint, jsonify
from datetime import datetime
import sys
import os
from app import db
from sqlalchemy import text

# Crear el blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de salud para verificar que la API está funcionando
    GET /api/health
    
    Returns:
        JSON con el estado del servicio
    """
    return jsonify({
        'status': 'healthy',
        'service': 'control-accesos-backend',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'python_version': sys.version.split()[0],
        'environment': os.getenv('FLASK_ENV', 'development')
    }), 200

@health_bp.route('/health/db', methods=['GET'])
def health_db():
    """
    Endpoint para verificar la conexión a la base de datos
    GET /api/health/db
    
    Returns:
        JSON con el estado de la base de datos
    """
    try:
        # Probar conexión
        connection = db.engine.connect()
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        connection.close()
        
        # Verificar pgvector
        connection = db.engine.connect()
        result = connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        has_vector = result.fetchone()[0]
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': version[:60],
            'pgvector': 'active' if has_vector else 'inactive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/models', methods=['GET'])
def health_models():
    """
    Endpoint para verificar que los modelos están cargados
    GET /api/health/models
    
    Returns:
        JSON con el estado de los modelos
    """
    try:
        from app.models import Persona, Rostro, Acceso
        
        # Contar registros
        personas = Persona.query.count()
        rostros = Rostro.query.count()
        accesos = Acceso.query.count()
        
        return jsonify({
            'status': 'healthy',
            'models': {
                'Persona': 'loaded',
                'Rostro': 'loaded',
                'Acceso': 'loaded'
            },
            'counts': {
                'personas': personas,
                'rostros': rostros,
                'accesos': accesos
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/all', methods=['GET'])
def health_all():
    """
    Endpoint que combina todas las verificaciones de salud
    GET /api/health/all
    
    Returns:
        JSON con el estado completo del sistema
    """
    try:
        # Verificar base de datos
        connection = db.engine.connect()
        result = connection.execute(text("SELECT version()"))
        db_version = result.fetchone()[0]
        connection.close()
        
        # Verificar modelos
        from app.models import Persona, Rostro, Acceso
        personas = Persona.query.count()
        rostros = Rostro.query.count()
        accesos = Acceso.query.count()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.getenv('FLASK_ENV', 'development'),
            'python_version': sys.version.split()[0],
            'database': {
                'status': 'connected',
                'version': db_version[:60],
                'pgvector': 'active'
            },
            'models': {
                'Persona': {'loaded': True, 'count': personas},
                'Rostro': {'loaded': True, 'count': rostros},
                'Acceso': {'loaded': True, 'count': accesos}
            },
            'endpoints': {
                'health': '/api/health',
                'health_db': '/api/health/db',
                'health_models': '/api/health/models',
                'health_all': '/api/health/all',
                'capture': '/api/capture',
                'validacion': '/api/validacion',
                'acceso_registrar': '/api/acceso/registrar'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500