# ============================================
# SISTEMA DE CONTROL DE ACCESOS - BACKEND
# Dockerfile para el servicio de reconocimiento facial
# ============================================

# ============================================
# 1. IMAGEN BASE
# ============================================
FROM python:3.10-slim

# ============================================
# 2. METADATOS DEL MANTENEDOR
# ============================================
LABEL maintainer="Ramirez Cruz Nazario"
LABEL version="1.0.0"
LABEL description="Backend para sistema de control de accesos con reconocimiento facial"

# ============================================
# 3. VARIABLES DE ENTORNO
# ============================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Mexico_City \
    DEBIAN_FRONTEND=noninteractive

# ============================================
# 4. INSTALAR DEPENDENCIAS DEL SISTEMA
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias para OpenCV (versiones actualizadas)
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libblas-dev \
    liblapack-dev \
    # Dependencias para PostgreSQL
    libpq-dev \
    gcc \
    # Dependencias para procesamiento de imágenes
    ffmpeg \
    libavcodec-extra \
    # Herramientas útiles
    curl \
    wget \
    # Dependencias adicionales para DeepFace
    libjpeg-dev \
    libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 5. CREAR DIRECTORIO DE TRABAJO
# ============================================
WORKDIR /app

# ============================================
# 6. COPIAR ARCHIVOS DE REQUERIMIENTOS
# ============================================
COPY requirements.txt .

# ============================================
# 7. INSTALAR DEPENDENCIAS DE PYTHON
# ============================================
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# 8. INSTALAR DEEPFACE CON DEPENDENCIAS COMPLETAS
# ============================================
# DeepFace requiere tensorflow y sus dependencias
RUN pip install --no-cache-dir \
    tensorflow==2.13.0 \
    deepface==0.0.79 \
    keras==2.13.1 \
    opencv-python-headless==4.8.1.78 \
    opencv-contrib-python-headless==4.8.1.78

# ============================================
# 9. COPIAR EL CÓDIGO FUENTE
# ============================================
COPY . .

# ============================================
# 10. CREAR CARPETAS NECESARIAS
# ============================================
RUN mkdir -p /app/uploads /app/logs /app/models /app/temp

# ============================================
# 11. CONFIGURAR PERMISOS
# ============================================
RUN chmod -R 755 /app/uploads /app/logs /app/models /app/temp

# ============================================
# 12. EXPONER PUERTO
# ============================================
EXPOSE 5000

# ============================================
# 13. COMANDO DE INICIO
# ============================================
CMD ["python", "-m", "app.main"]