#!/bin/bash
# QA Check Script - Verifies no secrets or personal data in repository

echo "🔍 Running QA Check on vulture..."
echo "=================================="

ERRORS=0

# Check for hardcoded secrets
echo ""
echo "Checking for hardcoded secrets..."
if grep -r "gsk_[A-Za-z0-9]\|ghp_[A-Za-z0-9]\|MTQzOTg2NjExNDcwNzU1ODQ5Mw" --include="*.py" --include="*.md" --include="*.txt" . 2>/dev/null | grep -v ".git" | grep -v "venv" | grep -v "__pycache__" | grep -v "qa-check.sh"; then
    echo "❌ Found hardcoded secrets!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ No hardcoded secrets found"
fi

# Check README exists
echo ""
echo "Checking documentation..."
if [ -f "README.md" ]; then
    echo "✅ README.md exists"
else
    echo "❌ README.md missing!"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ QA Check PASSED - No issues found"
    exit 0
else
    echo "❌ QA Check FAILED - Found $ERRORS issue(s)"
    exit 1
fi
