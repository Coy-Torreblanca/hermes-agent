> **This is a reference file loaded via `skill_view()`.** Friction concepts apply to all gbrain MCP operations — report issues via `mcp_gbrain_log_ingest` or direct operator notification.

# Friction Protocol — Convention

> Cross-cutting rule shared by skills the claw-test harness exercises (setup,
> brain-ops, query, ingest, smoke-test, migrations).

When you encounter friction interacting with gbrain — anything confusing, missing,
surprising, or wrong — log it so maintainers can see it without you writing a bug
report. Friction reports drive the claw-test feedback loop (the harness collects,
renders, and re-runs).

## When to Log

Log friction when any of these happens:

- An operation failed with a non-actionable error message
- A doc said one thing and the tool did another
- You couldn't find the next step
- A setup step needed a manual workaround
- A parameter exists but isn't documented
- A success condition was unclear (you couldn't tell if the operation worked)

Log delight (positive signal) when:

- Something worked on the first try and the docs were exactly right
- An error message handed you the fix
- A parameter you guessed at turned out to exist with the obvious name

## Severity Guide

| severity   | meaning |
|------------|---------|
| `blocker`  | Couldn't proceed at all. Hard stop. |
| `error`    | Operation failed unexpectedly. |
| `confused` | Docs/tool mismatch, ambiguity, missing pointer. |
| `nit`      | Polish opportunity. Cosmetic or low-impact. |

Be specific: "doctor says `schema_version=0` and points at apply-migrations, but
apply-migrations exits with no output" beats "doctor was confusing."

## How to Log

Log friction as a timeline entry on the brain's friction page:

```
mcp_gbrain_add_timeline_entry(
    slug="wiki/friction-log",
    date="YYYY-MM-DD",
    summary="<severity>: <one-line-what-happened>",
    detail="Phase: <which-operation>. Hint: <what-could-be-better>."
)
```

If the friction page doesn't exist yet, create it first via `mcp_gbrain_put_page`:

```
slug: wiki/friction-log
type: log
title: Friction Log
---
# Friction Log

## Timeline
```

Then append timeline entries as friction occurs.

Alternatively, use `mcp_gbrain_log_ingest` to record friction as an ingestion event with `source_type: "friction"`.
