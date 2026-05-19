# Org Sprint Plan (absorbed from org-sprint-plan skill)

Plan sprints, check capacity, track velocity, and roll over unfinished work. Mirrors Column View (`C-c C-x C-c`) and `M-x my/org-end-of-sprint-cleanup` in Emacs.

## When to Use

- Coy says "sprint planning", "plan next sprint", "roll over sprint", "what's my velocity?"
- Start of sprint — pull from backlog into sprint commitment
- End of sprint — roll unfinished work forward
- Mid-sprint — capacity check before committing new items

## Operations

### 1. Sprint Planning (beginning of sprint)

**Sprint boundaries:** Sprint start = last LOGBOOK DONE timestamp of Bi-Weekly Sprint Cleanup habit. Sprint end = SCHEDULED date of that habit. See gbrain [[concepts/sprint-date-derivation]].

- Current sprint (Sprint 4): `2026-04-11` → `2026-05-30`
- Derivation: `habit_query.py /data/syncthing/Sync/org/work/sprint_habits.org --list` → find "Bi-Weekly Sprint Cleanup" → scheduled + last LOGBOOK timestamp

**Read the landscape:**
- Current sprint number from `/data/syncthing/Sync/org/work/tasks.org`
- All backlog items (SPRINT: backlog or no SPRINT) in tasks.org
- All backlog items in `/data/syncthing/Sync/org/personal/personal.org` (FULL MODE)

**Propose sprint composition:**
- Sort backlog by VALUE (Critical → High → Medium → Low)
- Propose items up to 16 pts capacity
- Present as a ranked list with points and value

```
📋 PROPOSED SPRINT 5 (capacity: 16 pts):
  [#A] STORY Build auth service      5 pts  Critical
  [#B] STORY Add rate limiting        3 pts  High
  [#B] TODO Implement health checks   2 pts  Medium
  [#B] STORY Migrate database         3 pts  High
  [#C] TODO Write API docs            1 pt   Low
  ─────────────────────────────────────────
  TOTAL: 14/16 pts (2 pts buffer)
```

**Coy confirms or adjusts, then:**
- Set SPRINT property on confirmed items to current sprint number

### 2. Sprint Roll-Over (fortnightly)

**Find unfinished work:**
- All tasks in tasks.org and personal.org with SPRINT = current but NOT DONE/CANCELLED

**Roll forward:**
- Increment SPRINT by 1 on each unfinished task
- Completed (DONE) tasks stay in their original sprint for velocity history

**Update sprint number:**
- Coy manually updates `my/current-sprint` in Emacs config — Hermes can't do this
- Remind Coy: edit `~/.emacs.d/lisp/org-config.el`, change `(defvar my/current-sprint "4" ...)` → `"5"`, restart Emacs

### 3. Capacity Check (mid-sprint)

**Count committed points:**
- Sum POINTS on all tasks with SPRINT = current (excluding DONE/CANCELLED)
- Compare to 16 max

### 4. Velocity Report

**Per-sprint velocity:**
- Count DONE tasks per sprint number
- Sum completed points per sprint

## File Paths

| File | Purpose |
|------|---------|
| `/data/syncthing/Sync/org/work/tasks.org` | Work sprint items |
| `/data/syncthing/Sync/org/personal/personal.org` | Personal sprint items |
| `/data/syncthing/Sync/org/personal/habits.org` | Recurring habits (not sprinted) |

## Rules

1. **16 pt capacity hard limit** — warn if proposed sprint exceeds, require Coy approval to override
2. **Roll-over is fortnightly** — every 2 weeks per `sprint_habits.org`
3. **Never change SPRINT on DONE items** — they stay in their original sprint for velocity history
4. **Backlog items have no SPRINT or SPRINT: backlog** — only set SPRINT when pulling into a sprint
5. **Emacs config update is manual** — Hermes can't edit org-config.el. Remind Coy.
6. **Velocity is per-sprint** — don't mix work and personal points in the same velocity number

## Implementation

**Parse backlog (script):** `python3 skills/coy/coy-sprint/scripts/parse_backlog.py` — returns backlog items sorted by VALUE then POINTS. Options: `--max-points 16`, `--value-only Critical`, `--file <path>`.

**Property changes** use `patch`: `old: :SPRINT:    backlog` → `new: :SPRINT:    5`

## Pitfalls

- **Sprint number drift** — verify current sprint by checking most common SPRINT value on active (not DONE) tasks
- **Don't sprint habits** — items in habits.org use SCHEDULED repeat, not SPRINT
- **Personal sprint items** — only count personal points separately from work points
- **Roll-over requires Emacs restart** — Coy has to do this manually, don't forget to remind him
