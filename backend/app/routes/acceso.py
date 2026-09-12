# backend/app/routes/acceso.py
"""
Endpoint para registro de accesos
Fase 6.1 - Crear servicio de registro
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import text, func

from app import db
from app.models import Acceso, Persona, Rostro

logger = logging.getLogger(__name__)

# Crear el blueprint
acceso_bp = Blueprint('acceso', __name__)


# ============================================
# 6.1.2 Implementar endpoint /api/acceso/registrar
# ============================================

@acceso_bp.route('/acceso/registrar', methods=['POST'])
def register_access():
    """
    Registra un intento de acceso en el sistema
    POST /api/acceso/registrar
    
    Body:
        {
            "rostro_id": 1,           # Opcional: ID del rostro reconocido
            "persona_id": 1,          # Opcional: ID de la persona
            "exito": true,            # Requerido: true/false
            "puerta": "Principal",    # Opcional: nombre de la puerta
            "confianza": 95.5,        # Opcional: porcentaje de confianza
            "imagen_intento": "base64_encoded_image",  # Opcional: imagen capturada
            "tiempo_deteccion": 150.0, # Opcional: tiempo en ms
            "ip_origen": "192.168.1.100", # Opcional: IP del dispositivo
            "detalles": "Acceso permitido" # Opcional: detalles adicionales
        }
    
    Returns:
        JSON con el resultado del registro
    """
    try:
        # Obtener datos de la solicitud
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Se requieren datos para el registro',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Validar campo requerido
        if 'exito' not in data:
            return jsonify({
                'error': 'El campo "exito" es requerido (true/false)',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # ============================================
        # 6.1.3 Implementar función register_access()
        # ============================================
        result = _register_access(data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error en /api/acceso/registrar: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def _register_access(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra un intento de acceso en la base de datos
    Fase 6.1.3 - Guarda intentos en BD
    
    Args:
        data: Diccionario con los datos del acceso
        
    Returns:
        Dict: Resultado del registro
    """
    try:
        # Extraer datos
        rostro_id = data.get('rostro_id')
        persona_id = data.get('persona_id')
        exito = data.get('exito', False)
        puerta = data.get('puerta', 'Principal')
        confianza = data.get('confianza')
        imagen_intento = data.get('imagen_intento')
        tiempo_deteccion = data.get('tiempo_deteccion')
        ip_origen = data.get('ip_origen', request.remote_addr)
        detalles = data.get('detalles')
        
        # Si no hay persona_id pero hay rostro_id, obtener persona_id del rostro
        if not persona_id and rostro_id:
            rostro = Rostro.query.get(rostro_id)
            if rostro:
                persona_id = rostro.persona_id
        
        # Validar que persona_id existe si se proporciona
        if persona_id:
            persona = Persona.query.get(persona_id)
            if not persona:
                return {
                    'success': False,
                    'error': f'Persona con ID {persona_id} no encontrada'
                }
        
        # Validar que rostro_id existe si se proporciona
        if rostro_id:
            rostro = Rostro.query.get(rostro_id)
            if not rostro:
                return {
                    'success': False,
                    'error': f'Rostro con ID {rostro_id} no encontrado'
                }
        
        # Crear registro de acceso usando SQLAlchemy
        nuevo_acceso = Acceso(
            rostro_id=rostro_id,
            persona_id=persona_id,
            exito=exito,
            puerta=puerta,
            confianza=confianza,
            imagen_intento=imagen_intento,
            tiempo_deteccion=tiempo_deteccion,
            ip_origen=ip_origen,
            detalles=detalles or _get_motivo(exito, persona_id)
        )
        
        db.session.add(nuevo_acceso)
        db.session.commit()
        
        logger.info(f"Acceso registrado: ID={nuevo_acceso.id}, exito={exito}, puerta={puerta}")
        
        return {
            'success': True,
            'message': 'Acceso registrado correctamente',
            'acceso_id': nuevo_acceso.id,
            'exito': nuevo_acceso.exito,
            'timestamp': nuevo_acceso.timestamp.isoformat() if nuevo_acceso.timestamp else None,
            'persona_id': persona_id,
            'rostro_id': rostro_id,
            'puerta': puerta
        }
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en _register_access: {str(e)}")
        return {
            'success': False,
            'error': f'Error al registrar acceso: {str(e)}'
        }


def _get_motivo(exito: bool, persona_id: Optional[int]) -> str:
    """
    Genera un motivo para el registro de acceso
    """
    if exito:
        return 'Acceso permitido'
    elif persona_id:
        return 'Acceso denegado - Credenciales no coinciden'
    else:
        return 'Persona no registrada en el sistema'


# ============================================
# ENDPOINTS ADICIONALES
# ============================================

