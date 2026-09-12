# DICCIONARIO DE DATOS
## Sistema de Control de Accesos - Reconocimiento Facial
### Instituto Tecnológico de Oaxaca

**Versión:** 1.1
**Fecha:** 12 de septiembre de 2026
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
7. [Glosario de Términos](#glosario-de-términos)

---

## INTRODUCCIÓN

El presente diccionario de datos documenta la estructura de la base de datos del **Sistema de Control de Accesos basado en Reconocimiento Facial** para el Instituto Tecnológico de Oaxaca. Toda la estructura descrita (columnas, índices, trigger y comportamiento de llaves foráneas) fue verificada directamente contra la base de datos real mediante `information_schema`, `pg_indexes`, `pg_trigger` y `pg_get_constraintdef`.

### Convenciones de Nomenclatura

| Convención | Descripción | Ejemplo |
|------------|-------------|---------|
| **snake_case** | Nombres de tablas y columnas en minúsculas con guiones bajos | `matricula_empleado` |
| **SERIAL** | Tipo de dato autoincrementable para llaves primarias | `id SERIAL PRIMARY KEY` |
| **FK** | Llave foránea que referencia otra tabla | `persona_id` → `persona.id` |

### Tipos de Datos Utilizados

| Tipo | Descripción | Uso |
|------|-------------|-----|
| `SERIAL` | Entero autoincrementable | Llaves primarias |
| `INTEGER` | Número entero | Llaves foráneas, conteos |
| `VARCHAR(n)` | Cadena de texto de longitud variable | Nombres, descripciones |
| `TEXT` | Cadena de texto larga | Detalles, observaciones |
| `BOOLEAN` | Valor verdadero/falso | Estados, banderas |
| `TIMESTAMP` | Fecha y hora | Registros de tiempo |
| `FLOAT` | Número decimal de precisión doble | Porcentajes, métricas |
| `JSON` / `JSONB` | Objeto JSON | Datos estructurados, auditoría |
| `vector(512)` | Vector de 512 dimensiones (pgvector) | Embeddings faciales |

---

## TABLA PERSONA

### Descripción
Almacena la información de todas las personas registradas en el sistema: estudiantes, profesores, personal administrativo y visitantes.

### Estructura

| # | Campo | Tipo | Nulo | Predeterminado | Descripción |
|---|-------|------|------|----------------|-------------|
| 1 | `id` | SERIAL | NO | `nextval('persona_id_seq')` | Identificador único de la persona (PK) |
| 2 | `nombre` | VARCHAR(50) | NO | - | Nombre(s) de la persona |
| 3 | `apellido` | VARCHAR(50) | NO | - | Apellidos de la persona |
| 4 | `matricula_empleado` | VARCHAR(20) | NO | - | Matrícula o número de empleado (ÚNICO) |
| 5 | `tipo` | VARCHAR(20) | NO | - | Tipo de persona: `Estudiante`, `Profesor`, `Administrativo`, `Visitante` (CHECK) |
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

### Índices (verificados con `pg_indexes`)

| Nombre | Campos | Tipo | Propósito |
|--------|--------|------|-----------|
| `persona_pkey` | `id` | PRIMARY KEY | Identificador único |
| `persona_matricula_empleado_key` | `matricula_empleado` | UNIQUE | Evitar duplicados |
| `idx_persona_matricula` | `matricula_empleado` | BTREE | Optimizar búsquedas por matrícula |
| `idx_persona_tipo` | `tipo` | BTREE | Filtrar por tipo de persona |
| `idx_persona_activo` | `activo` | BTREE | Filtrar personas activas/inactivas |

### Trigger (verificado con `pg_trigger`)

| Nombre | Evento | Propósito |
|--------|--------|-----------|
| `trg_persona_update` | BEFORE UPDATE | Actualiza automáticamente `fecha_actualizacion` |

### Relaciones

| Tabla | Tipo | Comportamiento al eliminar |
|-------|------|-----------------------------|
| `rostro` | **1 : N** | `ON DELETE CASCADE` — al borrar la persona se borran sus rostros |
| `acceso` | **1 : N** | `ON DELETE SET NULL` — el historial de accesos se conserva con `persona_id = NULL` |

---

## TABLA ROSTRO

### Descripción
Almacena los embeddings faciales (vectores de características) y las referencias a las imágenes de cada persona registrada.

### Estructura

| # | Campo | Tipo | Nulo | Predeterminado | Descripción |
|---|-------|------|------|----------------|-------------|
| 1 | `id` | SERIAL | NO | `nextval('rostro_id_seq')` | Identificador único del rostro (PK) |
| 2 | `persona_id` | INTEGER | NO | - | Llave foránea a `persona.id` (FK, `ON DELETE CASCADE`) |
| 3 | `embedding` | vector(512) | NO | - | Vector de 512 dimensiones generado por DeepFace, modelo **Facenet512** |
| 4 | `imagen_respaldo` | VARCHAR(255) | NO | - | Ruta al archivo de imagen almacenado |
| 5 | `fecha_captura` | TIMESTAMP | SÍ | `CURRENT_TIMESTAMP` | Fecha y hora de captura del rostro |
| 6 | `activo` | BOOLEAN | SÍ | `TRUE` | Rostro disponible para reconocimiento |

### Índices (verificados con `pg_indexes`)

| Nombre | Campos | Tipo | Propósito |
|--------|--------|------|-----------|
| `rostro_pkey` | `id` | PRIMARY KEY | Identificador único |
| `idx_rostro_persona` | `persona_id` | BTREE | Optimizar búsquedas por persona |
| `idx_rostro_embedding` | `embedding` | IVFFLAT (`vector_cosine_ops`, `lists=100`) | Búsqueda de similitud facial por distancia coseno |

### Relaciones

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `persona` | **N : 1** | Pertenece a una persona |
| `acceso` | **1 : N** | `ON DELETE SET NULL` — el historial de accesos se conserva con `rostro_id = NULL` |

### Características especiales

- **Embedding**: vector de 512 dimensiones generado por el modelo **Facenet512** de DeepFace (confirmado en pruebas de la fase 7.2: `model: Facenet512`, `embedding_size: 512`).
- **Búsqueda por similitud**: distancia coseno, calculada directamente en PostgreSQL mediante el operador `<=>` de pgvector, acelerada por el índice `idx_rostro_embedding` (IVFFLAT).
- **Almacenamiento de imágenes**: se guarda la ruta de la imagen original en `imagen_respaldo` para verificación manual.

---

## TABLA ACCESO

### Descripción
Registra todos los intentos de acceso al sistema, exitosos y fallidos, con metadatos técnicos para análisis y auditoría.

### Estructura

| # | Campo | Tipo | Nulo | Predeterminado | Descripción |
|---|-------|------|------|----------------|-------------|
| 1 | `id` | SERIAL | NO | `nextval('acceso_id_seq')` | Identificador único del intento (PK) |
| 2 | `rostro_id` | INTEGER | SÍ | NULL | Llave foránea a `rostro.id` (FK, `ON DELETE SET NULL`) |
| 3 | `persona_id` | INTEGER | SÍ | NULL | Llave foránea a `persona.id` (FK, `ON DELETE SET NULL`) |
| 4 | `embedding` | JSON | SÍ | NULL | **Campo heredado de un diseño anterior; actualmente sin uso.** El constructor del modelo `Acceso` nunca le asigna valor, precisamente para evitar un conflicto de tipo con la columna `embedding` (tipo `vector`) de la tabla `rostro`. Se recomienda su eliminación en un refactor futuro |
| 5 | `imagen_intento` | VARCHAR(255) | SÍ | NULL | Ruta a la imagen capturada en el intento |
| 6 | `timestamp` | TIMESTAMP | NO | `CURRENT_TIMESTAMP` | Fecha y hora del intento de acceso |
| 7 | `exito` | BOOLEAN | NO | `FALSE` | Resultado del intento: `TRUE` (éxito), `FALSE` (fallido) |
| 8 | `puerta` | VARCHAR(50) | SÍ | NULL | Identificador de la puerta o punto de acceso |
| 9 | `confianza` | FLOAT | SÍ | NULL | Similitud coseno obtenida en la comparación (0-1) |
| 10 | `tiempo_deteccion` | FLOAT | SÍ | NULL | Tiempo de procesamiento en milisegundos |
| 11 | `ip_origen` | VARCHAR(45) | SÍ | NULL | Dirección IP del dispositivo que realizó el intento |
| 12 | `detalles` | TEXT | SÍ | NULL | Información adicional del intento (motivo de éxito o denegación) |

### Índices (verificados con `pg_indexes`)

| Nombre | Campos | Tipo | Propósito |
|--------|--------|------|-----------|
| `acceso_pkey` | `id` | PRIMARY KEY | Identificador único |
| `idx_acceso_timestamp` | `timestamp` DESC | BTREE | Consultas de historial más reciente primero |
| `idx_acceso_rostro` | `rostro_id` | BTREE | Consultas por rostro |
| `idx_acceso_exito` | `exito` | BTREE | Filtrar por resultado |
| `idx_acceso_puerta` | `puerta` | BTREE | Filtrar por puerta/ubicación |

### Relaciones

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `rostro` | **N : 1** | Puede ser NULL si no se identificó rostro, o si el rostro fue eliminado después |
| `persona` | **N : 1** | Puede ser NULL si no se identificó a la persona, o si la persona fue eliminada después |

### Estados de acceso

| Estado | Condición | Caso de uso |
|--------|-----------|-------------|
| **Éxito** | `exito = TRUE` | Rostro reconocido y autorizado |
| **Fallido, identificado** | `exito = FALSE`, `rostro_id IS NOT NULL` | Rostro reconocido pero no autorizado |
| **Fallido, no identificado** | `exito = FALSE`, `rostro_id IS NULL` | Rostro no encontrado en la base de datos |

---

## TABLA AUDITORIA

### Descripción
Registra eventos administrativos (altas, bajas, modificaciones) para trazabilidad. **Nota:** esta tabla existe en el esquema de la base de datos, pero al momento de esta versión el proyecto aún no define un modelo ORM ni rutas que escriban en ella — queda lista para integrarse cuando se construya el módulo de administración.

### Estructura

| # | Campo | Tipo | Nulo | Predeterminado | Descripción |
|---|-------|------|------|----------------|-------------|
| 1 | `id` | SERIAL | NO | `nextval('auditoria_id_seq')` | Identificador único del evento (PK) |
| 2 | `usuario` | VARCHAR(50) | NO | - | Usuario que realizó la acción |
| 3 | `accion` | VARCHAR(50) | NO | - | Tipo de acción: `INSERT`, `UPDATE`, `DELETE` |
| 4 | `tabla_afectada` | VARCHAR(50) | SÍ | NULL | Nombre de la tabla modificada |
| 5 | `registro_id` | INTEGER | SÍ | NULL | ID del registro afectado |
| 6 | `datos_anteriores` | JSONB | SÍ | NULL | Estado previo del registro |
| 7 | `datos_nuevos` | JSONB | SÍ | NULL | Nuevo estado del registro |
| 8 | `ip_origen` | VARCHAR(45) | SÍ | NULL | Dirección IP del usuario |
| 9 | `fecha_evento` | TIMESTAMP | SÍ | `CURRENT_TIMESTAMP` | Fecha y hora del evento |

### Nota de diseño

A diferencia de `persona`, `rostro` y `acceso`, esta tabla **no declara llaves foráneas físicas** hacia las tablas que audita — `tabla_afectada` y `registro_id` son una referencia genérica de propósito general, ya que una sola tabla de auditoría debe poder registrar cambios de cualquier tabla del sistema. Es un patrón aceptado específicamente para bitácoras/auditoría, pero no debe replicarse en tablas transaccionales.

---

## RELACIONES ENTRE TABLAS

| Relación | Tipo | Comportamiento al eliminar |
|----------|------|------------------------------|
| `persona` → `rostro` | **1 : N** | `ON DELETE CASCADE` |
| `persona` → `acceso` | **1 : N** | `ON DELETE SET NULL` |
| `rostro` → `acceso` | **1 : N** | `ON DELETE SET NULL` |
| `auditoria` → (cualquier tabla) | — | Referencia lógica, sin FK física |

---

## GLOSARIO DE TÉRMINOS

| Término | Definición |
|---------|------------|
| **Embedding** | Vector numérico que representa las características faciales de una persona, generado por un modelo de deep learning (DeepFace). |
| **pgvector** | Extensión de PostgreSQL que permite almacenar y buscar vectores de alta dimensión. |
| **Distancia coseno** | Métrica de similitud entre dos vectores; valores cercanos a 1 indican alta similitud. |
| **IVFFLAT** | Índice de PostgreSQL para búsqueda aproximada de vectores (Approximate Nearest Neighbor). |
| **DeepFace** | Biblioteca de Python para reconocimiento facial que utiliza modelos pre-entrenados. |
| **Facenet512** | Modelo de deep learning usado en este proyecto; genera embeddings de 512 dimensiones. |
| **JSONB** | Tipo de dato de PostgreSQL que almacena JSON en formato binario para consultas eficientes. |

---

## HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambios | Responsable |
|---------|-------|---------|-------------|
| 1.0 | 04/09/2026 | Creación inicial del diccionario de datos | Ramírez Cruz Nazario |
| 1.1 | 12/09/2026 | Corrección: Facenet → Facenet512; aclarado que `acceso.embedding` está sin uso; verificación cruzada de índices, trigger y comportamiento de FK contra la base de datos real | Ramírez Cruz Nazario |

---

## APROBACIONES

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Responsable | Ramírez Cruz Nazario | 12/09/2026 | _____________ |
| Asesor | _________________ | ____/____/____ | _____________ |

---

**FIN DEL DICCIONARIO DE DATOS**