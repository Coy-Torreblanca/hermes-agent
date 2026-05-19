# Retro & Stale — Phase 4 Sprint Intelligence Commands

## `org_query.py --retro <sprint|all>`

**File:** `~/.hermes/scripts/org_query.py`

Generates a sprint retrospective report from the org file.

```bash
# Sprint 4 retro
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --retro 4

# All sprints aggregated (⚠️ see pitfall below)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --retro all
```

**Output keys:** `sprint`, `committed`, `completed`, `cancelled`, `completion_ratio`, `velocity_pts`, `blocked_count`, `blocked_items`, `completed_items`, `cancelled_items`, `pain_points`

### Sprint Boundaries (Date Derivation)

Sprint start/end dates are derived from the **Bi-Weekly Sprint Cleanup & Planning** habit in `sprint_habits.org`. See [[concepts/sprint-date-derivation]].

| Boundary | Source |
|----------|--------|
| Sprint Start | Last `- State "DONE" from ...` LOGBOOK timestamp |
| Sprint End | `SCHEDULED:` date of the cleanup habit |

## Understanding `--retro` vs `--sprint` Point Totals

**The two commands report different numbers for "committed points" — understand the difference.**

| Command | What it shows | Example (Sprint 4) |
|---------|---------------|-------------------|
| `--sprint N` | ALL headings with `:SPRINT: N`, **including EPICs** with cumulative child sums | 188pts |
| `--retro N` | Non-EPIC items only (EPICs are containers, not work items) | 97pts committed |

**Why the discrepancy:** The `--sprint` command shows EPIC rows with accumulated child totals (e.g., EPIC Personal AI v1 = 83pts = sum of all children under it with SPRINT:4). The EPIC's own `:POINTS:` is often 0 — the 83 is a presentation convenience. But if you sum `--sprint` output literally, you double-count those child points.

**Rule:** Use `--retro N` for committed scope. Use `--sprint N` only for listing items. Don't sum `--sprint` output for sprint commitment totals.

[Source: Investigation, 2026-05-18 — corrected earlier misquote of 188 vs 97]

### ⚠️ Pitfall: `%^{...}` Org Template Values Crash `--retro all`

The `compute_retro()` function calls `int(h['properties'].get('POINTS', '0'))` on every item. If any item has a raw org‑mode capture‑template prompt like `%^{POINTS}p` in its `:POINTS:` property (an Emacs interactive prompt that wasn't replaced during capture), `int()` raises `ValueError` and the command crashes.

**Fix:** Wrap the `int()` call in a try/except that falls back to `0`:
```python
try:
    points = int(h['properties'].get('POINTS', '0'))
except (ValueError, TypeError):
    points = 0
```

**Status:** Discovered and fixed 2026-05-18. `compute_retro()` wraps `int()` in try/except.

---

## `parse_backlog.py --stale N`

**File:** `/data/.hermes/skills/coy/coy-sprint/scripts/parse_backlog.py`

Flags backlog items untouched for N+ sprint cycles (~2 weeks per sprint).

```bash
# Items stale for 2+ sprints (~4 weeks)
python3 scripts/parse_backlog.py --stale 2

# With custom point budget
python3 scripts/parse_backlog.py --stale 3 --max-points 8
```

**Behavior:**
- Without `--stale`: no change from default output
- With `--stale N`: items older than N sprint cycles get a `⏰` prefix
- Stale age calculated from `:CREATED:` property compared to `date.today()`
- Items without `:CREATED:` dates are not flagged as stale
- `--max-points` still limits total committed points shown

### Known Nuances
- `:CREATED:` values can include day names and times (e.g. `[2026-03-23 Mon 18:30]`). The parser uses `re.search` to find the date, so any format works.
- The `:CREATED:` property is parsed at the STORY/TODO heading level, not inherited from parents.

[Source: Implementation, 2026-05-18]
