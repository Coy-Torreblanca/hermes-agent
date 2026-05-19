# Habits.org Format & Workflow

Habits live in `/data/syncthing/Sync/org/personal/habits.org`. They differ from regular
todos: they have a `SCHEDULED` line with a recurrence repeater and `:STYLE: habit`.

## Entry Format

```
* TODO 📖 Title — context
  SCHEDULED: <YYYY-MM-DD Day +recurrence>
  :PROPERTIES:
  :STYLE:    habit
  :END:

  Body text. What, why, when. Enough context to remember months later.
```

## Recurrence Patterns

| Pattern | Repeater | Example |
|---------|----------|---------|
| Daily | `+1d` | `SCHEDULED: <2026-05-10 Sun +1d>` |
| Weekly | `+1w` | `SCHEDULED: <2026-05-16 Sat +1w>` |
| Monthly (same day-of-month) | `+1m` | `SCHEDULED: <2026-06-02 Tue +1m>` |

First occurrence should be the next upcoming date, not today if today already passed.

## Determining the Right Day

- **Sunday prep → Saturday** (day before 9:15 AM service)
- **Bible study prep → Friday** (prep for the week's daily 5 AM study blocks)
- **Monthly on specific date → that date** (e.g., rent reminder on 2nd)
- **When unsure**, use Saturday as a safe weekly prep day and note it for Coy to adjust

## Move-to-Habits Workflow

When Coy says "move this to habits" or "set this up in org habits":

1. **Find the entry** in the source file (usually `personal.org`)
2. **Read habits.org** to see existing format and pick consistent style
3. **Determine recurrence** — read the GOAL/body for clues about frequency and day
4. **Mark original as DONE** in source file (patch `** TODO` → `** DONE`)
5. **Append as habit** to habits.org with `SCHEDULED`, `:STYLE: habit`, and body text
6. **Preserve context** — body should explain what/why/when, not just a bare headline
7. **Use emoji** for visual scanability — match existing habits' style (📖, 🙏, 💸)

## Toggling Habits (`--toggle` Behavior)

When you run `habit_query.py <file> --toggle "Title"`, the script:

1. **Inserts a state log entry** after `:END:`:
   - Uses **3-space indent**: `   - State "DONE" from "TODO" [2026-05-18 Mon 12:01]`
   - Do NOT use 2-space indent — that mismatches the existing org-mode convention

2. **Advances the SCHEDULED date** according to the repeater pattern:

   | Repeater | Advancement | Example |
   |----------|-------------|---------|
   | `+1d` | +1 day from today | Toggle Mon → SCHEDULED Tue |
   | `.+1d/2d` | +1 weekday (skips Sat/Sun) | Toggle Fri → SCHEDULED Mon |
   | `+1w` / `++2w/21d` | +7 days from today | Toggle May 18 → SCHEDULED May 25 |
   | `+2w` | +14 days from today | Toggle May 18 → SCHEDULED Jun 1 |
   | `+1m` | +1 month from today (same day-of-month) | Toggle May 18 → SCHEDULED Jun 18 |

3. **Updates `:LAST_REPEAT:`** to today's toggle timestamp.

All existing state entries, properties, and body text are preserved.

**Bug fix 2026-05-18:** Originally `toggle_habit()` only inserted a log entry and never advanced the SCHEDULED date, causing the habit to stay overdue. It also used 2-space indent instead of 3, misaligning with existing entries. Both fixed. See `habit_query.py` `toggle_habit()` function.

## Dual Setup: Habits + Google Tasks for Timed Reminders

When a habit has a **specific time-of-day alert** (e.g., "remind me at 4 PM on the 2nd"),
set it up in BOTH systems:

| System | Purpose | How |
|--------|---------|-----|
| **Google Tasks** | Alerting via hourly coach | Create task with `RECURRING: monthly|weekly` in `notes`. Due date = first occurrence. Time goes in `notes`. |
| **Org habits** (`habits.org`) | Orgzly Revived tracking on phone | `SCHEDULED: <DATE Day +recurrence>` with `:STYLE: habit` |

**Example — rent reminder on 2nd at 4 PM:**
- Google Tasks: title `"💸 Pay rent"`, due `2026-06-02`, notes `"RECURRING: monthly | Rent due 1st — pay by 2nd. 4 PM."`
- Org habits: `SCHEDULED: <2026-06-02 Tue +1m>`, `:STYLE: habit`

**The hourly coach** surfaces the Google Tasks reminder when due; **Orgzly** tracks the habit
for Coy's daily review. Both advance on their own (coach advances overdue recurring tasks,
Orgzly advances SCHEDULED +repeater).

## Pitfalls

- **Don't use `:ID:` for habits** — Orgzly habit tracking uses `:LAST_REPEAT:`, not IDs.
  Exception: if Coy explicitly provides an ID, use it (as with rent reminder E463...).
- **SCHEDULED day-of-week must be correct** — a `+1w` from a wrong day creates drift.
  Use `cal` or `date` to verify.
- **Don't strip body context** — the habit's purpose must survive Coy forgetting why he set it up.
- **State lines use exactly 3-space indent** — always `   - State "DONE"`. The old buggy code produced `  - State` (2 spaces) which misaligned with existing entries in the file. Confirmed fixed in all test fixtures and the toggle_habit() function.
- **SCHEDULED date auto-advances on toggle** — `--toggle` now advances the SCHEDULED date per the repeater pattern. Previously it did NOT advance, so the habit stayed on its old date and appeared overdue. If you see a habit that keeps showing as overdue after toggling, verify it was toggled with the fixed `habit_query.py` (post 2026-05-18).
