# Testing Suite — Coy-Sprint Scripts

Automated tests for `org_query.py`, `parse_backlog.py`, and `capture-items.sh`.

## Quick Start

```bash
# Run all tests (verbose)
./run_tests.sh

# Quick summary only
./run_tests.sh --quiet

# Run a specific test file
python3 test_org_query.py -v
python3 test_parse_backlog.py -v
python3 test_cli_integration.py -v

# With coverage report (requires: pip install coverage)
coverage run --source=.. test_org_query.py
coverage report -m
```

## Test Files

| File | Coverage | Scope |
|------|----------|-------|
| `test_org_query.py` | 28 tests | Unit tests: `parse_org`, `find_epic`, `find_active`, `sprint_items`, `insert_point`, `children_of`, `find_heading`, `validate`, `stats`, property parsing, edge cases |
| `test_parse_backlog.py` | 10 tests | Backlog filtering, value sort order, max-points, value-only filter, item exclusion |
| `test_cli_integration.py` | 18 tests | End-to-end: every CLI command, error cases, edge cases |

## Fixtures

| File | Purpose |
|------|---------|
| `fixtures/sample_tasks.org` | Full EPIC hierarchy with DONE/STARTED/NEXT/BACKLOG items across 4 EPICs |
| `fixtures/sample_backlog.org` | Backlog-specific fixture with mixed sprint values |
| `fixtures/edge_cases.org` | WIP violations, empty EPICs, missing properties |

## Adding Tests

1. Add test fixtures to `fixtures/` if you need custom org data
2. Add test methods to the appropriate `test_*.py` file
3. Run `./run_tests.sh` to verify nothing breaks

### Naming Convention

- Test methods: `test_<what_is_being_tested>`
- Fixture files: `descriptive_name.org`
- Test helper functions start with `assert_` or use regular `snake_case`

## When to Run

- **Before** any PR or deployment that modifies `org_query.py` or `parse_backlog.py`
- **After** refactoring, new features, or bug fixes
- **Periodically** to catch regressions from org file structure changes

## Architecture

```
scripts/tests/
├── run_tests.sh              # Test runner (bash)
├── README.md                 # This file
├── test_org_query.py         # Unit tests for org_query.py (28 tests)
├── test_parse_backlog.py     # Unit tests for parse_backlog.py (10 tests)
├── test_cli_integration.py   # CLI end-to-end tests (18 tests)
└── fixtures/
    ├── sample_tasks.org      # Main fixture: 4 EPICs, varied keywords/properties
    ├── sample_backlog.org    # Backlog-specific fixture
    └── edge_cases.org        # Edge cases: WIP violations, empty EPICs
```
