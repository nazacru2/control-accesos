# backend/app/routes/personas.py
"""
Endpoints de gestión de personas y rostros
Fase 4.1 - Activación/Desactivación de rostros

Responsable: Ramírez Cruz Nazario
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from app import db
from app.models import Persona, Rostro
from app.services.cache import get_embedding_cache   # 🆕 5.1.2

logger = logging.getLogger(__name__)

# Blueprint
personas_bp = Blueprint('personas', __name__)


# ============================================
# 4.1.1 — GET /api/personas
# ============================================
@personas_bp.route('/personas', methods=['GET'])
def listar_personas():
    """
    Lista todas las personas registradas.

    Query params opcionales:
        ?activo=true|false   (filtra por estado activo)
        ?tipo=Estudiante     (filtra por tipo)

    Returns:
        200: lista de personas
    """
    try:
        query = Persona.query

        activo_param = request.args.get('activo')
        if activo_param is not None:
            activo_bool = activo_param.lower() in ('true', '1', 'yes')
            query = query.filter(Persona.activo == activo_bool)

        tipo_param = request.args.get('tipo')
        if tipo_param:
            query = query.filter(Persona.tipo == tipo_param)

        personas = query.order_by(Persona.id.asc()).all()

        return jsonify({
            'success': True,
            'total': len(personas),
            'data': [p.to_dict() for p in personas],
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Error en GET /api/personas: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 4.1.2 — GET /api/persona/{id}
# ============================================
@personas_bp.route('/persona/<int:persona_id>', methods=['GET'])
def obtener_persona(persona_id: int):
    """
    Obtiene los datos de una persona por su ID.
    Incluye el conteo de rostros asociados.

    Returns:
        200: datos de la persona
        404: persona no encontrada
    """
    try:
        persona = Persona.query.get(persona_id)
        if persona is None:
            return _error(f"Persona con id={persona_id} no encontrada", 404)

        data = persona.to_dict()

        total_rostros = Rostro.query.filter_by(persona_id=persona_id).count()
        rostros_activos = Rostro.query.filter_by(
            persona_id=persona_id, activo=True
        ).count()

        data['total_rostros'] = total_rostros
        data['rostros_activos'] = rostros_activos

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Error en GET /api/persona/{persona_id}: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 4.1.3 — GET /api/rostros/{persona_id}
# ============================================
@personas_bp.route('/rostros/<int:persona_id>', methods=['GET'])
def listar_rostros(persona_id: int):
    """
    Lista todos los rostros de una persona.

    Query params opcionales:
        ?activo=true|false   (filtra por estado)

    Returns:
        200: lista de rostros
        404: persona no encontrada
    """
    try:
        persona = Persona.query.get(persona_id)
        if persona is None:
            return _error(f"Persona con id={persona_id} no encontrada", 404)

        query = Rostro.query.filter_by(persona_id=persona_id)

        activo_param = request.args.get('activo')
        if activo_param is not None:
            activo_bool = activo_param.lower() in ('true', '1', 'yes')
            query = query.filter(Rostro.activo == activo_bool)

        rostros = query.order_by(Rostro.id.asc()).all()

        data = []
        for r in rostros:
            data.append({
                'id': r.id,
                'persona_id': r.persona_id,
                'activo': r.activo,
                'imagen_respaldo': r.imagen_respaldo,
                'fecha_captura': r.fecha_captura.isoformat()
                if r.fecha_captura else None,
                'es_promedio': '_promedio_' in (r.imagen_respaldo or ''),
            })

        return jsonify({
            'success': True,
            'persona_id': persona_id,
            'persona': persona.nombre_completo,
            'total': len(data),
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Error en GET /api/rostros/{persona_id}: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 4.1.4 — PUT /api/rostro/{id}/activar
# ============================================
@personas_bp.route('/rostro/<int:rostro_id>/activar', methods=['PUT'])
def activar_rostro(rostro_id: int):
    """
    Activa un rostro para que se use en la validación facial.

    Returns:
        200: rostro activado
        404: rostro no encontrado
    """
    try:
        rostro = Rostro.query.get(rostro_id)
        if rostro is None:
            return _error(f"Rostro con id={rostro_id} no encontrado", 404)

        if rostro.activo:
            return jsonify({
                'success': True,
                'message': f'El rostro {rostro_id} ya estaba activo',
                'data': {
                    'id': rostro.id,
                    'persona_id': rostro.persona_id,
                    'activo': True,
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        rostro.activo = True
        db.session.commit()

        # 5.1.2 — Invalidar caché tras cambio de estado
        get_embedding_cache().invalidate('rostros_activos_count')

        logger.info(f"Rostro {rostro_id} activado (persona_id={rostro.persona_id})")

        return jsonify({
            'success': True,
            'message': f'Rostro {rostro_id} activado correctamente',
            'data': {
                'id': rostro.id,
                'persona_id': rostro.persona_id,
                'activo': rostro.activo,
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error al activar rostro {rostro_id}: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 4.1.5 — PUT /api/rostro/{id}/desactivar
# ============================================
@personas_bp.route('/rostro/<int:rostro_id>/desactivar', methods=['PUT'])
def desactivar_rostro(rostro_id: int):
    """
    Desactiva un rostro para que NO se use en la validación facial.

    Returns:
        200: rostro desactivado
        404: rostro no encontrado
    """
    try:
        rostro = Rostro.query.get(rostro_id)
        if rostro is None:
            return _error(f"Rostro con id={rostro_id} no encontrado", 404)

        if not rostro.activo:
            return jsonify({
                'success': True,
                'message': f'El rostro {rostro_id} ya estaba inactivo',
                'data': {
                    'id': rostro.id,
                    'persona_id': rostro.persona_id,
                    'activo': False,
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        rostro.activo = False
        db.session.commit()

        # 5.1.2 — Invalidar caché tras cambio de estado
        get_embedding_cache().invalidate('rostros_activos_count')

        logger.info(
            f"Rostro {rostro_id} desactivado (persona_id={rostro.persona_id})"
        )

        return jsonify({
            'success': True,
            'message': f'Rostro {rostro_id} desactivado correctamente',
            'data': {
                'id': rostro.id,
                'persona_id': rostro.persona_id,
                'activo': rostro.activo,
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error al desactivar rostro {rostro_id}: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# 4.1.6 — DELETE /api/rostro/{id}
# ============================================
@personas_bp.route('/rostro/<int:rostro_id>', methods=['DELETE'])
def eliminar_rostro(rostro_id: int):
    """
    Elimina un rostro (borrado lógico: se marca como inactivo).

    Por política del sistema, NUNCA se borra físicamente para
    preservar el historial de accesos.

    Returns:
        200: rostro eliminado lógicamente
        404: rostro no encontrado
    """
    try:
        rostro = Rostro.query.get(rostro_id)
        if rostro is None:
            return _error(f"Rostro con id={rostro_id} no encontrado", 404)

        # Borrado lógico
        rostro.activo = False
        db.session.commit()

        # 5.1.2 — Invalidar caché tras cambio de estado
        get_embedding_cache().invalidate('rostros_activos_count')

        logger.info(f"Rostro {rostro_id} eliminado (lógico)")

        return jsonify({
            'success': True,
            'message': f'Rostro {rostro_id} eliminado (marcado como inactivo)',
            'data': {
                'id': rostro.id,
                'persona_id': rostro.persona_id,
                'activo': rostro.activo,
                'eliminado_logicamente': True,
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error al eliminar rostro {rostro_id}: {e}")
        return _error(f"Error interno: {str(e)}", 500)


# ============================================
# Utilidad de error uniforme
# ============================================
def _error(mensaje: str, codigo: int):
    """Construye una respuesta JSON de error uniforme."""
    return jsonify({
        'success': False,
        'error': mensaje,
        'timestamp': datetime.utcnow().isoformat()
    }), codigo