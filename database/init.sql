-- ============================================
-- SISTEMA DE CONTROL DE ACCESOS - SPRINT 0
-- Script de inicialización de base de datos
-- PostgreSQL + pgvector
-- ============================================

-- ============================================
-- 1. ACTIVAR EXTENSIÓN pgvector
-- ============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 2. CREAR TABLAS PRINCIPALES
-- ============================================

-- 2.1 TABLA: Persona
-- Almacena la información de las personas registradas
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
-- Almacena el embedding facial (vector) y referencia a la imagen
CREATE TABLE IF NOT EXISTS Rostro (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER NOT NULL REFERENCES Persona(id) ON DELETE CASCADE,
    embedding vector(512) NOT NULL,  -- Vector de 512 dimensiones (DeepFace)
    ruta_imagen VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

-- 2.3 TABLA: Acceso
-- Registra todos los intentos de acceso (log)
CREATE TABLE IF NOT EXISTS Acceso (
    id SERIAL PRIMARY KEY,
    persona_id INTEGER REFERENCES Persona(id) ON DELETE SET NULL,
    embedding vector(512),  -- Vector capturado en el intento
    ruta_imagen VARCHAR(255),  -- Imagen capturada en el intento
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Exitoso', 'Fallido', 'No registrado', 'Error')),
    confianza FLOAT,  -- Porcentaje de confianza (0-100)
    tiempo_deteccion FLOAT,  -- Milisegundos que tardó en procesar
    fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origen VARCHAR(45),  -- IPv4 o IPv6
    detalles TEXT
);

-- 2.4 TABLA: Auditoria
-- Registra eventos administrativos (altas, bajas, modificaciones)
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
-- 3. CREAR ÍNDICES PARA OPTIMIZACIÓN
-- ============================================

-- 3.1 Índice para búsqueda de embeddings (distancia coseno)
CREATE INDEX IF NOT EXISTS idx_rostro_embedding ON Rostro 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 3.2 Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_persona_matricula ON Persona(matricula_empleado);
CREATE INDEX IF NOT EXISTS idx_persona_tipo ON Persona(tipo);
CREATE INDEX IF NOT EXISTS idx_persona_activo ON Persona(activo);
CREATE INDEX IF NOT EXISTS idx_rostro_persona ON Rostro(persona_id);
CREATE INDEX IF NOT EXISTS idx_acceso_persona ON Acceso(persona_id);
CREATE INDEX IF NOT EXISTS idx_acceso_estado ON Acceso(estado);
CREATE INDEX IF NOT EXISTS idx_acceso_fecha ON Acceso(fecha_intento DESC);

-- ============================================
-- 4. CREAR VISTAS ÚTILES
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
    r.ruta_imagen,
    r.embedding
FROM Persona p
JOIN Rostro r ON p.id = r.persona_id
WHERE p.activo = TRUE AND r.activo = TRUE;

-- 4.2 Vista: Resumen de accesos por día
CREATE OR REPLACE VIEW v_resumen_accesos_diario AS
SELECT 
    DATE(fecha_intento) AS fecha,
    COUNT(*) AS total_intentos,
    SUM(CASE WHEN estado = 'Exitoso' THEN 1 ELSE 0 END) AS exitosos,
    SUM(CASE WHEN estado = 'Fallido' THEN 1 ELSE 0 END) AS fallidos,
    SUM(CASE WHEN estado = 'No registrado' THEN 1 ELSE 0 END) AS no_registrados,
    ROUND(AVG(confianza), 2) AS confianza_promedio
FROM Acceso
GROUP BY DATE(fecha_intento)
ORDER BY fecha DESC;

-- ============================================
-- 5. CREAR FUNCIONES Y TRIGGERS
-- ============================================

-- 5.1 Función: Actualizar fecha_actualizacion automáticamente
CREATE OR REPLACE FUNCTION update_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5.2 Trigger para Persona
CREATE TRIGGER trg_persona_update
BEFORE UPDATE ON Persona
FOR EACH ROW
EXECUTE FUNCTION update_fecha_actualizacion();

-- 5.3 Función: Buscar persona por embedding (distancia coseno)
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
    ruta_imagen VARCHAR,
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
        r.ruta_imagen,
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
    p_persona_id INTEGER,
    p_embedding vector(512),
    p_ruta_imagen VARCHAR,
    p_estado VARCHAR,
    p_confianza FLOAT,
    p_tiempo_deteccion FLOAT,
    p_ip_origen VARCHAR
)
RETURNS INTEGER AS $$
DECLARE
    v_acceso_id INTEGER;
BEGIN
    INSERT INTO Acceso (
        persona_id,
        embedding,
        ruta_imagen,
        estado,
        confianza,
        tiempo_deteccion,
        ip_origen,
        detalles
    ) VALUES (
        p_persona_id,
        p_embedding,
        p_ruta_imagen,
        p_estado,
        p_confianza,
        p_tiempo_deteccion,
        p_ip_origen,
        CASE 
            WHEN p_estado = 'Exitoso' THEN 'Acceso permitido'
            WHEN p_estado = 'Fallido' THEN 'Credenciales no coinciden'
            WHEN p_estado = 'No registrado' THEN 'Persona no registrada en el sistema'
            ELSE 'Error durante el procesamiento'
        END
    )
    RETURNING id INTO v_acceso_id;
    
    RETURN v_acceso_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. DATOS DE PRUEBA (OPCIONAL)
-- ============================================

-- Insertar un usuario administrador por defecto
INSERT INTO Persona (nombre, apellido, matricula_empleado, tipo, correo)
VALUES ('Admin', 'Sistema', 'ADMIN001', 'Administrativo', 'admin@sistema.com')
ON CONFLICT (matricula_empleado) DO NOTHING;

-- Insertar un usuario de prueba
INSERT INTO Persona (nombre, apellido, matricula_empleado, tipo, correo)
VALUES ('Juan', 'Pérez', 'EMP001', 'Estudiante', 'juan.perez@instituto.com')
ON CONFLICT (matricula_empleado) DO NOTHING;

-- ============================================
-- 7. MENSAJE DE CONFIRMACIÓN
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Base de datos inicializada correctamente';
    RAISE NOTICE '📊 Tablas creadas: Persona, Rostro, Acceso, Auditoria';
    RAISE NOTICE '🔍 Extensión pgvector activada';
    RAISE NOTICE '📈 Índices y funciones creados';
END;
$$;