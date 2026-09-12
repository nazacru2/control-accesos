# ============================================
# SISTEMA DE CONTROL DE ACCESOS - BACKEND
# Dockerfile optimizado para tu requirements.txt
# SPRINT 1
# ============================================

# ============================================
# 1. IMAGEN BASE
# ============================================
FROM python:3.10-slim

# ============================================
# 2. METADATOS
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
    # Dependencias para OpenCV
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    # Dependencias para PostgreSQL
    libpq-dev \
    gcc \
    # Dependencias para procesamiento de imágenes
    ffmpeg \
    libavcodec-extra \
    libjpeg-dev \
    libpng-dev \
    # Herramientas útiles
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 5. CREAR DIRECTORIO DE TRABAJO
# ============================================
WORKDIR /app

# ============================================
# 6. COPIAR Y INSTALAR DEPENDENCIAS
# ============================================
COPY requirements.txt .

# Instalar dependencias en una sola capa para optimizar
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# 7. COPIAR EL CÓDIGO FUENTE
# ============================================
COPY . .

# ============================================
# 8. CREAR CARPETAS NECESARIAS
# ============================================
RUN mkdir -p /app/uploads /app/logs /app/models /app/temp \
    /app/capturas /app/rostros

# ============================================
# 9. CONFIGURAR PERMISOS
# ============================================
RUN chmod -R 755 /app/uploads /app/logs /app/models /app/temp \
    /app/capturas /app/rostros

# ============================================
# 10. EXPONER PUERTO
# ============================================
EXPOSE 5000

# ============================================
# 11. COMANDO DE INICIO
# ============================================
CMD ["python", "run.py"]