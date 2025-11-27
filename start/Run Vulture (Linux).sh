#!/bin/bash
# Run Vulture - Linux launcher
# Automatically installs/setups on first run

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get project root (one level up from start/)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo ""
    echo "Please install Docker. On Ubuntu/Debian:"
    echo "  sudo apt-get update && sudo apt-get install docker.io"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker first."
    echo ""
    echo "On Linux, you may need to start the Docker service:"
    echo "  sudo systemctl start docker"
    echo ""
    exit 1
fi

# Auto-install: Create directories if they don't exist
echo "Setting up Vulture..."
mkdir -p input/to_be_decompiled input/to_be_compiled output/decompiled output/compiled
echo "✓ Directories ready"
echo ""

# Build if needed or if build flag is passed
if [ "$1" = "build" ]; then
    echo "Building Docker image..."
    docker compose -f _internal/docker/docker-compose.yml build
elif ! docker compose -f _internal/docker/docker-compose.yml images | grep -q vulture-mod-decompiler; then
    echo "Docker image not found. Building..."
    docker compose -f _internal/docker/docker-compose.yml build
fi

# Create directories if they don't exist
mkdir -p input output mappings tools

echo "Starting Docker container..."
echo ""

# Run container with interactive processing script
docker compose -f _internal/docker/docker-compose.yml run --rm -it vulture bash /workspace/process_all.sh

