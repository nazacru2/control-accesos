-- ============================================
-- Limpieza del usuario de prueba TEST001 (Sprint 1)
-- persona_id=4, "Prueba Sprint1" — causó un falso positivo en 7.1.4
-- del Sprint 2 al quedar activo y sin relación con las pruebas actuales.
-- ============================================
-- Ejecutar con:
--   docker exec -i postgres_accesos psql -U admin -d control_accesos < limpieza_test001.sql

\echo '--- Persona TEST001 ---'
SELECT id, nombre, apellido, matricula_empleado, tipo, activo
FROM persona WHERE matricula_empleado = 'TEST001';

\echo '--- Rostro(s) asociados ---'
SELECT r.id, r.persona_id, r.imagen_respaldo, r.activo
FROM rostro r
JOIN persona p ON p.id = r.persona_id
WHERE p.matricula_empleado = 'TEST001';

\echo '--- Accesos asociados (se preservan con persona_id/rostro_id en NULL) ---'
SELECT a.id, a.timestamp, a.exito, a.puerta, a.confianza
FROM acceso a
JOIN persona p ON p.id = a.persona_id
WHERE p.matricula_empleado = 'TEST001';

-- Borrado (descomenta cuando confirmes lo de arriba)
BEGIN;
DELETE FROM persona WHERE matricula_empleado = 'TEST001';
COMMIT;

-- Verificación posterior:
--    SELECT COUNT(*) FROM persona WHERE matricula_empleado = 'TEST001';  -- debe dar 0