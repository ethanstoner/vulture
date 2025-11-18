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

# Download CFR decompiler (latest version)
RUN wget -q https://github.com/leibnitz27/cfr/releases/latest/download/cfr.jar -O /workspace/tools/cfr.jar || \
    wget -q https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar -O /workspace/tools/cfr.jar

# Download JD-CLI (command-line version of JD-GUI)
RUN wget -q https://github.com/intoolswetrust/jd-cli/releases/download/jd-cli-1.2.0/jd-cli-1.2.0-dist.tar.gz -O /tmp/jd-cli.tar.gz && \
    tar -xzf /tmp/jd-cli.tar.gz -C /workspace/tools/ && \
    rm /tmp/jd-cli.tar.gz && \
    find /workspace/tools -name "jd-cli*.jar" -exec mv {} /workspace/tools/jd-cli.jar \;

# Download SpecialSource for applying mappings (optional - will skip if unavailable)
RUN wget -q https://github.com/md-5/SpecialSource/releases/download/1.11.0/SpecialSource-1.11.0-shaded.jar -O /workspace/tools/specialsource.jar || \
    wget -q https://repo.md-5.net/content/repositories/releases/net/md-5/SpecialSource/1.11.0/SpecialSource-1.11.0-shaded.jar -O /workspace/tools/specialsource.jar || \
    echo "SpecialSource download failed, will use text-based mappings only" || true

# Copy Python scripts from _internal/src directory
COPY _internal/src/mod_analyzer.py _internal/src/mod_deobfuscator.py _internal/src/mod_compiler.py ./

# Set environment variables
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Default command
CMD ["/bin/bash"]

