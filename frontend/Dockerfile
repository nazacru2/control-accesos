# ============================================
# SISTEMA DE CONTROL DE ACCESOS - FRONTEND
# Dockerfile simplificado (archivos estáticos)
# ============================================

FROM nginx:alpine

# Instalar herramientas útiles
RUN apk add --no-cache \
    curl \
    tzdata \
    && ln -sf /usr/share/zoneinfo/America/Mexico_City /etc/localtime \
    && echo "America/Mexico_City" > /etc/timezone

# Copiar la configuración de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos estáticos (HTML, CSS, JS)
COPY index.html /usr/share/nginx/html/index.html

# Exponer el puerto 80 (HTTP)
EXPOSE 80

# Comando de inicio (correr Nginx en primer plano)
CMD ["nginx", "-g", "daemon off;"]