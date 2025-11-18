#!/bin/bash
# Run Vulture - Linux launcher

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VULTURE_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Change to vulture directory (project root)
cd "$VULTURE_DIR"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

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
    echo "Or run interactively with: docker compose -f docker/docker-compose.yml run --rm vulture"
    exit 0
fi

echo "Found $JAR_COUNT JAR file(s) in input directory"
echo "Starting automatic processing..."
echo ""

# Run container with auto-processing script
docker compose -f docker/docker-compose.yml run --rm vulture bash /workspace/process_all.sh

