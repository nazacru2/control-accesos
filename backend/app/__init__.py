# backend/app/__init__.py
"""
Módulo principal de la aplicación Flask
Configuración e inicialización de servicios
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class):
    """
    Factory pattern para crear la aplicación Flask
    
    Args:
        config_class: Clase de configuración a utilizar
        
    Returns:
        Flask: Aplicación configurada
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # ============================================
    # 3.2.1 Configurar Flask app (YA CONFIGURADO)
    # ============================================
    
    # ============================================
    # 3.2.2 Configurar CORS
    # ============================================
    cors_config = config_class.get_cors_config() if hasattr(config_class, 'get_cors_config') else {}
    CORS(app, **cors_config)
    app.logger.info('CORS configurado')
    
    # ============================================
    # 3.2.3 Configurar base de datos
    # ============================================
    db.init_app(app)
    migrate.init_app(app, db)
    app.logger.info('Base de datos configurada')
    
    # Configurar logging
    configure_logging(app)
    
    # Registrar blueprints (rutas)
    register_blueprints(app)
    
    # Registrar manejadores de errores
    register_error_handlers(app)
    
    # Contexto de aplicación para comandos CLI
    @app.shell_context_processor
    def make_shell_context():
        from app.models import Persona, Rostro, Acceso
        return {
            'db': db,
            'Persona': Persona,
            'Rostro': Rostro,
            'Acceso': Acceso
        }
    
    app.logger.info('Aplicación inicializada correctamente')
    return app

def configure_logging(app):
    """Configura el sistema de logging"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Log de archivo con rotación
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # Log en consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Logging configurado')

def register_blueprints(app):
    """Registra todos los blueprints de rutas"""
    from app.routes import health_bp
    from app.routes import captura_bp
    from app.routes import validacion_bp
    from app.routes import acceso_bp
    
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(captura_bp, url_prefix='/api')
    app.register_blueprint(validacion_bp, url_prefix='/api')
    app.register_blueprint(acceso_bp, url_prefix='/api')
    
    app.logger.info('Blueprints registrados')

def register_error_handlers(app):
    """Registra manejadores de errores personalizados"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Error 500: {str(error)}')
        return jsonify({'error': 'Error interno del servidor'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Solicitud incorrecta'}), 400
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Método no permitido'}), 405
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'Archivo demasiado grande'}), 413
    
    app.logger.info('Manejadores de errores registrados')