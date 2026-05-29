@echo off
REM Setup PostgreSQL 18 Environment Configuration

echo ============================================
echo Pharma DMS - PostgreSQL 18 Configuration
echo ============================================
echo.
echo Your PostgreSQL Settings:
echo   Username: postgres
echo   Password: Nsairaju@7
echo   Port: 5433
echo   Database: dms_db
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: backend directory not found!
    echo Please run this script from the DMS root directory.
    pause
    exit /b 1
)

REM Copy env file
if exist "backend\env_postgres18.txt" (
    copy "backend\env_postgres18.txt" "backend\.env"
    echo [SUCCESS] Created backend\.env file
    echo.
) else (
    echo ERROR: env_postgres18.txt not found!
    pause
    exit /b 1
)

echo ============================================
echo Next Steps:
echo ============================================
echo.
echo 1. Create PostgreSQL Database:
echo    psql -U postgres -p 5433 -f setup_database.sql
echo.
echo 2. Initialize DMS Tables:
echo    cd backend
echo    python scripts\init_db.py
echo.
echo 3. Start Application:
echo    cd backend
echo    python run.py
echo.
echo 4. Access API: http://localhost:8000/api/docs
echo.
echo For detailed instructions, see:
echo   POSTGRES_SETUP_INSTRUCTIONS.md
echo.
echo ============================================

pause


