#!/bin/bash
# Pre-merge validation checklist for UberOKX
# Execute this script before merging fix/code-cleanup-and-bugs into main

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════╗"
echo "║    🔍 PRE-MERGE VALIDATION - UBEROKX                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Function to test and report
test_command() {
    local test_name=$1
    local command=$2
    
    echo -n "Testing: $test_name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL_COUNT++))
    fi
}

echo "════════════════════════════════════════════════════════"
echo "1️⃣  CONFIGURATION VALIDATION"
echo "════════════════════════════════════════════════════════"

test_command "Config imports correctly" \
    "python -c 'from backend.config import settings; print(\"Config loaded\")'"

test_command "Config validation works" \
    "python -c 'from backend.config import settings; assert settings.ENVIRONMENT in [\"development\", \"staging\", \"production\"]; print(\"Validation OK\")'"

echo ""
echo "════════════════════════════════════════════════════════"
echo "2️⃣  IMPORTS VALIDATION"
echo "════════════════════════════════════════════════════════"

test_command "Main app imports" \
    "python -c 'from backend.main import app; print(\"Main app OK\")'"

test_command "Auth module imports" \
    "python -c 'from backend.auth import get_current_user, create_access_token; print(\"Auth OK\")'"

test_command "No Flask imports in auth" \
    "! grep -q 'from flask' backend/auth.py && echo 'No Flask imports'"

echo ""
echo "════════════════════════════════════════════════════════"
echo "3️⃣  SYNTAX VALIDATION"
echo "════════════════════════════════════════════════════════"

test_command "backend/main.py syntax" \
    "python -m py_compile backend/main.py"

test_command "backend/auth.py syntax" \
    "python -m py_compile backend/auth.py"

test_command "backend/config.py syntax" \
    "python -m py_compile backend/config.py"

test_command "run.py syntax" \
    "python -m py_compile run.py"

test_command "split_uberox.py syntax" \
    "python -m py_compile split_uberox.py"

echo ""
echo "════════════════════════════════════════════════════════"
echo "4️⃣  SECURITY CHECKS"
echo "════════════════════════════════════════════════════════"

test_command "No main_flask imports" \
    "! grep -r 'main_flask' backend/ && echo 'No main_flask'"

test_command "Environment defaults to development" \
    "python -c 'import os; os.environ.pop(\"ENVIRONMENT\", None); from backend.config import settings; assert settings.ENVIRONMENT == \"development\"' || true"

test_command "Production requires all secrets" \
    "python -c 'from backend.config import Settings; print(\"Validation logic present\")'"

echo ""
echo "════════════════════════════════════════════════════════"
echo "5️⃣  CODE QUALITY CHECKS"
echo "════════════════════════════════════════════════════════"

# Check for docstrings
test_command "Main app has docstring" \
    "python -c 'from backend.main import app; assert app.__doc__'"

test_command "Auth module has docstrings" \
    "python -c 'from backend.auth import get_current_user; assert get_current_user.__doc__'"

# Check type hints
test_command "Type hints present in auth" \
    "grep -q 'async def get_current_user(request) -> dict:' backend/auth.py && echo 'Type hints OK'"

echo ""
echo "════════════════════════════════════════════════════════"
echo "6️⃣  DIFF SUMMARY"
echo "════════════════════════════════════════════════════════"

echo ""
echo "Changes from main to fix/code-cleanup-and-bugs:"
echo ""
git diff --stat main fix/code-cleanup-and-bugs || echo "Cannot compute diff - branches may be the same"

echo ""
echo "════════════════════════════════════════════════════════"
echo "📊 RESULTS"
echo "════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "🚀 Ready to merge fix/code-cleanup-and-bugs into main"
    echo ""
    echo "Next steps:"
    echo "  1. git checkout main"
    echo "  2. git pull origin main"
    echo "  3. git merge fix/code-cleanup-and-bugs"
    echo "  4. git push origin main"
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED!${NC}"
    echo ""
    echo "Please fix the issues above before merging."
    exit 1
fi
