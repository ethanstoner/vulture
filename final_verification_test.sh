#!/bin/bash
# Final comprehensive verification test
# Simulates a fresh user experience

set -e

PROJECT_ROOT="/home/ethan/vulture"
cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     FINAL COMPREHENSIVE VERIFICATION TEST                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

test_check() {
    local name=$1
    local cmd=$2
    
    echo -n "Testing $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✓ PASS"
        ((PASSED++))
        return 0
    else
        echo "✗ FAIL"
        ((FAILED++))
        return 1
    fi
}

echo "=== Core Functionality Tests ==="
echo ""

# Test 1: Docker build
test_check "Docker Build" "docker compose -f _internal/docker/docker-compose.yml build -q"

# Test 2: Python syntax
test_check "Python Syntax" "python3 -m py_compile _internal/src/*.py"

# Test 3: Imports
test_check "Python Imports" "python3 -c 'import sys; sys.path.insert(0, \"_internal/src\"); from tool_manager import ToolManager; from version_detector import VersionDetector; from config import Config'"

# Test 4: Tool Manager CLI
test_check "Tool Manager CLI" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/tool_manager.py --help | grep -q usage"

# Test 5: Version Detection
test_check "Version Detection" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/version_detector.py /workspace/input/to_be_decompiled/TestMod-1.0.0.jar | grep -q Detected"

# Test 6: Mod Analyzer
test_check "Mod Analyzer" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/mod_analyzer.py /workspace/input/to_be_decompiled/TestMod-1.0.0.jar | grep -q 'MOD ANALYSIS REPORT'"

# Test 7: Decompilation
test_check "Decompilation" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/mod_deobfuscator.py /workspace/input/to_be_decompiled/TestMod-1.0.0.jar --output /workspace/output/decompiled/final_test --no-auto-download | grep -q Decompiled"

# Test 8: Decompiled Output Exists
test_check "Decompiled Output" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture test -f /workspace/output/decompiled/final_test/com/example/testmod/TestMod.java"

# Test 9: Config Management
test_check "Config Management" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/config.py --list | grep -q default_mc_version"

# Test 10: All Mod Types
echo ""
echo "=== Mod Type Compatibility Tests ==="
echo ""

for mod in TestForge-1.8.9.jar TestForge-1.21.jar TestFabric-1.8.9.jar TestFabric-1.21.jar; do
    if [ -f "input/to_be_decompiled/$mod" ]; then
        test_check "$mod" "docker compose -f _internal/docker/docker-compose.yml run --rm vulture python3 /workspace/mod_deobfuscator.py /workspace/input/to_be_decompiled/$mod --output /workspace/output/decompiled/test_${mod%.jar} --no-auto-download | grep -q Decompiled"
    fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    TEST RESULTS                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - SYSTEM VERIFIED AND WORKING"
    exit 0
else
    echo "✗ SOME TESTS FAILED - REVIEW REQUIRED"
    exit 1
fi
