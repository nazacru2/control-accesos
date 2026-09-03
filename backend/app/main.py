# ============================================
# SISTEMA DE CONTROL DE ACCESOS - BACKEND
# Punto de entrada principal (main.py)
# ============================================

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
import os
from dotenv import load_dotenv
import logging

# ============================================
# 1. CONFIGURACIÓN DE LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# 2. CARGAR VARIABLES DE ENTORNO
# ============================================
load_dotenv()

# ============================================
# 3. INICIALIZAR APLICACIÓN FLASK
# ============================================
app = Flask(__name__)

# Configuración de CORS
CORS(app)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER', 'admin')}:"
    f"{os.getenv('DB_PASSWORD', 'SecurePassword123!')}@"
    f"{os.getenv('DB_HOST', 'postgres')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'control_accesos')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_super_secreta_123456789')

# Inicializar SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuración de límite de peticiones
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ============================================
# 4. RUTAS DE LA API
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del servicio"""
    return jsonify({
        'status': 'healthy',
        'service': 'control-accesos-backend',
        'version': '1.0.0',
        'timestamp': '2026-08-27T11:00:00Z'
    }), 200

@app.route('/api/', methods=['GET'])
def index():
    """Endpoint raíz de la API"""
    return jsonify({
        'message': 'API de Control de Accesos',
        'version': '1.0.0',
        'endpoints': {
            '/api/health': 'Verificar estado del servicio',
            '/api/db-test': 'Verificar conexión a la base de datos',
            '/api/': 'Información de la API'
        }
    }), 200

@app.route('/api/db-test', methods=['GET'])
def db_test():
    """Endpoint para verificar conexión a la base de datos"""
    try:
        # Ejecutar una consulta simple usando text()
        result = db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'connected',
            'message': 'Database connection successful'
        }), 200
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}'
        }), 500

# ============================================
# 5. MANEJADORES DE ERRORES
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# 6. PUNTO DE ENTRADA
# ============================================

if __name__ == '__main__':
    logger.info("Starting Control de Accesos Backend...")
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )