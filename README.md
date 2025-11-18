# Vulture

A comprehensive toolkit for analyzing, decompiling, and deobfuscating Minecraft mods. Vulture picks apart mod JARs to reveal their inner workings, making it perfect for security researchers, mod developers, and anyone who needs to inspect mod behavior in a safe, isolated environment.

## Features

- **Static Analysis**: Analyze mod JAR files without execution
- **Decompilation**: Convert compiled bytecode back to readable Java source
- **Deobfuscation**: Apply MCP/ProGuard mappings to restore readable names
- **Security Detection**: Automatically identify suspicious patterns (webhooks, token access, network code)
- **Isolated Execution**: All tools run in Docker containers for safety
- **Multiple Decompilers**: Support for CFR, JD-CLI, and Fernflower

## Requirements

- Python 3.8+
- Docker and Docker Compose (recommended)
- Java 8+ (optional, if not using Docker)

**Platform Support:**
- Windows (PowerShell/CMD)
- macOS (Terminal)
- Linux (Bash)

## Quick Start

### Automatic Processing (Easiest Method)

**Simply place your JAR files in the `input/` directory and run the platform-specific script:**

**macOS:**
- Double-click `Run Vulture (macOS).command`

**Windows:**
- Double-click `Run Vulture (Windows).bat`

**Linux:**
- Run: `bash Run\ Vulture\ \(Linux\).sh`

The script will automatically:
1. Build the Docker image (if needed)
2. Analyze all JAR files in `input/`
3. Decompile and deobfuscate (if mappings are available)
4. Save all results to `output/`

### Manual Docker Usage

For advanced users who want to run tools manually:

```bash
# Build the Docker image
docker compose -f docker/docker-compose.yml build

# Run analysis on a mod
docker compose -f docker/docker-compose.yml run --rm vulture python3 /workspace/mod_analyzer.py input/your_mod.jar

# Decompile a mod
docker compose -f docker/docker-compose.yml run --rm vulture python3 /workspace/mod_deobfuscator.py input/your_mod.jar --output output/mod_name
```

**Note:** For most users, the automatic processing scripts are recommended.

### Using Local Python Environment

For local development (not recommended for most users):

**On Linux/macOS:**
```bash
# Setup virtual environment
bash scripts/linux/setup.sh  # or scripts/macos/setup.sh
source venv/bin/activate

# Analyze a mod
python src/mod_analyzer.py input/your_mod.jar

# Decompile a mod
python src/mod_deobfuscator.py input/your_mod.jar --output output/mod_name
```

**On Windows:**
```cmd
REM Setup virtual environment
scripts\windows\setup.bat
venv\Scripts\activate.bat

REM Analyze a mod
python src\mod_analyzer.py input\your_mod.jar

REM Decompile a mod
python src\mod_deobfuscator.py input\your_mod.jar --output output\mod_name
```

**Note:** Docker is the recommended method. Local setup requires Java 8+ and manual decompiler installation.

## Project Structure

```
.
├── Run Vulture (macOS).command    # Start Vulture on macOS (double-click)
├── Run Vulture (Windows).bat      # Start Vulture on Windows (double-click)
├── Run Vulture (Linux).sh         # Start Vulture on Linux
├── docker/                         # Docker configuration (internal)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
├── src/                            # Source code (internal)
│   ├── mod_analyzer.py
│   ├── mod_deobfuscator.py
│   └── process_all.sh
├── requirements.txt                # Python dependencies
├── LICENSE                         # License file
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── input/                          # Place JAR files here
├── output/                         # Decompiled code output
├── mappings/                       # MCP/ProGuard mapping files
└── tools/                          # Custom decompiler tools (optional)
```

## Usage

### Mod Analyzer

Analyzes mod structure and detects security patterns without modifying the JAR:

```bash
# Basic analysis (inside Docker container)
docker compose run --rm vulture python3 /workspace/mod_analyzer.py input/mod.jar

# Save results to JSON
docker compose run --rm vulture python3 /workspace/mod_analyzer.py input/mod.jar --json
```

The analyzer reports:
- Class and resource listings
- Mod metadata (mcmod.info)
- Security patterns (webhooks, token access, network code)
- Suspicious string patterns

### Mod Deobfuscator

Decompiles and optionally deobfuscates mods:

```bash
# Basic decompilation (inside Docker container)
docker compose run --rm vulture python3 /workspace/mod_deobfuscator.py input/mod.jar --output output/mod_name

# With MCP mappings (deobfuscation)
docker compose run --rm vulture python3 /workspace/mod_deobfuscator.py input/mod.jar mappings/joined.srg --output output/mod_name

# Full analysis after deobfuscation
docker compose run --rm vulture python3 /workspace/mod_deobfuscator.py input/mod.jar mappings/joined.srg --output output/mod_name --analyze

# Choose specific decompiler
docker compose run --rm vulture python3 /workspace/mod_deobfuscator.py input/mod.jar --decompiler jd-cli --output output/mod_name
```

