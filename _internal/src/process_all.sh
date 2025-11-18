#!/bin/bash
# Auto-process JAR files - decompile or compile based on user choice

# Don't exit on error - we want to continue processing other files
set +e

INPUT_DECOMPILE_DIR="/workspace/input/to_be_decompiled"
INPUT_COMPILE_DIR="/workspace/input/to_be_compiled"
OUTPUT_DECOMPILED_DIR="/workspace/output/decompiled"
OUTPUT_COMPILED_DIR="/workspace/output/compiled"
MAPPINGS_DIR="/workspace/mappings"

echo "=========================================="
echo "Vulture - Mod Processing"
echo "=========================================="
echo ""

# Ask user what they want to do
echo "What would you like to do?"
echo "  1) Decompile JAR files"
echo "  2) Compile Java source"
echo "  3) Both (decompile then compile)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        OPERATION="decompile"
        ;;
    2)
        OPERATION="compile"
        ;;
    3)
        OPERATION="both"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Selected: $OPERATION"
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

# DECOMPILE OPERATION
if [ "$OPERATION" = "decompile" ] || [ "$OPERATION" = "both" ]; then
    echo "=========================================="
    echo "DECOMPILING JAR FILES"
    echo "=========================================="
    echo ""
    
    # Check if input directory exists and has JAR files
    if [ ! -d "$INPUT_DECOMPILE_DIR" ]; then
        echo "Error: Input directory not found: $INPUT_DECOMPILE_DIR"
        exit 1
    fi
    
    # Find all JAR files
    JAR_FILES=("$INPUT_DECOMPILE_DIR"/*.jar)
    
    if [ ! -e "${JAR_FILES[0]}" ]; then
        echo "⚠ No JAR files found in $INPUT_DECOMPILE_DIR"
        echo "Please place JAR files in input/to_be_decompiled/"
    else
        echo "Found ${#JAR_FILES[@]} JAR file(s) to decompile:"
        for jar in "${JAR_FILES[@]}"; do
            echo "  - $(basename "$jar")"
        done
        echo ""
        
        # Process each JAR file
        for jar_file in "${JAR_FILES[@]}"; do
            JAR_NAME=$(basename "$jar_file" .jar)
            echo "=========================================="
            echo "Decompiling: $JAR_NAME"
            echo "=========================================="
            echo ""
            
            DECOMPILED_PATH="$OUTPUT_DECOMPILED_DIR/$JAR_NAME"
            
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
            
            echo "✓ Decompiled: $JAR_NAME"
            echo ""
        done
        
        echo "=========================================="
        echo "Decompilation complete!"
        echo "Results in: $OUTPUT_DECOMPILED_DIR"
        echo "=========================================="
        echo ""
    fi
fi

# COMPILE OPERATION
if [ "$OPERATION" = "compile" ] || [ "$OPERATION" = "both" ]; then
        echo "=========================================="
        echo "COMPILING JAVA SOURCE"
        echo "=========================================="
        echo ""
        
        # Check if input directory exists and has source directories
        if [ ! -d "$INPUT_COMPILE_DIR" ]; then
            echo "Error: Input directory not found: $INPUT_COMPILE_DIR"
            exit 1
        fi
        
        # Find all directories (each is a mod's source code)
        SOURCE_DIRS=("$INPUT_COMPILE_DIR"/*)
        
        if [ ! -e "${SOURCE_DIRS[0]}" ]; then
            echo "⚠ No source directories found in $INPUT_COMPILE_DIR"
            echo "Please place decompiled source code in input/to_be_compiled/"
        else
            echo "Found source directory(ies) to compile:"
            for dir in "${SOURCE_DIRS[@]}"; do
                if [ -d "$dir" ]; then
                    echo "  - $(basename "$dir")"
                fi
            done
            echo ""
            
            # Process each source directory
            for source_dir in "${SOURCE_DIRS[@]}"; do
                if [ ! -d "$source_dir" ]; then
                    continue
                fi
                
                MOD_NAME=$(basename "$source_dir")
                echo "=========================================="
                echo "Compiling: $MOD_NAME"
                echo "=========================================="
                echo ""
                
                COMPILED_JAR="$OUTPUT_COMPILED_DIR/${MOD_NAME}_recompiled.jar"
                
                # Try to find original JAR in decompiled input directory
                ORIGINAL_JAR=""
                if [ -d "$INPUT_DECOMPILE_DIR" ]; then
                    # Try exact match first
                    ORIGINAL_JAR=$(find "$INPUT_DECOMPILE_DIR" -name "${MOD_NAME}.jar" 2>/dev/null | head -1)
                    # If not found, try without version suffix
                    if [ -z "$ORIGINAL_JAR" ]; then
                        BASE_NAME=$(echo "$MOD_NAME" | sed 's/-[0-9].*$//')
                        ORIGINAL_JAR=$(find "$INPUT_DECOMPILE_DIR" -name "${BASE_NAME}*.jar" 2>/dev/null | head -1)
                    fi
                    # If still not found, try any JAR that might match
                    if [ -z "$ORIGINAL_JAR" ]; then
                        ORIGINAL_JAR=$(find "$INPUT_DECOMPILE_DIR" -name "*.jar" 2>/dev/null | head -1)
                    fi
                fi
                
                if [ -n "$ORIGINAL_JAR" ] && [ -f "$ORIGINAL_JAR" ]; then
                    echo "Found original JAR: $(basename "$ORIGINAL_JAR")"
                    echo "Using it as classpath for compilation..."
                    python3 /workspace/mod_compiler.py "$source_dir" "$COMPILED_JAR" --original-jar "$ORIGINAL_JAR" || {
                        echo "Warning: Compilation failed for $MOD_NAME"
                        continue
                    }
                else
                    echo "No original JAR found, compiling without dependencies..."
                    python3 /workspace/mod_compiler.py "$source_dir" "$COMPILED_JAR" || {
                        echo "Warning: Compilation failed for $MOD_NAME"
                        continue
                    }
                fi
                echo ""
                
                echo "✓ Compiled: $MOD_NAME"
                echo ""
            done
        
        echo "=========================================="
        echo "Compilation complete!"
        echo "Results in: $OUTPUT_COMPILED_DIR"
        echo "=========================================="
        echo ""
    fi
fi

echo "=========================================="
echo "All operations complete!"
echo "=========================================="
echo ""
