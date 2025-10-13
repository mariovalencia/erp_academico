#!/bin/bash

# Script de configuración del entorno de desarrollo ERP
# UBICACIÓN: Debe estar en la raíz del proyecto, junto a docker-compose.yml

set -e  # Detener ejecución en caso de error

echo "🚀 Configurando entorno de desarrollo ERP..."
echo "=============================================="
echo "Directorio actual: $(pwd)"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: El script debe ejecutarse desde el directorio raíz del proyecto"
    echo "   donde se encuentra el archivo docker-compose.yml"
    exit 1
fi

# Verificar Docker y Docker Compose
echo "🔍 Verificando dependencias..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor, instala Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor, instálalo primero."
    exit 1
fi

echo "✅ Dependencias verificadas"

# Crear estructura de directorios si no existen
echo "📁 Creando estructura de directorios..."
mkdir -p backend/src frontend/src database

# Verificar archivos esenciales
if [ ! -f "backend/Dockerfile" ]; then
    echo "⚠️  Advertencia: backend/Dockerfile no encontrado"
fi

if [ ! -f "frontend/Dockerfile" ]; then
    echo "⚠️  Advertencia: frontend/Dockerfile no encontrado"
fi

# Construir y levantar los contenedores
echo "📦 Construyendo y levantando contenedores..."
docker-compose down  # Limpiar contenedores previos
docker-compose up --build -d

echo "⏳ Esperando a que los servicios estén listos..."
# Esperar a que PostgreSQL esté listo
for i in {1..30}; do
    if docker-compose exec database pg_isready -U erp_user; then
        echo "✅ PostgreSQL está listo"
        break
    fi
    echo "⏱️  Esperando a PostgreSQL... ($i/30)"
    sleep 2
done

# Esperar a que Backend esté listo
for i in {1..30}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "✅ Backend está listo"
        break
    fi
    echo "⏱️  Esperando al Backend... ($i/30)"
    sleep 2
done

# Verificar estado de los contenedores
echo "🔍 Verificando estado de los contenedores..."
docker-compose ps

echo ""
echo "🎉 ¡Entorno de desarrollo configurado exitosamente!"
echo ""
echo "🌐 URLs de acceso:"
echo "   Frontend (Angular):  http://localhost:4200"
echo "   Backend (Django):    http://localhost:8000"
echo "   Database (PostgreSQL): localhost:5432"
echo "   PGAdmin:             http://localhost:5050"
echo ""
echo "📊 Credenciales de base de datos:"
echo "   Database: erp_dev"
echo "   User:     erp_user"
echo "   Password: erp_password"
echo ""
echo "🔧 Comandos útiles:"
echo "   docker-compose logs -f backend      # Ver logs del backend"
echo "   docker-compose logs -f frontend     # Ver logs del frontend"
echo "   docker-compose exec backend python manage.py createsuperuser"
echo "   docker-compose down                 # Detener contenedores"
echo "   docker-compose restart              # Reiniciar servicios"
echo ""
echo "💡 Para detener el entorno: docker-compose down"