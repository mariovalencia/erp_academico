@echo off
echo 🚀 Configurando entorno de desarrollo ERP...
echo ==============================================

:: Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está instalado o no está en el PATH
    exit /b 1
)

:: Verificar Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose no está instalado o no está en el PATH
    exit /b 1
)

echo ✅ Dependencias verificadas

:: Construir y levantar contenedores
echo 📦 Construyendo y levantando contenedores...
docker-compose down
docker-compose up --build -d

echo ⏳ Esperando a que los servicios estén listos...
timeout 30

echo 🔍 Verificando estado de los contenedores...
docker-compose ps

echo.
echo 🎉 ¡Entorno de desarrollo configurado exitosamente!
echo.
echo 🌐 URLs de acceso:
echo    Frontend ^(Angular^): http://localhost:4200
echo    Backend ^(Django^):   http://localhost:8000
echo    PGAdmin:              http://localhost:5050
echo.
echo 💡 Para detener el entorno: docker-compose down