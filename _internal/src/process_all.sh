#!/bin/bash
# Auto-process all JAR files in the input directory

# Don't exit on error - we want to continue processing other files
set +e

INPUT_DIR="/workspace/input"
OUTPUT_DIR="/workspace/output"
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

# Check for mappings
MAPPING_FILES=("$MAPPINGS_DIR"/*.srg "$MAPPINGS_DIR"/*.tsrg "$MAPPINGS_DIR"/*.txt)
MAPPINGS_FILE=""
if [ -e "${MAPPING_FILES[0]}" ]; then
    MAPPINGS_FILE="${MAPPING_FILES[0]}"
    echo "Found mapping file: $(basename "$MAPPINGS_FILE")"
    echo ""
fi

# Process each JAR file
for jar_file in "${JAR_FILES[@]}"; do
    JAR_NAME=$(basename "$jar_file" .jar)
    echo "=========================================="
    echo "Processing: $JAR_NAME"
    echo "=========================================="
    echo ""
    
    # Step 1: Analyze the mod
    echo "Step 1: Analyzing mod structure..."
    echo "-----------------------------------"
    # Change to output directory so JSON file is saved there
    cd "$OUTPUT_DIR"
    python3 /workspace/mod_analyzer.py "$jar_file" --json || {
        echo "Warning: Analysis failed for $JAR_NAME, continuing..."
    }
    cd /workspace
    echo ""
    
    # Step 2: Decompile and deobfuscate
    echo "Step 2: Decompiling and deobfuscating..."
    echo "-----------------------------------"
    OUTPUT_PATH="$OUTPUT_DIR/$JAR_NAME"
    
    if [ -n "$MAPPINGS_FILE" ]; then
        echo "Using mappings: $(basename "$MAPPINGS_FILE")"
        python3 /workspace/mod_deobfuscator.py "$jar_file" "$MAPPINGS_FILE" \
            --output "$OUTPUT_PATH" \
            --analyze || {
            echo "Warning: Deobfuscation failed for $JAR_NAME, trying without mappings..."
            python3 /workspace/mod_deobfuscator.py "$jar_file" \
                --output "$OUTPUT_PATH" || {
                echo "Error: Decompilation failed for $JAR_NAME"
            }
        }
    else
        echo "No mappings found, decompiling without deobfuscation..."
        python3 /workspace/mod_deobfuscator.py "$jar_file" \
            --output "$OUTPUT_PATH" || {
            echo "Error: Decompilation failed for $JAR_NAME"
        }
    fi
    echo ""
    
    echo "✓ Completed processing: $JAR_NAME"
    echo ""
done

echo "=========================================="
echo "All files processed!"
echo "=========================================="
echo "Results are in: $OUTPUT_DIR"
echo ""

