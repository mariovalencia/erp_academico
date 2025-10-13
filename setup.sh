#!/bin/bash

set -e

echo "🚀 Configurando entorno de desarrollo ERP..."
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Crear archivos .env si no existen
create_env_file() {
    if [ ! -f "$1" ]; then
        echo "📝 Creando $1..."
        cat > "$1" << EOF
$2
EOF
    else
        echo "✅ $1 ya existe"
    fi
}

# Crear archivo .env global
create_env_file ".env" "$(cat << EOF
# Docker Compose Environment Variables
PROJECT_NAME=erp-dev
COMPOSE_PROJECT_NAME=erp_dev

# Database
POSTGRES_DB=erp_dev
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=erp_password_secure_123
POSTGRES_HOST=database
POSTGRES_PORT=5432

# Backend
BACKEND_PORT=8000
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=django-insecure-dev-key-change-in-production

# Frontend
FRONTEND_PORT=4200
NODE_ENV=development

# PGAdmin
PGADMIN_EMAIL=admin@erp.com
PGADMIN_PASSWORD=admin_password_secure

# Network
NETWORK_NAME=erp-network
EOF
)"

# Crear archivo .env.backend
create_env_file "backend/.env.backend" "$(cat << EOF
# Django Backend Environment Variables
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend,0.0.0.0

DATABASE_URL=postgresql://erp_user:erp_password_secure_123@database:5432/erp_dev
DB_ENGINE=django.db.backends.postgresql
DB_NAME=erp_dev
DB_USER=erp_user
DB_PASSWORD=erp_password_secure_123
DB_HOST=database
DB_PORT=5432

CORS_ALLOWED_ORIGINS=http://localhost:4200,http://frontend:4200
CORS_ALLOW_ALL_ORIGINS=True
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://frontend:4200

API_VERSION=v1
API_DEBUG=True
LOG_LEVEL=DEBUG
EOF
)"

# Crear archivo .env.frontend
create_env_file "frontend/.env.frontend" "$(cat << EOF
# Angular Frontend Environment Variables
API_URL=http://localhost:8000/api
API_BASE_URL=http://backend:8000/api
API_VERSION=v1

APP_NAME=ERP Development
APP_VERSION=1.0.0
NODE_ENV=development

ENABLE_DEBUG=true
ENABLE_ANALYTICS=false

AUTH_API=http://localhost:8000/auth
REPORT_API=http://localhost:8000/reports
EOF
)"

echo "✅ Archivos de entorno creados/verificados"

# Continuar con la construcción...
docker-compose down
docker-compose up --build -d

echo "🎉 Entorno listo!"