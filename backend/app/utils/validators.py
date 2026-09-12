# backend/app/utils/validators.py
"""
Validadores para datos de entrada
"""

import re

TIPOS_PERMITIDOS = ['Estudiante', 'Profesor', 'Administrativo', 'Visitante']
PUERTAS_VALIDAS = ['Principal', 'Chedraui', 'Secundaria', 'Edificio I']

def validate_matricula(matricula):
    """
    Valida el formato de la matrícula/empleado
    
    Args:
        matricula: String con la matrícula
        
    Returns:
        bool: True si es válida
    """
    if not matricula:
        return False
    if not isinstance(matricula, str):
        return False
    # Matrícula: al menos 3 caracteres alfanuméricos
    return bool(re.match(r'^[A-Z0-9]{3,20}$', matricula.upper()))

def validate_tipo_persona(tipo):
    """
    Valida el tipo de persona
    
    Args:
        tipo: String con el tipo
        
    Returns:
        bool: True si es válido
    """
    return tipo in TIPOS_PERMITIDOS

def validate_puerta(puerta):
    """
    Valida el identificador de puerta
    
    Args:
        puerta: String con el nombre de la puerta
        
    Returns:
        bool: True si es válida
    """
    if not puerta:
        return True  # Es opcional
    return puerta in PUERTAS_VALIDAS or len(puerta) >= 3

def validate_confidence(confidence):
    """
    Valida el valor de confianza
    
    Args:
        confidence: Float con el porcentaje de confianza
        
    Returns:
        bool: True si es válido
    """
    if confidence is None:
        return True
    if not isinstance(confidence, (int, float)):
        return False
    return 0 <= confidence <= 100