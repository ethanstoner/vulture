#!/bin/bash
# Setup script for Vulture on macOS
# Creates virtual environment and sets up Docker

set -e

echo "Setting up Vulture Mod Decompiler"
echo "=================================="
echo.

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed. Docker setup will be skipped."
    echo "   You can still use the virtual environment."
    USE_DOCKER=false
else
    USE_DOCKER=true
    echo "Docker found"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "Warning: Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Virtual environment created and dependencies installed"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""

# Docker setup
if [ "$USE_DOCKER" = true ]; then
    echo "Setting up Docker environment..."
    
    # Create necessary directories
    mkdir -p input output mappings tools
    
    echo "Directories created:"
    echo "  - input/    (place JAR files here)"
    echo "  - output/   (decompiled/deobfuscated code will be here)"
    echo "  - mappings/ (place mapping files here)"
    echo "  - tools/    (optional: custom tools)"
    
    echo ""
    echo "To build and run Docker container:"
    echo "  docker compose build"
    echo "  docker compose run --rm vulture"
    echo ""
    echo "Or use the convenience script:"
    echo "  scripts/macos/run_docker.sh"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Quick start:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Place JAR file in input/ directory"
echo "  3. Run: python mod_analyzer.py input/your_mod.jar"
echo ""

