@echo off
REM Setup script for Vulture on Windows
REM Creates virtual environment and sets up Docker

echo Setting up Vulture Mod Decompiler
echo ==================================
echo.

REM Check if Python 3 is available
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo Error: Python 3 is not installed. Please install Python 3 first.
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo Warning: Docker is not installed. Docker setup will be skipped.
    echo    You can still use the virtual environment.
    set USE_DOCKER=false
) else (
    set USE_DOCKER=true
    echo Docker found
)

REM Create virtual environment
echo.
echo Creating Python virtual environment...
if exist "venv" (
    echo Warning: Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

%PYTHON_CMD% -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Virtual environment created and dependencies installed
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.

REM Docker setup
if "%USE_DOCKER%"=="true" (
    echo Setting up Docker environment...
    
    REM Create necessary directories
    if not exist "input" mkdir input
    if not exist "output" mkdir output
    if not exist "mappings" mkdir mappings
    if not exist "tools" mkdir tools
    
    echo Directories created:
    echo   - input\    (place JAR files here)
    echo   - output\   (decompiled/deobfuscated code will be here)
    echo   - mappings\ (place mapping files here)
    echo   - tools\    (optional: custom tools)
    
    echo.
    echo To build and run Docker container:
    echo   docker compose build
    echo   docker compose run --rm vulture
    echo.
    echo Or use the convenience script:
    echo   run_docker.bat
)

echo.
echo Setup complete!
echo.
echo Quick start:
echo   1. Activate venv: venv\Scripts\activate.bat
echo   2. Place JAR file in input\ directory
echo   3. Run: python mod_analyzer.py input\your_mod.jar
echo.

