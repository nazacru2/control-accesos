-- ============================================
-- Limpieza del dato de prueba EMP001 (Sprint 0)
-- Tiene un embedding ALEATORIO (no un rostro real), sigue activo
-- desde database/init.sql y cuenta como "persona registrada".
-- ============================================
-- Ejecutar con:
--   docker exec -i postgres_accesos psql -U admin -d control_accesos < limpieza_emp001.sql

-- 1. Revisión previa (informativo — no borra nada)
\echo '--- Persona EMP001 ---'
SELECT id, nombre, apellido, matricula_empleado, tipo, activo
FROM persona WHERE matricula_empleado = 'EMP001';

\echo '--- Rostro(s) asociados ---'
SELECT r.id, r.persona_id, r.imagen_respaldo, r.activo
FROM rostro r
JOIN persona p ON p.id = r.persona_id
WHERE p.matricula_empleado = 'EMP001';

\echo '--- Accesos asociados (si hay, se preservan con persona_id/rostro_id en NULL) ---'
SELECT a.id, a.timestamp, a.exito, a.puerta
FROM acceso a
JOIN persona p ON p.id = a.persona_id
WHERE p.matricula_empleado = 'EMP001';

-- 2. Borrado (descomenta las líneas siguientes cuando confirmes lo de arriba)
BEGIN;
DELETE FROM persona WHERE matricula_empleado = 'EMP001';
-- -- El rostro fantasma se borra solo por ON DELETE CASCADE.
-- -- Si había accesos, sus columnas rostro_id/persona_id quedan en NULL
-- -- por ON DELETE SET NULL (se conserva el historial, no se pierde).
COMMIT;

-- 3. Verificación posterior (correr después del DELETE):
--    SELECT COUNT(*) FROM persona WHERE matricula_empleado = 'EMP001';  -- debe dar 0
--    SELECT COUNT(*) FROM rostro WHERE imagen_respaldo LIKE '%prueba_001%';  -- debe dar 0
