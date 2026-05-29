@echo off
REM Pharma DMS - Quick Start Script for Windows

echo ==========================================
echo Pharma DMS - Quick Start
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo X Docker is not installed. Please install Docker Desktop first.
    echo   Visit: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo X Docker Compose is not installed. Please install Docker Compose first.
    echo   Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo √ Docker and Docker Compose are installed
echo.

REM Start services
echo Starting services...
docker-compose up -d

REM Wait for services to be ready
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo.
    echo X Failed to start services. Please check the logs:
    echo   docker-compose logs
    pause
    exit /b 1
)

echo.
echo ==========================================
echo √ Services started successfully!
echo ==========================================
echo.
echo Access the application at:
echo   - API Documentation: http://localhost:8000/api/docs
echo   - API: http://localhost:8000
echo   - pgAdmin: http://localhost:5050
echo.
echo Default Admin Credentials:
echo   - Username: admin
echo   - Password: Admin@123456
echo.
echo WARNING: Change the admin password after first login!
echo.
echo To view logs: docker-compose logs -f backend
echo To stop services: docker-compose down
echo ==========================================
pause

