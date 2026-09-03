# Sistema de Control de Accesos - Reconocimiento Facial

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

Sistema de control de accesos basado en **reconocimiento facial** utilizando **DeepFace**, **Flask**, **PostgreSQL con pgvector** y **React**.

---

## Tabla de Contenidos

- [Características](#-características)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación Paso a Paso](#-instalación-paso-a-paso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Comandos Útiles](#-comandos-útiles)
- [Solución de Problemas](#-solución-de-problemas)
- [Autor](#-autor)

---

## Características

- **Reconocimiento Facial** con DeepFace (Facenet512)
- **Base de Datos Vectorial** con pgvector para embeddings faciales
- **API REST** con Flask y autenticación JWT
- **Dashboard** interactivo con React y Material-UI
- **Contenedores Docker** para fácil despliegue
- **Cámara USB** soporte para captura en tiempo real
- **Logs de accesos** y auditoría completa

---

## Requisitos del Sistema

### Hardware Mínimo
- **Procesador:** Intel Core i5 o superior
- **RAM:** 8 GB (16 GB recomendado)
- **Disco:** 50 GB de espacio libre
- **Cámara:** USB compatible (Dell WB3023 o similar)

### Software
- **Sistema Operativo:** Windows 11 (con WSL2)
- **Docker Desktop** v24.0.0 o superior
- **Git** v2.40.0 o superior
- **Visual Studio Code** (opcional, recomendado)

---

## Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/nazacru2/control-accesos.git
cd control-accesos
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# En PowerShell
code .env
```

Copia el siguiente contenido:

```env
# ============================================
# SISTEMA DE CONTROL DE ACCESOS - VARIABLES DE ENTORNO
# ============================================

# Base de datos
DB_HOST=postgres
DB_PORT=5432
DB_NAME=control_accesos
DB_USER=admin
DB_PASSWORD=*********

# Seguridad de la API
SECRET_KEY=********
JWT_EXPIRATION_HOURS=24
JWT_ALGORITHM=HS256

# Configuración de la cámara
CAMERA_TYPE=usb
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# Configuración de DeepFace
DEEPFACE_MODEL=Facenet512
DEEPFACE_DETECTOR=mtcnn
DEEPFACE_UMBRAL=0.75

# Configuración del backend
FLASK_APP=app.main
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=INFO
TZ=America/Mexico_City

# Configuración del frontend
VITE_API_URL=http://localhost:5000/api
VITE_WEBSOCKET_URL=ws://localhost:5000/ws
```

### 3. Configurar WSL2 (para cámara USB)

```bash
# En PowerShell (como Administrador)
# 1. Instalar usbipd-win
winget install usbipd

# 2. Listar dispositivos USB
usbipd list

# 3. Compartir la cámara con WSL (reemplaza BUSID)
usbipd bind --busid 1-5

# 4. En WSL (Ubuntu)
sudo apt update
sudo apt install linux-tools-virtual hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip /usr/lib/linux-tools/*/usbip 20
sudo modprobe vhci-hcd
sudo usbip attach -r <IP> -b 1-5
```

### 4. Levantar los Contenedores

```bash
# Construir y levantar todos los servicios
docker-compose up -d --build

# Verificar que los contenedores estén funcionando
docker-compose ps
```

### 5. Verificar el Sistema

```bash
# Probar health check del backend
curl.exe http://localhost:5000/api/health

# Probar conexión a la base de datos
curl.exe http://localhost:5000/api/db-test

# Verificar las tablas de PostgreSQL
docker exec -it postgres_accesos psql -U admin -d control_accesos -c "\dt"

# Probar DeepFace
docker exec -it backend_accesos python -c "from deepface import DeepFace; import numpy as np; print('OK')"

# Probar OpenCV
docker exec -it backend_accesos python -c "import cv2; print(cv2.__version__)"
```

### 6. Acceder a la Aplicación

- **Frontend:** http://localhost
- **API Health Check:** http://localhost:5000/api/health
- **Base de datos:** localhost:5432

---

## Estructura del Proyecto

```
control-accesos/
├── .env                           # Variables de entorno
├── .gitignore                     # Archivos ignorados por Git
├── docker-compose.yml             # Orquestación de contenedores
├── README.md                      # Documentación del proyecto
├── backend/                       # Backend Flask
│   ├── Dockerfile                 # Configuración del contenedor
│   ├── requirements.txt           # Dependencias de Python
│   └── app/                       # Código fuente
│       ├── __init__.py
│       ├── main.py                # Punto de entrada
│       ├── models/                # Modelos de base de datos
│       ├── routes/                # Rutas de la API
│       ├── services/              # Lógica de negocio
│       └── utils/                 # Utilidades
├── database/                      # Base de datos
│   └── init.sql                   # Script de inicialización
└── frontend/                      # Frontend React
    ├── Dockerfile                 # Configuración del contenedor
    ├── index.html                 # HTML principal
    ├── nginx.conf                 # Configuración de Nginx
    ├── package.json               # Dependencias de Node.js
    ├── src/                       # Código fuente
    │   ├── App.tsx                # Componente principal
    │   ├── index.css              # Estilos globales
    │   └── main.tsx               # Punto de entrada
    ├── tsconfig.json              # Configuración de TypeScript
    ├── tsconfig.node.json         # Configuración de TypeScript (Node)
    └── vite.config.ts             # Configuración de Vite
```

---

## Tecnologías Utilizadas

### Backend
- **Framework:** Flask 2.3.3
- **Reconocimiento Facial:** DeepFace 0.0.79, TensorFlow 2.13.0
- **Visión por Computadora:** OpenCV 4.8.1
- **Base de Datos:** PostgreSQL 15, pgvector 0.2.0
- **Autenticación:** JWT, bcrypt
- **Logging:** Prometheus, python-json-logger

### Frontend
- **Framework:** React 18, TypeScript
- **Bundler:** Vite 4.4.9
- **UI:** Material-UI 5.14.3
- **HTTP Client:** Axios 1.4.0
- **Estado:** Zustand 4.4.1, React Query 4.32.6
- **Gráficos:** Recharts 2.7.2

### Contenedores
- **Orquestación:** Docker Compose 3.8
- **Imágenes:** Python 3.10-slim, Node 18-alpine, Nginx Alpine, pgvector/pgvector:pg15

---

## Comandos Útiles

### Docker

```bash
# Levantar todos los servicios
docker-compose up -d

# Detener todos los servicios
docker-compose down

# Reconstruir un servicio específico
docker-compose up -d --build backend

# Ver logs de un servicio
docker-compose logs -f backend

# Ver estado de los contenedores
docker-compose ps

# Acceder al shell del backend
docker exec -it backend_accesos bash
```

### Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it postgres_accesos psql -U admin -d control_accesos

# Ver todas las tablas
\dt

# Ver una tabla específica
SELECT * FROM Persona;

# Salir de psql
\q
```

### Pruebas Rápidas

```bash
# Probar health check
curl.exe http://localhost:5000/api/health

# Probar conexión a la base de datos
curl.exe http://localhost:5000/api/db-test

# Probar DeepFace
docker exec -it backend_accesos python -c "from deepface import DeepFace; import numpy as np; print('OK')"

# Probar OpenCV
docker exec -it backend_accesos python -c "import cv2; print(cv2.__version__)"
```

---

## Solución de Problemas

### Error: Docker no inicia
```bash
# Habilitar WSL2
wsl --set-default-version 2
```

### Error: Puerto 80 ocupado
```bash
# Verificar qué proceso usa el puerto 80
netstat -ano | findstr :80
# Matar el proceso (reemplaza PID)
taskkill /PID <PID> /F
```

### Error: Cámara no detectada
```bash
# Verificar que la cámara esté compartida
usbipd list
# Compartir la cámara
usbipd bind --busid 1-5
# Adjuntar en WSL
sudo usbip attach -r <IP> -b 1-5
```

### Error: Conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté saludable
docker-compose ps
# Ver logs de PostgreSQL
docker-compose logs postgres
```

### Error: DeepFace tarda mucho
- La primera ejecución descarga modelos de ~200MB
- Esperar a que se complete la descarga

---

## Capturas de Pantalla

*(Agrega capturas de pantalla de la aplicación en funcionamiento)*

---

## Autor

**Nazario Ramírez Cruz**

- GitHub: [@nazacru2](https://github.com/nazacru2)
- Email: nazacru02@gmail.com

---

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## Agradecimientos

- [DeepFace](https://github.com/serengil/deepface) - Librería de reconocimiento facial
- [pgvector](https://github.com/pgvector/pgvector) - Extensión de vectores para PostgreSQL
- [Material-UI](https://mui.com/) - Componentes de interfaz de usuario

---

**¡Gracias por usar este sistema!**