@echo off
REM Double-clickable script to run Vulture Docker container on Windows
REM Automatically installs/setups on first run

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
REM Get project root (one level up from start\)
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed.
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)

REM Auto-install: Create directories if they don't exist
echo Setting up Vulture...
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "mappings" mkdir mappings
if not exist "tools" mkdir tools
echo ✓ Directories ready
echo.

REM Build if build flag is passed
if "%1"=="build" (
    echo Building Docker image...
    docker compose -f _internal/docker/docker-compose.yml build
    goto :run
)

REM Check if image exists (simplified check)
docker compose -f _internal/docker/docker-compose.yml images | findstr /C:"vulture-mod-decompiler" >nul 2>&1
if errorlevel 1 (
    echo Docker image not found. Building...
    docker compose -f _internal/docker/docker-compose.yml build
)

:run
REM Create directories if they don't exist
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "mappings" mkdir mappings
if not exist "tools" mkdir tools

echo Starting Docker container...
echo.

REM Check if there are any JAR files in input directory
dir /b input\*.jar >nul 2>&1
if errorlevel 1 (
    echo ⚠ No JAR files found in .\input\ directory
    echo.
    echo Please place JAR files in .\input\ and run this script again.
    echo.
    pause
    exit /b 0
)

echo Found JAR file(s) in input directory
echo Starting automatic processing...
echo.

REM Run container with auto-processing script
docker compose -f _internal/docker/docker-compose.yml run --rm vulture bash /workspace/process_all.sh

REM Keep window open so user can see output
echo.
echo Processing complete! Press any key to close this window...
pause >nul

