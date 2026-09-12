# backend/check_db.py
"""
Script para verificar la conexión a la base de datos
Fase 3.2.4 - Verificar conexión a BD
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app, db
from config import Config
from sqlalchemy import text

def check_db_connection():
    """Verifica la conexión a la base de datos"""
    print("=" * 60)
    print("VERIFICACIÓN DE CONEXIÓN A BASE DE DATOS")
    print("=" * 60)
    
    # Crear la aplicación
    app = create_app(Config)
    
    with app.app_context():
        try:
            # ============================================
            # 3.2.4 Probar con db.engine.connect()
            # ============================================
            print("\n1. Intentando conectar a la base de datos...")
            connection = db.engine.connect()
            print("   Conexión exitosa!")
            
            # Verificar versión de PostgreSQL
            print("\n2. Verificando versión de PostgreSQL...")
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   {version[:50]}...")
            
            # Verificar extensión vector
            print("\n3. Verificando extensión pgvector...")
            result = connection.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            )
            has_vector = result.fetchone()[0]
            print(f"   pgvector: {'ACTIVO' if has_vector else 'NO ACTIVO'}")
            
            # Verificar tablas
            print("\n4. Verificando tablas...")
            result = connection.execute(
                text("SELECT table_name FROM information_schema.tables "
                     "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"   Tablas encontradas: {', '.join(tables) if tables else 'ninguna'}")
            
            # Verificar tablas específicas
            required_tables = ['persona', 'rostro', 'acceso']
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                print(f"   Tablas faltantes: {', '.join(missing_tables)}")
            else:
                print("   Todas las tablas requeridas existen")
            
            # Contar registros
            print("\n5. Contando registros...")
            result = connection.execute(text("SELECT COUNT(*) FROM persona"))
            personas = result.fetchone()[0]
            print(f"   Personas: {personas}")
            
            result = connection.execute(text("SELECT COUNT(*) FROM rostro"))
            rostros = result.fetchone()[0]
            print(f"   Rostros: {rostros}")
            
            result = connection.execute(text("SELECT COUNT(*) FROM acceso"))
            accesos = result.fetchone()[0]
            print(f"   Accesos: {accesos}")
            
            # Probar inserción de prueba
            print("\n6. Probando inserción de prueba...")
            try:
                result = connection.execute(
                    text("INSERT INTO acceso (exito, puerta) "
                         "VALUES (TRUE, 'Verificacion') RETURNING id")
                )
                acceso_id = result.fetchone()[0]
                print(f"   Inserción exitosa (ID: {acceso_id})")
                
                # Limpiar datos de prueba
                connection.execute(text(f"DELETE FROM acceso WHERE id = {acceso_id}"))
                connection.commit()
                print("   Datos de prueba eliminados")
            except Exception as e:
                print(f"   Error en inserción de prueba: {str(e)}")
            
            # Cerrar conexión
            connection.close()
            
            print("\n" + "=" * 60)
            print("VERIFICACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            return True
            
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"ERROR DE CONEXIÓN: {str(e)}")
            print("=" * 60)
            print("\nPosibles causas:")
            print("1. PostgreSQL no está corriendo")
            print("2. Credenciales incorrectas")
            print("3. Base de datos no existe")
            print("4. Puerto incorrecto")
            print("5. Firewall bloqueando conexión")
            return False

if __name__ == '__main__':
    success = check_db_connection()
    sys.exit(0 if success else 1)