@acceso_bp.route('/acceso/recientes', methods=['GET'])
def get_recent_access():
    """
    Obtiene los accesos más recientes
    GET /api/acceso/recientes?limit=10&puerta=Principal&exito=true
    
    Query Params:
        limit: Número de registros (default: 10, max: 100)
        puerta: Filtrar por puerta
        exito: Filtrar por éxito (true/false)
        persona_id: Filtrar por persona
    
    Returns:
        JSON con la lista de accesos
    """
    try:
        # Obtener parámetros
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Máximo 100 registros
        puerta = request.args.get('puerta')
        exito_str = request.args.get('exito')
        persona_id = request.args.get('persona_id', type=int)
        
        # Construir consulta
        query = Acceso.query
        
        if puerta:
            query = query.filter(Acceso.puerta == puerta)
        
        if exito_str is not None:
            exito = exito_str.lower() == 'true'
            query = query.filter(Acceso.exito == exito)
        
        if persona_id:
            query = query.filter(Acceso.persona_id == persona_id)
        
        # Ordenar y limitar
        accesos = query.order_by(
            Acceso.timestamp.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'count': len(accesos),
            'limit': limit,
            'accesos': [a.to_dict_complete() for a in accesos],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /api/acceso/recientes: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@acceso_bp.route('/acceso/estadisticas', methods=['GET'])
def get_access_stats():
    """
    Obtiene estadísticas de accesos
    GET /api/acceso/estadisticas?periodo=dia&puerta=Principal
    
    Query Params:
        periodo: dia, semana, mes (default: dia)
        puerta: Filtrar por puerta
    
    Returns:
        JSON con las estadísticas
    """
    try:
        periodo = request.args.get('periodo', 'dia')
        puerta = request.args.get('puerta')
        
        # Calcular fecha de inicio
        now = datetime.utcnow()
        if periodo == 'semana':
            fecha_inicio = now - timedelta(days=7)
        elif periodo == 'mes':
            fecha_inicio = now - timedelta(days=30)
        else:  # dia
            fecha_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Construir consulta
        query = Acceso.query.filter(Acceso.timestamp >= fecha_inicio)
        
        if puerta:
            query = query.filter(Acceso.puerta == puerta)
        
        # Estadísticas
        total = query.count()
        exitosos = query.filter(Acceso.exito == True).count()
        fallidos = total - exitosos
        
        # Tasa de éxito
        tasa_exito = (exitosos / total * 100) if total > 0 else 0
        
        # Accesos por puerta
        puertas_query = db.session.query(
            Acceso.puerta,
            func.count(Acceso.id).label('total'),
            func.sum(func.cast(Acceso.exito, db.Integer)).label('exitosos')
        ).filter(Acceso.timestamp >= fecha_inicio)
        
        if puerta:
            puertas_query = puertas_query.filter(Acceso.puerta == puerta)
        
        puertas_stats = puertas_query.group_by(Acceso.puerta).all()
        
        # Obtener persona más frecuente
        persona_frecuente = db.session.query(
            Acceso.persona_id,
            func.count(Acceso.id).label('total')
        ).filter(
            Acceso.timestamp >= fecha_inicio,
            Acceso.persona_id.isnot(None),
            Acceso.exito == True
        ).group_by(Acceso.persona_id).order_by(
            func.count(Acceso.id).desc()
        ).first()
        
        persona_info = None
        if persona_frecuente and persona_frecuente.persona_id:
            persona = Persona.query.get(persona_frecuente.persona_id)
            if persona:
                persona_info = {
                    'id': persona.id,
                    'nombre': persona.nombre,
                    'apellido': persona.apellido,
                    'matricula': persona.matricula_empleado,
                    'accesos': persona_frecuente.total
                }
        
        return jsonify({
            'success': True,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': now.isoformat(),
            'total': total,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'tasa_exito': round(tasa_exito, 2),
            'puertas': [
                {
                    'puerta': p.puerta,
                    'total': p.total,
                    'exitosos': p.exitosos or 0,
                    'tasa_exito': round((p.exitosos or 0) / p.total * 100, 2) if p.total > 0 else 0
                }
                for p in puertas_stats
            ],
            'persona_mas_frecuente': persona_info,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /api/acceso/estadisticas: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@acceso_bp.route('/acceso/persona/<int:persona_id>', methods=['GET'])
def get_access_by_persona(persona_id):
    """
    Obtiene los accesos de una persona específica
    GET /api/acceso/persona/{persona_id}?limit=20
    
    Query Params:
        limit: Número de registros (default: 20, max: 100)
    
    Returns:
        JSON con los accesos de la persona
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)
        
        # Verificar que la persona existe
        persona = Persona.query.get(persona_id)
        if not persona:
            return jsonify({
                'error': f'Persona con ID {persona_id} no encontrada'
            }), 404
        
        # Obtener accesos
        accesos = Acceso.query.filter_by(
            persona_id=persona_id
        ).order_by(
            Acceso.timestamp.desc()
        ).limit(limit).all()
        
        # Estadísticas de la persona
        total = Acceso.query.filter_by(persona_id=persona_id).count()
        exitosos = Acceso.query.filter_by(
            persona_id=persona_id,
            exito=True
        ).count()
        
        return jsonify({
            'success': True,
            'persona': persona.to_dict(),
            'estadisticas': {
                'total_accesos': total,
                'exitosos': exitosos,
                'fallidos': total - exitosos,
                'tasa_exito': round((exitosos / total * 100), 2) if total > 0 else 0
            },
            'accesos': [a.to_dict_complete() for a in accesos],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /api/acceso/persona/{persona_id}: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@acceso_bp.route('/acceso/puerta/<puerta>', methods=['GET'])
def get_access_by_puerta(puerta):
    """
    Obtiene los accesos de una puerta específica
    GET /api/acceso/puerta/{puerta}?limit=20
    
    Query Params:
        limit: Número de registros (default: 20, max: 100)
    
    Returns:
        JSON con los accesos de la puerta
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)
        
        # Obtener accesos
        accesos = Acceso.query.filter_by(
            puerta=puerta
        ).order_by(
            Acceso.timestamp.desc()
        ).limit(limit).all()
        
        # Estadísticas de la puerta
        total = Acceso.query.filter_by(puerta=puerta).count()
        exitosos = Acceso.query.filter_by(
            puerta=puerta,
            exito=True
        ).count()
        
        return jsonify({
            'success': True,
            'puerta': puerta,
            'estadisticas': {
                'total_accesos': total,
                'exitosos': exitosos,
                'fallidos': total - exitosos,
                'tasa_exito': round((exitosos / total * 100), 2) if total > 0 else 0
            },
            'accesos': [a.to_dict_complete() for a in accesos],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error en /api/acceso/puerta/{puerta}: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500