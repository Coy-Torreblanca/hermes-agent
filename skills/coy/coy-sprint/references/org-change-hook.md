# Org Change Hook — Post-Write gbrain Integration

> The org change hook is always active in `org_query.py`. Every `--create-todo` call
> captures pre/post file state, computes a structured diff, classifies the change,
> and logs it to the gbrain audit log. No env var to toggle.

## Scripts

| Script | Path | Purpose |
|--------|------|---------|
| `org_change_hook.py` | `~/.hermes/scripts/` | Post-change hook: pre/post snapshots, diff computation, change classification, audit logging |
| `org_gbrain_adapter.py` | `~/.hermes/scripts/` | Routes diffs to gbrain: slug resolution, page-type estimation, subagent prompt generation |

## Test Suite

**87 tests** at `~/.hermes/scripts/tests/`:
- `test_org_change_hook.py` (44 tests)
- `test_org_gbrain_adapter.py` (43 tests)

Run: `bash ~/.hermes/scripts/tests/run_tests.sh`

## How It Works

1. `org_query.py --create-todo` runs → hook captures **pre-state** (parses target file headings)
2. Write executes → file is modified
3. Hook captures **post-state** → computes **structured diff** (new headings, removed, metadata changes, state transitions)
4. **Classifier** determines: structural (new STORY/EPIC, GOAL/VALUE/POINTS changes) vs routine (state flips, inbox TODOs)
5. Audit entry written to `~/.hermes/scripts/gbrain_update_log.jsonl`

## Classification Rules

| Change | merits_gbrain | Classification |
|--------|---------------|---------------|
| New STORY created | True | structural |
| New EPIC created | True | structural |
| GOAL property changed | True | structural |
| VALUE property changed | True | structural |
| POINTS property changed | True | structural |
| TYPE property changed | True | structural |
| Heading removed | True | structural |
| State transition (TODO→DONE) | False | routine |
| New TODO in inbox | False | routine |
| SPRINT number change | False | routine |

## Reading the Audit Log

```bash
# Show recent entries
python3 ~/.hermes/scripts/org_change_hook.py --log

# Show N entries
python3 ~/.hermes/scripts/org_change_hook.py --log --log-limit 5
```

The log file is at `~/.hermes/scripts/gbrain_update_log.jsonl` — JSONL format, one entry per line.

## Interpreting `_gbrain_hook` Output

When `org_query.py` succeeds, the JSON response includes a `_gbrain_hook` key:

```json
{
  "_gbrain_hook": {
    "merits_gbrain": true,
    "decision_count": 1,
    "classification": "structural",
    "reason": "New STORY created",
    "decisions": [
      {
        "entity": "New Feature Story",
        "action": "search_first",
        "slug": "projects/new-feature-story",
        "reason": "New STORY created"
      }
    ],
    "audit_logged": true
  }
}
```

- `merits_gbrain`: True if the change was structural and needs gbrain attention
- `decisions`: List of suggested actions (search_first means: check gbrain for existing page first, then create/update)
- `audit_logged`: True if the entry was written to the audit log

## Cron Job

The `org-hook-habits-checks` cron (ID: `2cd25a27b8c3`) runs at 10 AM and 10 PM daily.
It reads the audit log and reports pending structural changes that need gbrain updates.
It does NOT take action — gbrain writes require user context.
See gbrain [[concepts/org-hook-habits-cron]] for details.

## Related gbrain Pages

- [[concepts/deterministic-org-changes]] — parent architecture
- [[concepts/org-hook-habits-cron]] — cron job operational details
