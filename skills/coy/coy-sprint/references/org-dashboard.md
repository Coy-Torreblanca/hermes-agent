# Org Dashboard (absorbed from org-dashboard skill)

Read-only view of Coy's sprint state. Mirrors `C-c a n` in Emacs — the Now vs. Next Dashboard.

## When to Use

- Coy says "what am I working on?", "sprint status", "what's next?", "dashboard"
- Morning briefing, hourly check-in, or any time Coy needs situational awareness
- Before starting new work — surface what's already in flight

## Dashboard Zones

### 🔥 WORKING ON NOW
- Filter: tasks in `STARTED` or `STORY-STARTED` state
- Should be exactly 1. More = multitasking.

### ⏭️ UP NEXT
- Filter: tasks in `NEXT` or `STORY-NEXT` state
- "Ready for Dev" queue. Already pointed, valued, sprinted.

### 🏃 CURRENT SPRINT LOAD
- Filter: tasks with `SPRINT=<current>` excluding STARTED/NEXT
- Remaining sprint commitment. Shows points per item.

### 📊 VELOCITY
- Completed points this sprint (DONE tasks with current SPRINT)
- Points remaining in sprint load
- Capacity: /16 max

## Work-Hours Context Filtering

| Window | Mode | What to surface |
|--------|------|-----------------|
| Mon–Fri, 8 AM – 3 PM | 💼 WORK | `/data/syncthing/Sync/org/work/tasks.org` only |
| Before 8 AM, after 3 PM, weekends | 🏠 FULL | tasks.org + `/data/syncthing/Sync/org/personal/personal.org` |

In WORK MODE skip personal.org items unless they have a deadline during work hours.

## Implementation

1. Determine current sprint number (check `/data/syncthing/Sync/org/work/tasks.org` for most common SPRINT value on active items)
2. `search_files` for `STARTED`, `STORY-STARTED`, `NEXT`, `STORY-NEXT` across `/data/syncthing/Sync/org/work/tasks.org` (and `/data/syncthing/Sync/org/personal/personal.org` in FULL MODE)
3. For each match, `read_file` surrounding lines to extract: heading, priority, points, value, tags, body
4. Count DONE items with current SPRINT for velocity
5. Present the four zones

**Active task search pattern:** Search for `STARTED|STORY-STARTED|NEXT|STORY-NEXT` without line anchoring — `search_files` regex with `^` can miss indented items under EPICs. Use `search_files(pattern="STARTED", target="content", path="...")` and read surrounding lines.

## Output Format

```
🔥 WORKING ON NOW:
  ** STORY-STARTED [#A] Build auth service  :backend:
     POINTS: 5 | VALUE: Critical | SPRINT: 4

⏭️ UP NEXT:
  ** STORY [#B] Add rate limiting  :infra:
     POINTS: 3 | VALUE: High | SPRINT: 4

🏃 SPRINT 4 LOAD (8/16 pts remaining):
  ** TODO Implement health checks  (2 pts)
  ** STORY Migrate database  :data: (3 pts)
  ** TODO Write API docs  (1 pt)

📊 VELOCITY: 5/16 pts completed this sprint (3 remaining)
```

## Rules

1. **Read-only** — this skill never modifies org files
2. **Single WIP check** — flag if >1 STARTED task exists
3. **Empty NEXT queue** — if NEXT is empty and STARTED is done, suggest promoting from sprint load
4. **Capacity warning** — flag if committed points exceed 16
5. **Timezone** — determine work/full mode using local time, not system time

## Pitfalls

- **Anchored regex misses indented items** — `^** STORY-STARTED` won't match `** STORY-STARTED` under an EPIC. Search for the keyword without anchoring.
- **STALE sprints** — if no tasks have the current sprint number in `/data/syncthing/Sync/org/work/tasks.org`, check if sprint roll-over happened
- **Personal.org items during work hours** — suppress `/data/syncthing/Sync/org/personal/personal.org` items unless deadline-tagged and due during work window
