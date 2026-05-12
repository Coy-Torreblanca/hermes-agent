# Google Tasks CLI Reference (absorbed from google-tasks skill)

Thin CLI wrapper for quick Google Tasks operations. All substantive context (API quirks, pitfalls, recurring-task workarounds, the hourly coach architecture) lives in the parent `reminder-db` skill. Use this file only as a CLI syntax quick-reference.

## Prerequisites

Google Workspace OAuth must already be set up (token at `~/.hermes/google_token.json`).

Verify auth:
```bash
python3 skills/productivity/google-workspace/scripts/setup.py --check
```

## Commands

All commands use the wrapper script. Define a shorthand:

```bash
GTASKS="python3 skills/productivity/google-workspace/scripts/tasks_api.py"
```

### List task lists
```bash
$GTASKS lists
```

### List tasks (in default list)
```bash
$GTASKS list
# Or specific list:
$GTASKS list --list LIST_ID --max 50
```

### Create a task
```bash
$GTASKS create --list LIST_ID --title "Task title" --due YYYY-MM-DD --time HH:MM --notes "Optional notes"
```

### Update a task
```bash
$GTASKS update TASK_ID --list LIST_ID --title "New title" --due YYYY-MM-DD --time HH:MM --notes "Updated notes"
```

### Coy's default task list
```
MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow  (title: "coydiego's list")
```

## Quick reference

```bash
python3 skills/productivity/google-workspace/scripts/tasks_api.py create \
  --list MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow \
  --title "TASK TITLE" \
  --due YYYY-MM-DD \
  --time HH:MM \
  --notes "Optional notes"
```

- `--time` format: `HH:MM` (24-hour). Override with `--tz`.
- Google Tasks has no native recurrence. Recreate manually or pair with a recurring Hermes cron job.
- All commands return JSON.
