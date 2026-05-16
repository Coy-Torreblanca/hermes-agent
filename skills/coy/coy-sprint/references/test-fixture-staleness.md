# Test Fixture Staleness — Dynamic Date Generation

## Problem

Static fixture files with hardcoded dates rot over time. A fixture with `SCHEDULED: <2026-05-15>` becomes "overdue" on 2026-05-16, causing date-dependent tests to fail unpredictably.

## Solution: Generate Fixtures with Relative Dates

Replace static fixture files with a function that generates content using **dates computed relative to `date.today()`**:

```python
def _make_sample_fixture():
    """Generate fixture content with dates always 30+ days in the future."""
    today = date.today()
    # Compute dates relative to today
    days_to_sat = (5 - today.weekday()) % 7
    if days_to_sat == 0:
        days_to_sat = 7
    sat = today + timedelta(days=days_to_sat + 28)
    # ... more date computation ...
    
    content = f"""\
* TODO 📖 Study Anglican liturgy before Sundays
  SCHEDULED: <{sat_str} {sat_dow} +1w>
...
"""
    # Write to temp file, return path
    fd, path = tempfile.mkstemp(suffix='.org', prefix='test_sample_habits_')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path, {'anglican': sat_str, ...}

# Usage at module level
SAMPLE_HABITS, SAMPLE_FIXTURE_DATES = _make_sample_fixture()
atexit.register(lambda p=SAMPLE_HABITS: os.unlink(p) if os.path.exists(p) else None)
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Use `tempfile.mkstemp()` | Guarantees unique path, no name collisions between test files |
| Register `atexit` cleanup | Temp files cleaned up even on test crash or early exit |
| Export expected dates dict | Tests can reference computed dates instead of hardcoding |
| Generate at **module load time** | All tests see the same fixture in a single run; no setup/teardown overhead per test class |
| Static `sample_habits.org` file removed | Replaced by generation — can never stale |

## When This Pattern Applies

- Any test fixture where dates are checked against `date.today()` (via system clock)
- Any CLI command that internally calls `date.today()` on fixture input
- NOT needed when tests pass explicit `date()` args to the function under test (those are fixed test dates, not system clock)

## Anti-Patterns

- **Moving dates to 2050+ "to be safe"** — postpones the problem, doesn't solve it. Use relative dates.
- **Only one test noticing stale fixtures** — others may silently pass with wrong assertions. All date-dependent tests should reference the computed dates dict.
- **Forgetting the day-of-week in SCHEDULED lines** — The `SCHEDULED_RE` regex expects `<YYYY-MM-DD Day Repeater>`. Omitting the day name (e.g. `<2026-08-01 +1m>`) breaks parsing.

## See Also

- `coy-sprint/scripts/tests/test_habit_query.py` — `_make_sample_fixture()` implementation, reference implementation
- `coy-sprint/scripts/tests/fixtures/streak_habits.org` — safe because streak/status tests pass explicit `date()` arguments
