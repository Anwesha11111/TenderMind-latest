@echo off
echo ==============================================
echo   TenderMind Setup (Local AI Mode)
echo ==============================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found. Install Docker Desktop.
    pause
    exit /b 1
)
echo [OK] Docker found

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found.
    pause
    exit /b 1
)
echo [OK] Docker Compose found

echo.
echo Checking .env file...
if not exist ".env" (
<<<<<<< HEAD
    echo Creating default .env file...
    echo POSTGRES_DB=tendermind > .env
    echo DATABASE_URL=postgresql://postgres:password@db:5432/tendermind >> .env
    echo REDIS_URL=redis://redis:6379/0 >> .env
    echo [OK] .env file created
) else (
    echo [OK] .env file already exists
)

=======
    echo Creating default .env file for Mock AI Simulation
    echo MOCK_LLM="true" > .env
    echo OLLAMA_BASE_URL="http://192.168.1.55:11434" >> .env
    echo [OK] Created .env file
) else (
    echo [OK] .env file found
)
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6
echo.
echo ==============================================
echo   Setup Complete! (Offline Mode)
echo ==============================================
echo.
echo NOTE: First run will download local models (FLAN-T5, etc.)
echo This may take several minutes depending on your connection.
echo.
echo NEXT STEPS:
echo   Start the system:
echo      docker-compose up -d
echo.
echo   View logs (Model download progress):
echo      docker-compose logs -f celery-worker
echo.
echo   Services:
echo      - API:     http://localhost:8000/api/docs
echo      - Frontend: http://localhost:3000
echo.
pause
