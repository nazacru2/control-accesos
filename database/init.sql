-- ============================================
-- SISTEMA DE CONTROL DE ACCESOS - SPRINT 0
-- Script de inicialización de base de datos
-- PostgreSQL + pgvector
-- ALINEADO CON CHECKLIST SPRINT 1
-- CORREGIDO: Error ROUND en vista
-- ============================================

-- ============================================
-- 1. ACTIVAR EXTENSIÓN pgvector
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 2. CREAR TABLAS PRINCIPALES
-- ============================================

-- 2.1 TABLA: Persona
CREATE TABLE IF NOT EXISTS Persona (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    matricula_empleado VARCHAR(20) UNIQUE NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Estudiante', 'Profesor', 'Administrativo', 'Visitante')),
    correo VARCHAR(100),
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 TABLA: Rostro
CREATE TABLE IF NOT EXISTS Rostro (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER NOT NULL REFERENCES Persona(id) ON DELETE CASCADE,
    embedding vector(512) NOT NULL,
    imagen_respaldo VARCHAR(255) NOT NULL,
    fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- 2.3 TABLA: Acceso
CREATE TABLE IF NOT EXISTS Acceso (
    id SERIAL PRIMARY KEY,
    rostro_id INTEGER REFERENCES Rostro(id) ON DELETE SET NULL,
    persona_id INTEGER REFERENCES Persona(id) ON DELETE SET NULL,
    embedding vector(512),
    imagen_intento VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exito BOOLEAN NOT NULL DEFAULT FALSE,
    puerta VARCHAR(50),
    confianza FLOAT,
    tiempo_deteccion FLOAT,
    ip_origen VARCHAR(45),
    detalles TEXT
);

-- 2.4 TABLA: Auditoria
CREATE TABLE IF NOT EXISTS Auditoria (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    tabla_afectada VARCHAR(50),
    registro_id INTEGER,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    ip_origen VARCHAR(45),
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. CREAR ÍNDICES
-- ============================================

-- 3.1 Índice para búsqueda de embeddings
CREATE INDEX IF NOT EXISTS idx_rostro_embedding ON Rostro 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 3.2 Índices específicos del checklist
CREATE INDEX IF NOT EXISTS idx_rostro_persona ON Rostro(persona_id);
CREATE INDEX IF NOT EXISTS idx_acceso_timestamp ON Acceso(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_acceso_rostro ON Acceso(rostro_id);
CREATE INDEX IF NOT EXISTS idx_acceso_exito ON Acceso(exito);
CREATE INDEX IF NOT EXISTS idx_acceso_puerta ON Acceso(puerta);

-- 3.3 Índices adicionales
CREATE INDEX IF NOT EXISTS idx_persona_matricula ON Persona(matricula_empleado);
CREATE INDEX IF NOT EXISTS idx_persona_tipo ON Persona(tipo);
CREATE INDEX IF NOT EXISTS idx_persona_activo ON Persona(activo);

-- ============================================
-- 4. CREAR VISTAS
-- ============================================

-- 4.1 Vista: Personas con sus rostros activos
CREATE OR REPLACE VIEW v_personas_rostros AS
SELECT 
    p.id AS persona_id,
    p.nombre,
    p.apellido,
    p.matricula_empleado,
    p.tipo,
    r.id AS rostro_id,
    r.imagen_respaldo,
    r.embedding
FROM Persona p
JOIN Rostro r ON p.id = r.persona_id
WHERE p.activo = TRUE AND r.activo = TRUE;

-- 4.2 Vista: Resumen de accesos por día (CORREGIDA)
CREATE OR REPLACE VIEW v_resumen_accesos_diario AS
SELECT 
    DATE(timestamp) AS fecha,
    COUNT(*) AS total_intentos,
    SUM(CASE WHEN exito = TRUE THEN 1 ELSE 0 END) AS exitosos,
    SUM(CASE WHEN exito = FALSE THEN 1 ELSE 0 END) AS fallidos,
    SUM(CASE WHEN rostro_id IS NULL THEN 1 ELSE 0 END) AS no_registrados,
    CAST(COALESCE(AVG(confianza), 0) AS NUMERIC(10,2)) AS confianza_promedio
FROM Acceso
GROUP BY DATE(timestamp)
ORDER BY fecha DESC;

-- 4.3 Vista: Checklist Acceso
CREATE OR REPLACE VIEW v_checklist_acceso AS
SELECT 
    id,
    rostro_id,
    timestamp,
    exito,
    puerta,
    imagen_intento
FROM Acceso;

-- ============================================
-- 5. FUNCIONES Y TRIGGERS
-- ============================================

-- 5.1 Función: Actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION update_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5.2 Trigger para Persona
DROP TRIGGER IF EXISTS trg_persona_update ON Persona;
CREATE TRIGGER trg_persona_update
BEFORE UPDATE ON Persona
FOR EACH ROW
EXECUTE FUNCTION update_fecha_actualizacion();

-- 5.3 Función: Buscar persona por embedding
CREATE OR REPLACE FUNCTION buscar_persona_por_embedding(
    p_embedding vector(512),
    p_umbral FLOAT DEFAULT 0.75
)
RETURNS TABLE(
    persona_id INTEGER,
    nombre VARCHAR,
    apellido VARCHAR,
    matricula VARCHAR,
    tipo VARCHAR,
    rostro_id INTEGER,
    imagen_respaldo VARCHAR,
    distancia FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.nombre,
        p.apellido,
        p.matricula_empleado,
        p.tipo,
        r.id,
        r.imagen_respaldo,
        1 - (r.embedding <=> p_embedding) AS distancia
    FROM Rostro r
    JOIN Persona p ON r.persona_id = p.id
    WHERE p.activo = TRUE AND r.activo = TRUE
        AND (1 - (r.embedding <=> p_embedding)) >= p_umbral
    ORDER BY r.embedding <=> p_embedding
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 5.4 Función: Registrar acceso
CREATE OR REPLACE FUNCTION registrar_acceso(
    p_rostro_id INTEGER DEFAULT NULL,
    p_persona_id INTEGER DEFAULT NULL,
    p_embedding vector(512) DEFAULT NULL,
    p_imagen_intento VARCHAR DEFAULT NULL,
    p_exito BOOLEAN DEFAULT FALSE,
    p_puerta VARCHAR DEFAULT 'Principal',
    p_confianza FLOAT DEFAULT NULL,
    p_tiempo_deteccion FLOAT DEFAULT NULL,
    p_ip_origen VARCHAR DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_acceso_id INTEGER;
BEGIN
    INSERT INTO Acceso (
        rostro_id,
        persona_id,
        embedding,
        imagen_intento,
        timestamp,
        exito,
        puerta,
        confianza,
        tiempo_deteccion,
        ip_origen,
        detalles
    ) VALUES (
        p_rostro_id,
        p_persona_id,
        p_embedding,
        p_imagen_intento,
        CURRENT_TIMESTAMP,
        p_exito,
        p_puerta,
        p_confianza,
        p_tiempo_deteccion,
        p_ip_origen,
        CASE 
            WHEN p_exito = TRUE THEN 'Acceso permitido'
            WHEN p_rostro_id IS NULL THEN 'Persona no registrada'
            ELSE 'Credenciales no coinciden'
        END
    )
    RETURNING id INTO v_acceso_id;
    
    RETURN v_acceso_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. DATOS DE PRUEBA
-- ============================================

-- Usuario administrador
INSERT INTO Persona (nombre, apellido, matricula_empleado, tipo, correo)
VALUES ('Admin', 'Sistema', 'ADMIN001', 'Administrativo', 'admin@sistema.com')
ON CONFLICT (matricula_empleado) DO NOTHING;

-- Usuario de prueba (Checklist)
INSERT INTO Persona (nombre, apellido, matricula_empleado, tipo, correo)
VALUES ('Usuario', 'Prueba', 'EMP001', 'Estudiante', 'usuario.prueba@instituto.com')
ON CONFLICT (matricula_empleado) DO NOTHING;

-- Rostro de prueba
DO $$
DECLARE
    v_persona_id INTEGER;
    v_test_vector vector(512);
BEGIN
    SELECT id INTO v_persona_id FROM Persona WHERE matricula_empleado = 'EMP001';
    
    v_test_vector := array(
        SELECT random() * 0.1 
        FROM generate_series(1, 512)
    )::vector;
    
    INSERT INTO Rostro (persona_id, embedding, imagen_respaldo, fecha_captura, activo)
    VALUES (
        v_persona_id,
        v_test_vector,
        'rostros/prueba_001.jpg',
        CURRENT_TIMESTAMP,
        TRUE
    );
    
    RAISE NOTICE 'Datos de prueba insertados correctamente';
END $$;

-- ============================================
-- 7. VERIFICACIÓN DE CHECKLIST
-- ============================================
DO $$
DECLARE
    v_check_persona BOOLEAN;
    v_check_rostro BOOLEAN;
    v_check_acceso BOOLEAN;
BEGIN
    SELECT COUNT(*) = 6 INTO v_check_persona
    FROM information_schema.columns 
    WHERE table_name = 'persona' 
    AND column_name IN ('id', 'nombre', 'apellido', 'matricula_empleado', 'tipo', 'fecha_registro');
    
    SELECT COUNT(*) = 6 INTO v_check_rostro
    FROM information_schema.columns 
    WHERE table_name = 'rostro' 
    AND column_name IN ('id', 'persona_id', 'embedding', 'fecha_captura', 'imagen_respaldo', 'activo');
    
    SELECT COUNT(*) = 6 INTO v_check_acceso
    FROM information_schema.columns 
    WHERE table_name = 'acceso' 
    AND column_name IN ('id', 'rostro_id', 'timestamp', 'exito', 'puerta', 'imagen_intento');
    
    RAISE NOTICE '============================================';
    RAISE NOTICE 'VERIFICACIÓN DE CHECKLIST - SPRINT 1';
    RAISE NOTICE '============================================';
    RAISE NOTICE '2.1.2 Extensión vector: ACTIVADA';
    RAISE NOTICE '2.1.3 Tabla Persona: %', 
        CASE WHEN v_check_persona THEN 'COMPLETA' ELSE 'INCOMPLETA' END;
    RAISE NOTICE '2.1.4 Tabla Rostro: %', 
        CASE WHEN v_check_rostro THEN 'COMPLETA' ELSE 'INCOMPLETA' END;
    RAISE NOTICE '2.1.5 Tabla Acceso: %', 
        CASE WHEN v_check_acceso THEN 'COMPLETA' ELSE 'INCOMPLETA' END;
    RAISE NOTICE '2.1.6 Índices: CREADOS';
    RAISE NOTICE '2.1.7 Datos de prueba: INSERTADOS';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'BASE DE DATOS LISTA PARA SPRINT 1';
    RAISE NOTICE '============================================';
END $$;