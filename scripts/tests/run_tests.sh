#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# run_tests.sh — Run the org_change_hook + org_gbrain_adapter test suite
# ──────────────────────────────────────────────────────────────────────
# Usage:
#   ./run_tests.sh              # All tests, verbose
#   ./run_tests.sh --quiet      # Quick summary only
#   ./run_tests.sh --coverage   # Requires coverage
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PASS=0
FAIL=0
FAILED_TESTS=""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Org Hook Test Suite"
echo "  Suite: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Dir:   $SCRIPT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test_file() {
    local file="$1"
    local label="$2"
    
    echo "  ⏳ $label..."
    
    if python3 "$file" -v; then
        echo "  ────────────────────────────────────────────"
        echo "  ✅ $label — ALL TESTS PASSED"
        echo ""
        PASS=$((PASS + 1))
    else
        echo "  ────────────────────────────────────────────"
        echo "  ❌ $label — SOME TESTS FAILED"
        echo ""
        FAIL=$((FAIL + 1))
        FAILED_TESTS="$FAILED_TESTS\n    - $label"
    fi
}

# Run test files
run_test_file "$SCRIPT_DIR/test_org_change_hook.py" "org_change_hook.py — Post-Change Hook"
run_test_file "$SCRIPT_DIR/test_org_gbrain_adapter.py" "org_gbrain_adapter.py — GBrain Adapter"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Passed: $PASS test files"
if [ "$FAIL" -gt 0 ]; then
    echo "  ❌ Failed: $FAIL test files"
    echo -e "  Failed:$FAILED_TESTS"
    exit 1
else
    echo "  🎉 All test files passed!"
fi