**Supported Decompilers:**
- **CFR** (default): Best accuracy, handles modern Java features
- **JD-CLI**: Fast, good for quick inspection
- **Fernflower**: IntelliJ-style output (requires manual download)

## Obtaining Mappings

Mappings translate obfuscated Minecraft names back to readable ones. Required for proper deobfuscation.

**Minecraft uses ProGuard obfuscation**, which converts readable names to short ones:
- `Minecraft.getMinecraft()` → `a.a()`
- `Session.getToken()` → `b.c()`

Mappings reverse this process to restore readable names.

### MCPBot (Recommended for older versions)

```bash
# Download for Minecraft 1.8.9
wget http://export.mcpbot.bspk.rs/mcp_snapshot/1.8.9/mcp_snapshot-1.8.9.zip
unzip mcp_snapshot-1.8.9.zip -d mappings/
```

### Forge Mappings

Forge provides official mappings for recent versions:
- Visit https://files.minecraftforge.net/
- Download `*-mappings.zip` for your Minecraft version
- Extract to `mappings/` directory

### ProGuard Mapping File

If you have a ProGuard `mapping.txt` file:
```bash
docker compose run --rm vulture python3 /workspace/mod_deobfuscator.py input/mod.jar mappings/mapping.txt --output output/mod_name
```

## Decompilation Quality

**What decompiles well:**
- ✅ Simple classes and methods
- ✅ Standard Java patterns
- ✅ Public APIs and interfaces

**What may not decompile perfectly:**
- ⚠️ Lambda expressions (may show as synthetic methods)
- ⚠️ Obfuscated code (variable names lost)
- ⚠️ Inline optimizations (may be restructured)

**Note:** Decompiled code may not be 100% accurate, especially with heavy obfuscation. Variable names are often auto-generated.

## Docker Details

The Docker image includes:
- Java 8 (Eclipse Temurin)
- Python 3 with required dependencies
- CFR decompiler (auto-downloaded)
- JD-CLI decompiler (auto-downloaded)
- SpecialSource (for applying mappings)

**Volume Mounts:**
- `./input` → `/workspace/input` (read-only)
- `./output` → `/workspace/output` (read-write)
- `./mappings` → `/workspace/mappings` (read-only)

**Interactive Shell:**

On Linux/macOS:
```bash
docker compose run --rm vulture
# You're now inside the container at /workspace
```

On Windows:
```cmd
docker compose run --rm vulture
REM You're now inside the container at /workspace
```

## Output Structure

When you run the automatic processing, results are saved in the `output/` directory:

```
output/
├── mod-name_analysis.json          # Analysis report (JSON format)
└── mod-name/                       # Decompiled source code
    ├── summary.txt                 # Decompilation summary
    └── [package structure]/        # Organized Java source files
        └── *.java                  # Decompiled class files
```

**Analysis JSON** contains:
- Mod metadata and file counts
- Class analysis (GUI, network, data classes)
- Security flags and suspicious patterns
- Resource listings

**Decompiled Code** includes:
- All Java source files organized by package
- Readable code structure (variable names may be auto-generated)
- Summary of decompilation process

## Security Analysis

The tools automatically detect common malicious patterns:

- Discord webhook URLs
- Token/session access patterns
- HTTP/HTTPS network requests
- Reflection usage for obfuscation
- Suspicious string patterns

Example output:
```
Security Analysis Results:
- Webhook references found in: com.example.ModClass
- Token access detected in: com.example.SessionUtils
- Network code found in: com.example.NetworkHandler
```

## Troubleshooting

**Decompiler not found**
- Ensure you're using Docker (decompilers are pre-installed)
- Or manually download decompiler JARs to `tools/` directory

**Mappings file not found**
- Download mappings using methods described above
- Place in `mappings/` directory

**Java not found (local environment)**
- Install Java 8+ or use Docker instead

**Docker build fails**
```bash
docker compose down
docker compose build --no-cache
```

## Limitations

- Decompiled code may not be 100% accurate, especially with heavy obfuscation
- Some control flow may be simplified or altered
- Variable names are often lost and regenerated
- Large mods may take several minutes to decompile

## Legal and Ethical Considerations

- Only analyze mods you own or have explicit permission to analyze
- Use findings responsibly and report vulnerabilities through proper channels
- This toolkit is for educational and security research purposes
- Respect intellectual property and licensing of analyzed mods

## Resources

- [CFR Decompiler](https://github.com/leibnitz27/cfr)
- [JD-GUI](https://java-decompiler.github.io/)
- [MCPBot](http://mcpbot.bspk.rs/)
- [SpecialSource](https://github.com/md-5/SpecialSource)
- [Minecraft Forge](https://files.minecraftforge.net/)

## License

This project is provided for educational use only. Use responsibly and ethically.
