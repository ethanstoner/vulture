#!/bin/bash
# Double-clickable script to run Vulture Docker container on macOS
# Automatically installs/setups on first run

set -e

# Get the directory where this script is located (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project root
cd "$SCRIPT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo ""
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Press any key to close this window..."
    read -n 1 -s
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker Desktop first."
    echo ""
    echo "Press any key to close this window..."
    read -n 1 -s
    exit 1
fi

# Auto-install: Create directories if they don't exist
echo "Setting up Vulture..."
mkdir -p input output mappings tools
echo "✓ Directories ready"
echo ""

# Build if needed or if build flag is passed
if [ "$1" = "build" ]; then
    echo "Building Docker image..."
    docker compose -f docker/docker-compose.yml build
elif ! docker compose -f docker/docker-compose.yml images | grep -q vulture-mod-decompiler; then
    echo "Docker image not found. Building..."
    docker compose -f docker/docker-compose.yml build
fi

# Create directories if they don't exist
mkdir -p input output mappings tools

echo "Starting Docker container..."
echo ""

# Check if there are any JAR files in input directory
JAR_COUNT=$(find input -name "*.jar" 2>/dev/null | wc -l | tr -d ' ')

if [ "$JAR_COUNT" -eq 0 ]; then
    echo "⚠ No JAR files found in ./input/ directory"
    echo ""
    echo "Please place JAR files in ./input/ and run this script again."
    echo ""
    echo "Press any key to close this window..."
    read -n 1 -s
    exit 0
fi

echo "Found $JAR_COUNT JAR file(s) in input directory"
echo "Starting automatic processing..."
echo ""

# Run container with auto-processing script
docker compose -f docker/docker-compose.yml run --rm vulture bash /workspace/process_all.sh

# Keep terminal open so user can see output
echo ""
echo "Processing complete! Press any key to close this window..."
read -n 1 -s

