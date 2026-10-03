# backend/app/services/registro.py
"""
Servicio de Registro Biométrico - Sprint 2
Fase 2.1 - Crear servicio de registro de personas

Responsable: Ramírez Cruz Nazario
"""

import os
import base64
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

import cv2
import numpy as np

from app import db
from app.models import Persona, Rostro
from app.services.face_recognizer import FaceRecognizer

logger = logging.getLogger(__name__)


class RegistroService:
    """
    Servicio encargado del registro de personas y sus rostros.

    Métodos principales:
    - validar_tipo()         -> valida contra el CHECK constraint real
    - verificar_duplicado()  -> 2.1.5
    - validar_imagen()       -> 2.1.6
    - agregar_rostro()       -> 2.1.4
    - registrar_persona()    -> 2.1.3
    """

    # Debe coincidir exactamente con persona_tipo_check en la base de datos
    # (ver database/init.sql). Si cambia el CHECK, cambiar también aquí.
    TIPOS_VALIDOS = {'Estudiante', 'Docente', 'Administrativo', 'Visitante'}

    def __init__(self):
        # Reutiliza el mismo detector que validacion.py (OpenCV Haar)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Configuración desde .env
        self.min_face_size = int(os.getenv("MIN_FACE_SIZE", 60))
        self.max_samples = int(os.getenv("MAX_SAMPLES_PER_PERSON", 5))
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")

        # Asegurar que existe la carpeta de respaldos
        self.respaldo_folder = os.path.join(self.upload_folder, "rostros")
        os.makedirs(self.respaldo_folder, exist_ok=True)

        # Instancia del reconocedor (singleton local)
        self._recognizer = None

    @property
    def recognizer(self) -> FaceRecognizer:
        """Lazy init del FaceRecognizer."""
        if self._recognizer is None:
            self._recognizer = FaceRecognizer(
                model_name=os.getenv("DEEPFACE_MODEL", "Facenet512"),
                detector_backend=os.getenv("DEEPFACE_DETECTOR", "mtcnn"),
                threshold=float(os.getenv("SIMILARITY_THRESHOLD", 0.6)),
            )
        return self._recognizer

    # ========================================================
    # Validar tipo contra el CHECK constraint real de la BD
    # ========================================================
    def validar_tipo(self, tipo: str) -> None:
        """
        Valida que 'tipo' sea uno de los valores aceptados por
        persona_tipo_check en PostgreSQL.

        Se llama una sola vez desde aquí, tanto en registrar_persona()
        como en registrar_persona_con_multiples_rostros(). Antes esta
        validación solo existía duplicada en el endpoint /multiple de
        routes/registro.py; el endpoint simple dejaba pasar cualquier
        valor hasta el INSERT, y el CHECK de Postgres lo rechazaba como
        una excepción genérica (500) en vez de un 400 controlado.

        Raises:
            ValueError: si el tipo no es válido.
        """
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo inválido: '{tipo}'. Valores permitidos: "
                f"{', '.join(sorted(self.TIPOS_VALIDOS))}"
            )

    # ========================================================
    # 2.1.5 — Verificar duplicado por matrícula
    # ========================================================
    def verificar_duplicado(self, matricula: str) -> bool:
        """
        Verifica si ya existe una persona con la matrícula dada.

        Returns:
            True si YA existe (duplicado), False si está libre.
        """
        existente = Persona.query.filter_by(
            matricula_empleado=matricula.strip()
        ).first()
        return existente is not None

    # ========================================================
    # 2.1.6 — Validar que la imagen contenga un rostro
    # ========================================================
    def validar_imagen(self, imagen: np.ndarray) -> Dict[str, Any]:
        """
        Valida que la imagen contenga al menos un rostro detectable
        y que cumpla con el tamaño mínimo configurado.

        Args:
            imagen: Imagen BGR como numpy array.

        Returns:
            Dict con:
              - valido (bool)
              - mensaje (str)
              - rostro (numpy array recortado) si valido
              - bbox (tuple) si valido
        """
        if imagen is None or imagen.size == 0:
            return {"valido": False, "mensaje": "Imagen vacía o inválida"}

        # Detección con Haar (igual que validacion.py)
        gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        rostros = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(rostros) == 0:
            return {
                "valido": False,
                "mensaje": "No se detectó ningún rostro en la imagen",
            }

        if len(rostros) > 1:
            return {
                "valido": False,
                "mensaje": f"Se detectaron {len(rostros)} rostros. Debe haber solo uno",
            }

        x, y, w, h = rostros[0]

        # Validar tamaño mínimo (MIN_FACE_SIZE del .env)
        if w < self.min_face_size or h < self.min_face_size:
            return {
                "valido": False,
                "mensaje": (
                    f"Rostro demasiado pequeño ({w}x{h}px). "
                    f"Mínimo requerido: {self.min_face_size}px"
                ),
            }

        rostro_recortado = imagen[y : y + h, x : x + w]

        return {
            "valido": True,
            "mensaje": "Rostro válido",
            "rostro": rostro_recortado,
            "bbox": (int(x), int(y), int(w), int(h)),
        }

    # ========================================================
    # 2.1.4 — Agregar un rostro (embedding) a una persona
    # ========================================================
    def agregar_rostro(
        self,
        persona_id: int,
        embedding: np.ndarray,
        imagen_bgr: Optional[np.ndarray] = None,
        activo: bool = True,
    ) -> Rostro:
        """
        Agrega un embedding de rostro asociado a una persona.
        Guarda la imagen de respaldo en disco (imagen_respaldo es NOT NULL).

        Args:
            persona_id: ID de la persona.
            embedding: Vector numpy (512 dims para Facenet512).
            imagen_bgr: Imagen original del rostro para respaldo.
            activo: Si el rostro se usará en validación.

        Returns:
            Instancia Rostro creada.

        Raises:
            ValueError: si el embedding es inválido o se supera el límite.
        """
        if embedding is None or len(embedding) == 0:
            raise ValueError("Embedding vacío o inválido")

        embedding_list = (
            embedding.tolist()
            if isinstance(embedding, np.ndarray)
            else list(embedding)
        )

        # Verificar límite de muestras por persona
        total_actual = Rostro.query.filter_by(persona_id=persona_id).count()
        if total_actual >= self.max_samples:
            raise ValueError(
                f"La persona ya alcanzó el máximo de {self.max_samples} muestras"
            )

        # Guardar imagen de respaldo (obligatorio por NOT NULL)
        ruta_respaldo = self._guardar_respaldo(persona_id, imagen_bgr)

        rostro = Rostro(
            persona_id=persona_id,
            embedding=embedding_list,
            imagen_respaldo=ruta_respaldo,
            activo=activo,
        )
        db.session.add(rostro)
        db.session.flush()  # Para obtener rostro.id sin commit
        return rostro

    def _guardar_respaldo(
        self, persona_id: int, imagen_bgr: Optional[np.ndarray]
    ) -> str:
        """
        Guarda la imagen de respaldo en disco y retorna la ruta.
        Si no se recibe imagen, genera un placeholder transparente.
        """
        nombre = f"persona_{persona_id}_{uuid.uuid4().hex[:8]}.jpg"
        ruta_completa = os.path.join(self.respaldo_folder, nombre)

        if imagen_bgr is not None and imagen_bgr.size > 0:
            cv2.imwrite(ruta_completa, imagen_bgr)
        else:
            # Placeholder 1x1 negro (evita romper NOT NULL)
            placeholder = np.zeros((1, 1, 3), dtype=np.uint8)
            cv2.imwrite(ruta_completa, placeholder)

        # Ruta relativa tipo "uploads/rostros/persona_X_xxx.jpg"
        return os.path.relpath(ruta_completa, start=os.getcwd()).replace("\\", "/")

    # ========================================================
    # 2.1.3 — Registrar una persona nueva
    # ========================================================
    def registrar_persona(
        self,
        nombre: str,
        apellido: str,
        matricula: str,
        tipo: str,
        embedding: np.ndarray,
        imagen_bgr: Optional[np.ndarray] = None,
        correo: Optional[str] = None,
        telefono: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Registra una persona y su primer rostro en una transacción única.

        Raises:
            ValueError: si el tipo es inválido, hay duplicado, o error de integridad.
        """
        # Validar tipo ANTES de tocar la base de datos
        self.validar_tipo(tipo)

        # Validación de duplicado
        if self.verificar_duplicado(matricula):
            raise ValueError(f"Ya existe una persona con matrícula {matricula}")

        try:
            # Crear persona (usar constructor real del modelo)
            persona = Persona(
                nombre=nombre.strip(),
                apellido=apellido.strip(),
                matricula_empleado=matricula.strip(),
                tipo=tipo.strip(),
                correo=correo,
                telefono=telefono,
                activo=True,
            )
            db.session.add(persona)
            db.session.flush()  # Obtener persona.id

            # Agregar primer rostro
            rostro = self.agregar_rostro(
                persona_id=persona.id,
                embedding=embedding,
                imagen_bgr=imagen_bgr,
                activo=True,
            )

            db.session.commit()

            logger.info(
                f"Persona registrada: ID={persona.id} matricula={matricula}"
            )

            return {
                "persona_id": persona.id,
                "nombre": persona.nombre,
                "apellido": persona.apellido,
                "matricula": persona.matricula_empleado,
                "tipo": persona.tipo,
                "rostro_id": rostro.id,
                "activo": persona.activo,
                "fecha_registro": persona.fecha_registro.isoformat()
                if persona.fecha_registro
                else None,
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registrando persona: {e}")
            raise

    # ========================================================
    # 3.1.1 — Registrar múltiples rostros para una persona
    # ========================================================
    def agregar_multiples_rostros(
        self,
        persona_id: int,
        embeddings: List[np.ndarray],
        imagenes_bgr: Optional[List[np.ndarray]] = None,
        incluir_promedio: bool = True,
    ) -> List[Rostro]:
        """
        Agrega múltiples embeddings de rostro a una persona existente.

        Args:
            persona_id: ID de la persona.
            embeddings: Lista de vectores numpy (uno por cada muestra).
            imagenes_bgr: Lista opcional de imágenes BGR para respaldo.
            incluir_promedio: Si True, agrega un embedding promedio al final.

        Returns:
            Lista de instancias Rostro creadas.

        Raises:
            ValueError: si no hay embeddings o se supera el límite.
        """
        if not embeddings or len(embeddings) == 0:
            raise ValueError("Debe proporcionar al menos un embedding")

        if len(embeddings) > self.max_samples:
            raise ValueError(
                f"Se recibieron {len(embeddings)} embeddings, "
                f"pero el máximo es {self.max_samples}"
            )

        # 3.1.2 — Validación de máximo de muestras
        total_actual = Rostro.query.filter_by(persona_id=persona_id).count()
        nuevas = len(embeddings) + (1 if incluir_promedio else 0)

        if total_actual + nuevas > self.max_samples:
            raise ValueError(
                f"La persona ya tiene {total_actual} muestras. "
                f"Se intentan agregar {nuevas} más, "
                f"pero el máximo es {self.max_samples}"
            )

        rostros_creados: List[Rostro] = []

        # Insertar cada embedding individual
        for i, emb in enumerate(embeddings):
            if emb is None or len(emb) == 0:
                logger.warning(f"Muestra {i+1} inválida, se omite")
                continue

            imagen = imagenes_bgr[i] if imagenes_bgr and i < len(imagenes_bgr) else None

            try:
                rostro = self.agregar_rostro(
                    persona_id=persona_id,
                    embedding=emb,
                    imagen_bgr=imagen,
                    activo=True,
                )
                rostros_creados.append(rostro)
            except ValueError as e:
                # Si excede el máximo a mitad del proceso, abortar todo
                raise ValueError(f"Error en muestra {i+1}: {e}")

        # 3.1.3 — Promedio de embeddings (opcional)
        if incluir_promedio and len(embeddings) >= 2:
            try:
                embedding_promedio = np.mean(
                    np.array(embeddings, dtype=np.float64), axis=0
                ).astype(np.float32)

                # Normalizar (L2) para consistencia con Facenet512
                norma = np.linalg.norm(embedding_promedio)
                if norma > 0:
                    embedding_promedio = embedding_promedio / norma

                # Guardar el promedio con un marcador especial en imagen_respaldo
                ruta_placeholder = self._guardar_respaldo_promedio(persona_id)

                rostro_promedio = Rostro(
                    persona_id=persona_id,
                    embedding=embedding_promedio.tolist(),
                    imagen_respaldo=ruta_placeholder,
                    activo=True,
                )
                db.session.add(rostro_promedio)
                db.session.flush()
                rostros_creados.append(rostro_promedio)

                logger.info(
                    f"Embedding promedio agregado para persona_id={persona_id}"
                )
            except Exception as e:
                # El promedio es opcional: si falla, no rompemos el registro
                logger.warning(f"No se pudo agregar el embedding promedio: {e}")

        logger.info(
            f"Agregados {len(rostros_creados)} rostros a persona_id={persona_id}"
        )
        return rostros_creados

    # ========================================================
    # Helper: guardar placeholder para el embedding promedio
    # ========================================================
    def _guardar_respaldo_promedio(self, persona_id: int) -> str:
        """
        Guarda una imagen placeholder para el rostro promedio.
        Usa un nombre distintivo para poder identificarlo después.
        """
        nombre = f"persona_{persona_id}_promedio_{uuid.uuid4().hex[:8]}.jpg"
        ruta_completa = os.path.join(self.respaldo_folder, nombre)

        # Placeholder 1x1 negro
        placeholder = np.zeros((1, 1, 3), dtype=np.uint8)
        cv2.imwrite(ruta_completa, placeholder)

        return os.path.relpath(ruta_completa, start=os.getcwd()).replace("\\", "/")

    # ========================================================
    # 3.1.1 (variante) — Registrar persona + múltiples rostros juntos
    # ========================================================
    def registrar_persona_con_multiples_rostros(
        self,
        nombre: str,
        apellido: str,
        matricula: str,
        tipo: str,
        embeddings: List[np.ndarray],
        imagenes_bgr: Optional[List[np.ndarray]] = None,
        correo: Optional[str] = None,
        telefono: Optional[str] = None,
        incluir_promedio: bool = True,
    ) -> Dict[str, Any]:
        """
        Registra una persona + múltiples rostros en una sola transacción.

        Raises:
            ValueError: si el tipo es inválido, hay duplicado,
                        menos de 3 muestras, o error de integridad.
        """
        # Validar tipo ANTES que cualquier otra cosa
        self.validar_tipo(tipo)

        # Validar duplicado
        if self.verificar_duplicado(matricula):
            raise ValueError(f"Ya existe una persona con matrícula {matricula}")

        # Validar mínimo de muestras (regla del Sprint 2)
        if not embeddings or len(embeddings) < 3:
            raise ValueError(
                f"Se requieren al menos 3 muestras de rostro, "
                f"se recibieron {len(embeddings) if embeddings else 0}"
            )

        # Validar máximo considerando el promedio
        total_con_promedio = len(embeddings) + (1 if incluir_promedio else 0)
        if total_con_promedio > self.max_samples:
            raise ValueError(
                f"Se recibieron {len(embeddings)} muestras + promedio = "
                f"{total_con_promedio}, pero el máximo es {self.max_samples}"
            )

        try:
            # Crear persona
            persona = Persona(
                nombre=nombre.strip(),
                apellido=apellido.strip(),
                matricula_empleado=matricula.strip(),
                tipo=tipo.strip(),
                correo=correo,
                telefono=telefono,
                activo=True,
            )
            db.session.add(persona)
            db.session.flush()  # Obtener persona.id

            # Agregar todos los rostros
            rostros = self.agregar_multiples_rostros(
                persona_id=persona.id,
                embeddings=embeddings,
                imagenes_bgr=imagenes_bgr,
                incluir_promedio=incluir_promedio,
            )

            # Commit único
            db.session.commit()

            logger.info(
                f"Persona con múltiples rostros registrada: "
                f"ID={persona.id} matricula={matricula} rostros={len(rostros)}"
            )

            return {
                "persona_id": persona.id,
                "nombre": persona.nombre,
                "apellido": persona.apellido,
                "matricula": persona.matricula_empleado,
                "tipo": persona.tipo,
                "total_rostros": len(rostros),
                "rostros_ids": [r.id for r in rostros],
                "activo": persona.activo,
                "fecha_registro": persona.fecha_registro.isoformat()
                if persona.fecha_registro
                else None,
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registrando persona con múltiples rostros: {e}")
            raise

    # ========================================================
    # Utilidad: decodificar imagen base64
    # ========================================================
    @staticmethod
    def decodificar_base64(imagen_b64: str) -> np.ndarray:
        """
        Decodifica una imagen base64 (con o sin prefijo data:image/...) a
        numpy array BGR.

        Raises:
            ValueError: si la cadena no es decodificable.
        """
        if not imagen_b64 or not isinstance(imagen_b64, str):
            raise ValueError("Cadena base64 vacía o inválida")

        # Remover prefijo "data:image/xxx;base64,"
        if "," in imagen_b64:
            imagen_b64 = imagen_b64.split(",", 1)[1]

        try:
            imagen_bytes = base64.b64decode(imagen_b64)
            np_arr = np.frombuffer(imagen_bytes, np.uint8)
            imagen = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if imagen is None:
                raise ValueError("No se pudo decodificar la imagen")
            return imagen
        except Exception as e:
            raise ValueError(f"Error decodificando base64: {e}")