#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# run_tests.sh — Run the org_query.py / parse_backlog.py test suite
# ──────────────────────────────────────────────────────────────────────
# Usage:
#   ./run_tests.sh              # All tests, verbose
#   ./run_tests.sh --quiet      # Quick summary only
#   ./run_tests.sh --coverage   # With coverage report (requires coverage)
#   ./run_tests.sh --watch      # Run tests, then watch for file changes
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR"

cd "$SCRIPT_DIR"

PASS=0
FAIL=0
FAILED_TESTS=""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Coy-Sprint Test Suite"
echo "  Suite: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Dir:   $SCRIPT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test_file() {
    local file="$1"
    local label="$2"
    local extra="$3"
    
    echo "  ⏳ $label..."
    
    if [ "${QUIET:-0}" = "1" ]; then
        # Quiet mode: just show pass/fail per file
        if python3 "$file" $extra 2>&1 | tail -1 | grep -q "OK"; then
            echo "  ✅ $label"
            PASS=$((PASS + 1))
        else
            echo "  ❌ $label"
            FAIL=$((FAIL + 1))
            FAILED_TESTS="$FAILED_TESTS\n    - $label"
        fi
    else
        # Verbose mode: show individual test results
        if python3 "$file" $extra; then
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
    fi
}

# ── Run Test Files ──────────────────────────────────────────────────

# org_query.py unit tests
run_test_file "$TESTS_DIR/test_org_query.py" "org_query.py — Unit Tests" "-v"

# parse_backlog.py tests
run_test_file "$TESTS_DIR/test_parse_backlog.py" "parse_backlog.py — Unit Tests" "-v"

# CLI integration tests
run_test_file "$TESTS_DIR/test_cli_integration.py" "CLI Integration Tests" "-v"

# ── Summary ─────────────────────────────────────────────────────────
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
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
