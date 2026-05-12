---
name: reminder-db
description: "TIME-BASED alerts only. For todos/tasks without a specific alert time, use coy-sprint → org-mode inbox. This skill IS for: 'remind me at 9 AM', 'ping me tomorrow at 4 AM'. NOT for: 'create a todo', 'add to my list'."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [reminder, postgres, alerting, reliability]
---

# Reminders — Google Tasks Backend (May 6, 2026)

> **Consolidated May 2026:** The thin `google-tasks` skill (CLI wrapper reference) has been archived. Its CLI syntax quick-reference is preserved in `references/google-tasks-cli-reference.md`. This skill is now the single authoritative skill for all Google Tasks operations — time-based reminders, recurring workarounds, the hourly coach architecture, and all API pitfalls.

**CRITICAL DISTINCTION:** This is for time-triggered alerts. If Coy says "create a todo" or "add to my list" or "I need to remember to..." without specifying a time → use **org-mode inbox** (`/data/syncthing/Sync/org/inbox.org`) via the `coy-sprint` skill. Only use Google Tasks when Coy says "remind me at X time" or "ping me when..." or gives a specific due time.

**Backend:** Google Tasks API (account: coydiego@gmail.com). Replaced Postgres `hermes.reminders` on May 6, 2026 — all reminders now live in Coy's Google Tasks alongside his manually-created tasks. Single source of truth.

**Alerting:** No native Google Tasks alerts. The **Hourly Check-in Coach** cron (`39a44a1b7ac2`) checks Google Tasks for due/overdue items every hour and surfaces them to Coy via Discord (`#coach`). Less granular than the old 5-minute poller, but zero infrastructure cost.

**Support files:**
- `references/runtime.md` — legacy reference (Postgres-based, deprecated)
- `references/os-cron-architecture.md` — legacy reference (deprecated)

## Schema (Google Tasks)

**Task List ID:** `MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow` ("coydiego's list")

**Task fields used:**

| Field | Type | Purpose |
|-------|------|---------|
| `title` | string | What to remind/do |
| `due` | RFC 3339 | When it's due |
| `notes` | string | Context, recurrence rules, source |
| `status` | string | `needsAction` (active) or `completed` (done) |

**Recurrence workaround:** Google Tasks API doesn't support `RRULE`. For recurring reminders, include `RECURRING: daily|weekly` in the `notes` field. The hourly coach detects overdue recurring tasks and advances their due date.

**Lifecycle:**
```
needsAction ──(Coy:"done")──→ completed (via tasks().patch with status='completed')
     │
     └──(Coy:"push to X")──→ tasks().patch with new due date
     │
     └──(Recurring advance)──→ tasks().update with full body (PUT)
```

## Commands

All operations use Google Tasks API via Python. Task list ID: `MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow`

### Create a reminder

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

creds = Credentials.from_authorized_user_file(os.path.expanduser("~/.hermes/google_token.json"))
svc = build("tasks", "v1", credentials=creds)
LIST_ID = "MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow"

task = {
    "title": "Ask Melody about the Airbnb",
    "due": "2026-05-06T09:00:00-05:00",
    "notes": "Mexico trip preparation | source: telegram",
}
created = svc.tasks().insert(tasklist=LIST_ID, body=task).execute()
print(f"Created: {created['id']}")
```

### Mark done

```python
# Use patch() for partial updates — update() requires the full resource body (PUT semantics)
svc.tasks().patch(tasklist=LIST_ID, task=TASK_ID, body={"status": "completed"}).execute()
```

### Push to a different time

```python
# Use patch() for partial updates — update() requires the full resource body
svc.tasks().patch(tasklist=LIST_ID, task=TASK_ID, body={
    "due": "2026-05-07T15:00:00-05:00"
}).execute()
```

### Advance a recurring task (full body via update)

```python
# update() = PUT semantics — must include ALL fields including id
# Used here because we're copying the full task with a new due date
svc.tasks().update(tasklist=LIST_ID, task=TASK_ID, body={
    "id": TASK_ID,
    "title": "🛌 Wind down for bed — lights out by 8:45 PM",
    "notes": "RECURRING: daily | 4 AM wake target",
    "status": "needsAction",
    "due": "2026-05-07T20:45:00-05:00"
}).execute()
```

### List all active tasks

```python
tasks = svc.tasks().list(tasklist=LIST_ID, showCompleted=False).execute()
for t in tasks.get("items", []):
    print(f"{t['title']} — due {t.get('due', 'none')}")
