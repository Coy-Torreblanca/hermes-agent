# Org State (absorbed from org-state skill)

Transition tasks between states. Mirrors `t` (rotate state) in Emacs agenda — with guards and context.

## When to Use

- Coy says "start X", "done with X", "cancel X", "promote X", "unblock X", "X is waiting on Y"
- After a task is finished — auto-suggests what's next
- NOT for triage (use `references/org-triage.md`), NOT for dashboard (use `references/org-dashboard.md`)

## State Machine

### Work Tasks
```
TODO ──→ NEXT ──→ STARTED ──→ DONE
  │                 │
  └──→ CANCELLED    └──→ WAITING ──→ STARTED
```

### Work Stories
```
STORY ──→ STORY-NEXT ──→ STORY-STARTED ──→ STORY-DONE
  │                        │
  └──→ CANCELLED           └──→ STORY-WAITING ──→ STORY-STARTED
```

### Personal
```
TODO ──→ STORY ──→ STORY-NEXT ──→ STORY-STARTED ──→ DONE
                    │               │
                    │               └──→ STORY-WAITING ──→ STORY-STARTED
                    │               └──→ WAITING ──→ TODO
                    └──→ CANCELLED
```

## Operations

| Coy says | Transition | Guard |
|----------|-----------|-------|
| "start X" | NEXT → STARTED | Warn if another STARTED exists; let Coy decide |
| "done with X" | STARTED → DONE | Timestamp + context note |
| "cancel X" | any → CANCELLED | Require reason note |
| "promote X" | TODO → NEXT | Must be in current sprint |
| "X is blocked/waiting on Y" | STARTED → WAITING | Require what/whom it's waiting on |
| "unblock X" | WAITING → STARTED | Clear blocker note |

## Status Note (every transition)

Every state change gets a context note with local time:

```
- State "DONE" from "STARTED" [2026-05-09 Sat 05:30 PDT]
  Built auth middleware, tests passing. Deployed to staging.
```

- **Local time** — use system time
- **Context** — what was accomplished, why cancelled, what it's waiting on
- **For WAITING**: note what it's waiting on (e.g., "Waiting on Sean to approve logging policy.")

## After DONE

1. Timestamp + context note
2. Check if all children of parent STORY are DONE → flag "Parent STORY is ready to close"
3. If NEXT queue is empty → scan sprint load by VALUE, suggest next promotion

## Implementation

Use `patch` for state changes — find the heading line + properties drawer, replace the state keyword and append the log note.

**Pattern for state keyword change:**
```
old: ** STORY-NEXT [#A] Task title
new: ** STORY-STARTED [#A] Task title
```

**Pattern for appending status note after properties drawer:**
Find `:END:` of the properties drawer, append the note after it.

## Rules

1. **Single WIP: warn, don't block** — flag if another STARTED exists, let Coy decide
2. **Sprint gate for promotion** — TODO → NEXT only if task has current SPRINT
3. **Parent closure: flag, don't auto-close** — when all children DONE, note the parent is ready
4. **Always add a status note** — bare state changes without context are lost history
5. **Local time in timestamps** — use system time.
6. **Never delete tasks** — CANCELLED preserves history
7. **CANCELLED requires reason** — block if no reason given

## Bulk Property Updates (Sprint Roll-over, Mass Promotion)

When updating SPRINT (or any property) on multiple stories at once — e.g., moving an EPIC + all its children between sprints — use `execute_code` with batched `patch()` calls rather than individual patch invocations:

```python
from hermes_tools import patch

# Move EPIC to new sprint
patch(path="...", old_string="""* EPIC Name...
:SPRINT:   4""", new_string="""...:SPRINT:   backlog""")

# Move child stories
patch(path="...", old_string="""** STORY Child 1...
:SPRINT:   4""", new_string="""...:SPRINT:   backlog""")
```

**Why:** Individual patch calls each require a full tool round-trip. 10+ stories = 10+ turns. `execute_code` runs all patches in a single turn. The `old_string` must include enough surrounding context (heading line + properties drawer opening) to be unique.

**Verification:** After bulk changes, grep to confirm:
```bash
grep -n 'SPRINT:' tasks.org | grep -E ':\s*4$'
```

## Pitfalls

- **Bulk property updates: match full context** — when using `patch()` inside `execute_code`, the `old_string` anchor must uniquely match ONE location. Include the heading line + first few properties. A bare `:SPRINT:   4` will match dozens of places.
- **Matching the right heading** — tasks can have similar names. Match by ID property when available, or by full heading text.
- **Properties drawer absent** — some bare TODOs may lack a properties drawer. Append status note after the body text instead.
- **Timezone drift** — always check where Coy is before timestamping. Journal has current location.
- **Not for triage** — this skill modifies state on already-placed tasks. New captures → `references/org-capture.md`, refiling → `references/org-triage.md`.
