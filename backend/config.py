# backend/config.py - Actualizado para coincidir con tu .env
"""
Configuración de la aplicación Flask
Variables de entorno y configuración de servicios
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # ============================================
    # 1. BASE DE DATOS
    # ============================================
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'control_accesos')
    DB_USER = os.getenv('DB_USER', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'SecurePassword123!')
    
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # ============================================
    # 2. SEGURIDAD DE LA API
    # ============================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_super_secreta_123456789')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    
    # ============================================
    # 3. CONFIGURACIÓN DE LA CÁMARA (Checklist 1.2.3)
    # ============================================
    CAMERA_TYPE = os.getenv('CAMERA_TYPE', 'usb')
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
    CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '640'))
    CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '480'))
    CAMERA_FPS = int(os.getenv('CAMERA_FPS', '30'))
    
    # ============================================
    # 4. CONFIGURACIÓN DE DEEPFACE (Checklist 1.2.4)
    # ============================================
    # NOTA: El checklist dice 'Facenet', pero tu .env usa 'Facenet512'
    # Facenet512 es una versión mejorada que genera embeddings de 512 dimensiones
    DEEPFACE_MODEL = os.getenv('DEEPFACE_MODEL', 'Facenet512')
    DEEPFACE_DETECTOR = os.getenv('DEEPFACE_DETECTOR', 'mtcnn')
    DEEPFACE_UMBRAL = float(os.getenv('DEEPFACE_UMBRAL', '0.75'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))
    DEEPFACE_ANTISP = os.getenv('DEEPFACE_ANTISP', 'ON') == 'ON'
    DEEPFACE_EMBEDDING_SIZE = 512  # Tamaño del embedding para Facenet512
    
    # ============================================
    # 5. CONFIGURACIÓN DEL BACKEND
    # ============================================
    FLASK_APP = os.getenv('FLASK_APP', 'app.main')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    TZ = os.getenv('TZ', 'America/Mexico_City')
    
    # ============================================
    # 6. CONFIGURACIÓN DE CORS (3.2.2)
    # ============================================
    FRONTEND_URL = os.getenv('VITE_API_URL', 'http://localhost:5000/api')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    CORS_HEADERS = ['Content-Type', 'Authorization', 'Accept']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']
    CORS_MAX_AGE = 3600
    
    # ============================================
    # 7. CONFIGURACIÓN DE ARCHIVOS
    # ============================================
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
    CAPTURAS_FOLDER = BASE_DIR / 'capturas'
    ROSTROS_FOLDER = BASE_DIR / 'rostros'
    LOGS_FOLDER = BASE_DIR / 'logs'
    MODELS_FOLDER = BASE_DIR / 'models'
    
    # Crear directorios si no existen
    for folder in [UPLOAD_FOLDER, CAPTURAS_FOLDER, ROSTROS_FOLDER, LOGS_FOLDER, MODELS_FOLDER]:
        folder.mkdir(exist_ok=True)
    
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png').split(','))
    
    # ============================================
    # 8. CONFIGURACIÓN DE CORREO (Opcional)
    # ============================================
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587')) if os.getenv('SMTP_PORT') else None
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM = os.getenv('SMTP_FROM', 'sistema@control-accesos.com')
    
    # ============================================
    # 9. CONFIGURACIÓN DE WEBSOCKET
    # ============================================
    WEBSOCKET_URL = os.getenv('VITE_WEBSOCKET_URL', 'ws://localhost:5000/ws')
    
    @classmethod
    def get_db_connection_params(cls):
        """Retorna los parámetros de conexión a la base de datos"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }
    
    @classmethod
    def get_cors_config(cls):
        """Retorna la configuración CORS"""
        return {
            'origins': cls.CORS_ORIGINS,
            'headers': cls.CORS_HEADERS,
            'methods': cls.CORS_METHODS,
            'expose_headers': cls.CORS_EXPOSE_HEADERS,
            'max_age': cls.CORS_MAX_AGE,
            'supports_credentials': True
        }
    
    @classmethod
    def is_allowed_file(cls, filename):
        """Verifica si la extensión del archivo está permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_deepface_config(cls):
        """Retorna la configuración de DeepFace"""
        return {
            'model_name': cls.DEEPFACE_MODEL,
            'detector_backend': cls.DEEPFACE_DETECTOR,
            'distance_metric': 'cosine',
            'enforce_detection': True,
            'align': True,
            'anti_spoofing': cls.DEEPFACE_ANTISP
        }


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    FLASK_DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Configuración para producción"""
    FLASK_DEBUG = False
    FLASK_ENV = 'production'
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = 'INFO'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost,http://localhost:80')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Configuración para pruebas"""
    FLASK_DEBUG = True
    FLASK_ENV = 'testing'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    CAMERA_TYPE = 'mock'
    CORS_ORIGINS = '*'


# Seleccionar configuración según entorno
ENV = os.getenv('FLASK_ENV', 'development')

if ENV == 'production':
    ActiveConfig = ProductionConfig
elif ENV == 'testing':
    ActiveConfig = TestingConfig
else:
    ActiveConfig = DevelopmentConfig