```

**Change default re-alert window:** Edit the `INTERVAL '30 minutes'` in `reminder_poll.py`.

## Reusable Scripts

| Script | Purpose |
|--------|---------|
| `scripts/check_google_tasks_and_calendar.py` | One-shot probe: lists today's calendar events + all `needsAction` Google Tasks. Used by hourly coach, daily briefings, and any cron job. Outputs `CAL\|` and `TASK\|` prefixed lines for easy parsing. |
| `scripts/poll_reminders.py` | Legacy Postgres poller — deprecated (kept for reference). |
| `scripts/reminder_poll.py` | Legacy Postgres poller — deprecated (kept for reference). |

## Adding a Reminder

When Coy says "remind me to X at Y time" or "remind me tomorrow to Z", create a task via Google Tasks API.

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

creds = Credentials.from_authorized_user_file(os.path.expanduser("~/.hermes/google_token.json"))
svc = build("tasks", "v1", credentials=creds)
LIST_ID = "MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow"

task = {
    "title": "Ask Melody about the Airbnb",
    "due": "2026-05-06T09:00:00-05:00",
    "notes": "Mexico trip preparation | source: telegram",
}
created = svc.tasks().insert(tasklist=LIST_ID, body=task).execute()
print(f"Created task: {created['id']}")
```

### Recurring reminders

Google Tasks API has no recurrence. Workaround: put `RECURRING: daily|weekly|monthly` in the `notes` field. The hourly coach detects overdue recurring tasks and advances their due date.

```python
task["notes"] = "RECURRING: weekly | Clean bathrooms"
```

### Midnight Rule

When Coy says "tomorrow" at or after midnight (12 AM), he means later that same calendar day after sleeping. Resolve relative to the day-after-waking.

## Alerting (Hourly Coach)

The **Hourly Check-in Coach** cron (`39a44a1b7ac2`) checks Google Tasks every hour for due/overdue items and surfaces them. No separate 5-minute poller — Google Tasks is the single source of truth.

**Architecture:**
```
Every hour (4 AM–9 PM)
  → Hourly coach runs
    → Lists all needsAction tasks from Google Tasks
    → Flags due-today and overdue items
    → Presents alongside calendar + org status
    → Delivers to Discord (#coach)
```


## Pitfalls

1. **Midnight rule:** When Coy says "tomorrow" at/after midnight, he means the same calendar day after sleeping.
2. **Recurring tasks:** Google Tasks has no native recurrence. Include `RECURRING: daily|weekly` in notes. The hourly coach handles advancing due dates.
3. **Task list ID hardcoded:** `MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow` — if Coy creates a new list, this must be updated.
4. **Google token must be valid:** If `NOT_AUTHENTICATED`, re-run Google Workspace setup.
5. **`update()` vs `patch()` — critical distinction:** Google Tasks API has two methods. `tasks().patch(tasklist, task, body)` supports partial field updates (PATCH semantics) — use for marking done, pushing time, or changing any subset of fields. `tasks().update(tasklist, task, body)` is PUT — it **requires the full resource** including `id`, `title`, `notes`, `status`, `due`. Using update() with a partial body causes `HttpError 400: Missing task ID`. Discovered May 6, 2026: recurring wind-down task advancement failed because update() was called with only `{"due": ...}`.
