# DICCIONARIO DE DATOS
## Sistema de Control de Accesos - Reconocimiento Facial
### Instituto Tecnológico de Oaxaca

**Versión:** 1.0  
**Fecha:** 4 de septiembre de 2026  
**Responsable:** Ramírez Cruz Nazario  
**Sprint:** 1 (Infraestructura y Captura de Rostros)

---

## ÍNDICE

1. [Introducción](#introducción)
2. [Tabla Persona](#tabla-persona)
3. [Tabla Rostro](#tabla-rostro)
4. [Tabla Acceso](#tabla-acceso)
5. [Tabla Auditoria](#tabla-auditoria)
6. [Relaciones entre Tablas](#relaciones-entre-tablas)
7. [Diagrama Entidad-Relación](#diagrama-entidad-relación)
8. [Glosario de Términos](#glosario-de-términos)

---

## INTRODUCCIÓN

El presente diccionario de datos documenta la estructura de la base de datos del **Sistema de Control de Accesos basado en Reconocimiento Facial** para el Instituto Tecnológico de Oaxaca.

### Convenciones de Nomenclatura

| Convención | Descripción | Ejemplo |
|------------|-------------|---------|
| **snake_case** | Nombres de tablas y columnas en minúsculas con guiones bajos | `matricula_empleado` |
| **PascalCase** | Nombres de tablas en singular con mayúscula inicial | `Persona`, `Rostro` |
| **SERIAL** | Tipo de dato autoincrementable para llaves primarias | `id SERIAL PRIMARY KEY` |
| **FK** | Llave foránea que referencia otra tabla | `persona_id` → `Persona.id` |

### Tipos de Datos Utilizados

| Tipo | Descripción | Uso |
|------|-------------|-----|
| `SERIAL` | Entero autoincrementable | Llaves primarias |
| `INTEGER` | Número entero | Llaves foráneas, conteos |
| `VARCHAR(n)` | Cadena de texto de longitud variable | Nombres, descripciones |
| `TEXT` | Cadena de texto larga | Detalles, observaciones |
| `BOOLEAN` | Valor verdadero/falso | Estados, banderas |
| `TIMESTAMP` | Fecha y hora con zona horaria | Registros de tiempo |
| `FLOAT` | Número decimal de precisión doble | Porcentajes, métricas |
| `JSONB` | Objeto JSON binario | Datos estructurados, auditoría |
| `vector(512)` | Vector de 512 dimensiones | Embeddings faciales |

---

## TABLA PERSONA

### Descripción
Almacena la información de todas las personas registradas en el sistema, incluyendo estudiantes, profesores, personal administrativo y visitantes.

### Estructura

| # | Campo | Tipo | Nulo | Predeterminado | Descripción |
|---|-------|------|------|----------------|-------------|
| 1 | `id` | SERIAL | NO | `nextval('persona_id_seq')` | Identificador único de la persona (PK) |
| 2 | `nombre` | VARCHAR(50) | NO | - | Nombre(s) de la persona |
| 3 | `apellido` | VARCHAR(50) | NO | - | Apellidos de la persona |
| 4 | `matricula_empleado` | VARCHAR(20) | NO | - | Matrícula o número de empleado (ÚNICO) |
| 5 | `tipo` | VARCHAR(20) | NO | - | Tipo de persona: `Estudiante`, `Profesor`, `Administrativo`, `Visitante` |
| 6 | `correo` | VARCHAR(100) | SÍ | NULL | Correo electrónico institucional |
| 7 | `telefono` | VARCHAR(20) | SÍ | NULL | Número de teléfono de contacto |
| 8 | `activo` | BOOLEAN | SÍ | `TRUE` | Estado de la cuenta: `TRUE` (activa), `FALSE` (inactiva) |
| 9 | `fecha_registro` | TIMESTAMP | SÍ | `CURRENT_TIMESTAMP` | Fecha y hora de creación del registro |
| 10 | `fecha_actualizacion` | TIMESTAMP | SÍ | `CURRENT_TIMESTAMP` | Fecha y hora de última modificación |

### Restricciones

| Tipo | Campo | Descripción |
|------|-------|-------------|
| **PK** | `id` | Llave primaria autoincrementable |
| **UK** | `matricula_empleado` | Llave única para evitar duplicados |
| **CHECK** | `tipo` | Valores permitidos: `Estudiante`, `Profesor`, `Administrativo`, `Visitante` |

### Índices

| Nombre | Campos | Tipo | Propósito |
|--------|--------|------|-----------|
| `persona_pkey` | `id` | PRIMARY KEY | Identificador único |
| `persona_matricula_empleado_key` | `matricula_empleado` | UNIQUE | Búsqueda rápida por matrícula |
| `idx_persona_matricula` | `matricula_empleado` | BTREE | Optimizar búsquedas por matrícula |
| `idx_persona_tipo` | `tipo` | BTREE | Filtrar por tipo de persona |
| `idx_persona_activo` | `activo` | BTREE | Filtrar personas activas/inactivas |

### Triggers

| Nombre | Evento | Propósito |
|--------|--------|-----------|
| `trg_persona_update` | BEFORE UPDATE | Actualiza automáticamente `fecha_actualizacion` |

### Relaciones

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `Rostro` | **1 : N** | Una persona puede tener múltiples rostros registrados |
| `Acceso` | **1 : N** | Una persona puede tener múltiples intentos de acceso |

### Ejemplo de Datos

```sql
INSERT INTO Persona (nombre, apellido, matricula_empleado, tipo, correo) 
VALUES ('Juan', 'Pérez', 'EMP001', 'Estudiante', 'juan.perez@instituto.com');