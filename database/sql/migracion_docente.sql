-- ============================================
-- Migración Sprint 2: 'Profesor' -> 'Docente'
-- Alinea el CHECK constraint de persona.tipo con las historias
-- de usuario HU-04, HU-09 y HU-10.
-- ============================================
-- Ejecutar con:
--   docker exec -i postgres_accesos psql -U admin -d control_accesos < migracion_docente.sql

BEGIN;

-- 1. Migrar filas existentes que usen el valor anterior.
--    (Si no hay ninguna, el UPDATE simplemente afecta 0 filas.)
UPDATE persona SET tipo = 'Docente' WHERE tipo = 'Profesor';

-- 2. Reemplazar el constraint.
ALTER TABLE persona DROP CONSTRAINT IF EXISTS persona_tipo_check;

ALTER TABLE persona ADD CONSTRAINT persona_tipo_check
    CHECK (tipo IN ('Estudiante', 'Docente', 'Administrativo', 'Visitante'));

COMMIT;

-- 3. Verificación posterior:
--    SELECT conname, pg_get_constraintdef(oid)
--    FROM pg_constraint WHERE conrelid = 'persona'::regclass AND contype = 'c';
--
--    SELECT tipo, COUNT(*) FROM persona GROUP BY tipo;

-- IMPORTANTE: actualizar también database/init.sql con el mismo CHECK,
-- o al recrear el contenedor de Postgres desde cero volverá a aparecer
-- 'Profesor' y desaparecerá 'Docente'.
