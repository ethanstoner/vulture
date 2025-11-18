#!/bin/bash
# Auto-process all JAR files in the input directory

# Don't exit on error - we want to continue processing other files
set +e

INPUT_DIR="/workspace/input"
DECOMPILED_DIR="/workspace/decompiled"
COMPILED_DIR="/workspace/compiled"
MAPPINGS_DIR="/workspace/mappings"

echo "=========================================="
echo "Vulture - Auto-Processing JAR Files"
echo "=========================================="
echo ""

# Check if input directory exists and has JAR files
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory not found: $INPUT_DIR"
    exit 1
fi

# Find all JAR files
JAR_FILES=("$INPUT_DIR"/*.jar)

if [ ! -e "${JAR_FILES[0]}" ]; then
    echo "No JAR files found in $INPUT_DIR"
    echo "Please place JAR files in the input/ directory"
    exit 0
fi

echo "Found ${#JAR_FILES[@]} JAR file(s) to process:"
for jar in "${JAR_FILES[@]}"; do
    echo "  - $(basename "$jar")"
done
echo ""

# Check for mappings (optional - create _internal/mappings/ if you have mapping files)
MAPPINGS_FILE=""
if [ -d "$MAPPINGS_DIR" ]; then
    MAPPING_FILES=("$MAPPINGS_DIR"/*.srg "$MAPPINGS_DIR"/*.tsrg "$MAPPINGS_DIR"/*.txt)
    if [ -e "${MAPPING_FILES[0]}" ]; then
        MAPPINGS_FILE="${MAPPING_FILES[0]}"
        echo "Found mapping file: $(basename "$MAPPINGS_FILE")"
        echo ""
    fi
fi

# Process each JAR file
for jar_file in "${JAR_FILES[@]}"; do
    JAR_NAME=$(basename "$jar_file" .jar)
    echo "=========================================="
    echo "Processing: $JAR_NAME"
    echo "=========================================="
    echo ""
    
    # Step 1: Decompile and deobfuscate
    echo "Step 1: Decompiling and deobfuscating..."
    echo "-----------------------------------"
    DECOMPILED_PATH="$DECOMPILED_DIR/$JAR_NAME"
    
    if [ -n "$MAPPINGS_FILE" ]; then
        echo "Using mappings: $(basename "$MAPPINGS_FILE")"
        python3 /workspace/mod_deobfuscator.py "$jar_file" "$MAPPINGS_FILE" \
            --output "$DECOMPILED_PATH" || {
            echo "Warning: Deobfuscation failed for $JAR_NAME, trying without mappings..."
            python3 /workspace/mod_deobfuscator.py "$jar_file" \
                --output "$DECOMPILED_PATH" || {
                echo "Error: Decompilation failed for $JAR_NAME"
                continue
            }
        }
    else
        echo "No mappings found, decompiling without deobfuscation..."
        python3 /workspace/mod_deobfuscator.py "$jar_file" \
            --output "$DECOMPILED_PATH" || {
            echo "Error: Decompilation failed for $JAR_NAME"
            continue
        }
    fi
    echo ""
    
    # Step 2: Compile back to JAR
    echo "Step 2: Compiling back to JAR..."
    echo "-----------------------------------"
    COMPILED_JAR="$COMPILED_DIR/${JAR_NAME}_recompiled.jar"
    
    if [ -d "$DECOMPILED_PATH" ]; then
        python3 /workspace/mod_compiler.py "$DECOMPILED_PATH" "$COMPILED_JAR" || {
            echo "Warning: Compilation failed for $JAR_NAME"
        }
    else
        echo "Warning: Decompiled directory not found, skipping compilation"
    fi
    echo ""
    
    echo "✓ Completed processing: $JAR_NAME"
    echo ""
done

echo "=========================================="
echo "All files processed!"
echo "=========================================="
echo "Decompiled source code: $DECOMPILED_DIR"
echo "Recompiled JAR files: $COMPILED_DIR"
echo ""

