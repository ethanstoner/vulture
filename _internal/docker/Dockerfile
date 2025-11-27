# Dockerfile for Vulture - Minecraft Mod Decompilation/Deobfuscation Environment
# Using Java 17 for modern mod support (records, pattern matching, etc.)
FROM eclipse-temurin:17-jdk

# Install Python 3 and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Create Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# Create directories for tools and output
RUN mkdir -p /workspace/tools /workspace/input /workspace/output /workspace/mappings

# Copy Python scripts from _internal/src directory
COPY _internal/src/mod_analyzer.py _internal/src/mod_deobfuscator.py _internal/src/mod_compiler.py _internal/src/tool_manager.py _internal/src/version_detector.py _internal/src/config.py ./

# Pre-install tools during Docker build for faster startup
# Tools will be auto-updated by tool_manager.py if newer versions are available
RUN python3 /workspace/tool_manager.py --install-tools || echo "Tool installation will happen on first run"

# Set environment variables
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Default command
CMD ["/bin/bash"]

