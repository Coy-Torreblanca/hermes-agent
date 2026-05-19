---
name: coy-sprint
description: "Manage Coy's sprint system — work tasks, personal board, capacity checks, velocity tracking. Todo CRUD (create/read/update/cancel), inbox capture, sprint dashboard. Reads/writes tasks.org and personal.org. TRIGGER: load this skill whenever Coy says anything about todos, tasks, sprints, inbox, work items, or 'what do I have going on'."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [sprint, org-mode, task-management, velocity, todo, inbox, tasks]
---

# Coy's Sprint Management System — Todo Operations

> **⚠️ SOURCE OF TRUTH: The Emacs configuration is authoritative.** Before modifying org files or relying on any value schema, check `/data/syncthing/Sync/org/emacs_config/` (see `references/emacs-config-reference.md`). The actual `.el` config files in `emacs_config/lisp/` define what Emacs does. Markdown summaries may be outdated.

Manage tasks in `/data/syncthing/Sync/org/work/tasks.org` following the Agent Management Protocol embedded in that file. This skill enforces all 10 non-negotiable rules.

## Sub-Operation References

Load the relevant reference via `read_file` before any org operation:

| Operation | Reference File | Trigger |
|-----------|---------------|---------|
| Capture TODO to inbox | `references/org-capture.md` | "add a todo", "add to my list" |
| Triage inbox → refile + metadata | `references/org-triage.md` | "triage my inbox", "refile these" |
| Read sprint dashboard | `references/org-dashboard.md` | "what am I working on?", "dashboard" |
| Change task states | `references/org-state.md` | "start X", "done with X", "cancel X" |
| Sprint planning + roll-over | `references/org-sprint-plan.md` | "sprint planning", "roll over sprint" |
| Manage shopping list | `references/shopping-list.md` | "add to shopping list", "what's on my shopping list" |
| Article → icebox stories + gbrain | `references/article-analysis-workflow.md` | "analyze this article", "create stories for this" |
| Bulk EPIC reparenting | `references/org-bulk-reparenting.md` | "move items between EPICs", "reparent backlog" |
| Sprint retro + stale detection | `references/org-retro-and-stale.md` | "run sprint retro", "stale backlog" |
| Body text → org children | `references/org-body-to-children.md` | "convert these to todos", "break this into subtasks" |
| Org change hook + gbrain audit | `references/org-change-hook.md` | "gbrain hook", "org_change_hook output", "_gbrain_hook", "check audit log" |

**Rule:** Before any org file operation, load the relevant reference file via `read_file`.

## When to Use

- User asks about sprint status, task states, or what to work on
- User asks about personal items, personal board, or "what about my personal items?"
- User wants to start, finish, cancel, or reprioritize tasks (work or personal)
- User wants to plan a new sprint or add stories
- User asks "what's next?" or "what should I work on?"
- User mentions any task by name from their backlog
- User asks about EPIC reorganization, moving items between projects, or bulk reparenting
- User says "create a plan" involving backlog/task management
- User asks for a reminder ("remind me tomorrow", "remind me about X") → delegate to `reminder-db` skill. This skill handles Todos, NOT time-based reminders.

**Defer to journaling when Coy is sharing life content.** Capture action items after he's done sharing, don't interrupt narrative flow by jumping to task extraction. The `coy-journal` skill governs significance detection.

## Canonical Org Files

```
/data/syncthing/Sync/org/work/tasks.org        ← Work tasks (edit this)
/data/syncthing/Sync/org/inbox.org              ← Inbox captures
/data/syncthing/Sync/org/personal/personal.org   ← Personal tasks
/data/syncthing/Sync/org/work/sprint_habits.org  ← Sprint maintenance habits
/data/syncthing/Sync/org/personal/shopping.org  ← Running Amazon shopping list
```

## State Machine

```
TODO → NEXT → STARTED → DONE
  ↓
CANCELLED (with note — never delete)
```

Story variants: STORY (backlog), STORY-NEXT, STORY-STARTED
Epic: EPIC (always backlog, no sprint state)

## Rules (enforced — do not break)

1. **SINGLE WIP**: Only ONE STARTED task at a time. Finish or cancel before starting another.
2. **PULL QUEUE**: Promote TODO → NEXT → STARTED in order. Never skip states.
3. **CAPACITY**: Max 16 pts/sprint. Warn/block if committed exceeds.
4. **GOAL FILTER**: Every STORY/EPIC needs :GOAL:. Sub-tasks not serving GOAL → ICEBOX.
5. **HIERARCHY**: Parents can't close until children are DONE/CANCELLED.
6. **PROPERTY INHERITANCE**: TODOs don't get :VALUE: or :SPRINT: (inherit from parent STORY).
7. **TIMESTAMPS**: DONE records: `- State "DONE" from "STARTED" [YYYY-MM-DD Day HH:MM]`
8. **ICEBOX**: Non-GOAL ideas → `EPIC <name> [ICEBOX]`
9. **VELOCITY**: Track completed points per sprint. Current: ~16 pts/sprint.
10. **ROLL-OVER**: Unfinished sprint tasks get SPRINT incremented. Done tasks stay for history.

## Org Query Script (Canonical Parser)

**🚨 Canonical script at `~/.hermes/scripts/org_query.py`** — single source of truth. **ALWAYS use `org_query.py` instead of regex/grep/search_files for org file operations.**

**The org change hook is always active.** Every `--create-todo` call now runs a post-change hook that captures pre/post state, computes a structured diff, classifies the change (structural vs routine), and writes an audit entry to `~/.hermes/scripts/gbrain_update_log.jsonl`. See `references/org-change-hook.md` for full details. There is no env var to toggle — the hook is always on.

```bash
# Dashboard
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --summary [sprint_num]

# Active tasks
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --find-active

# Find insertion point under an EPIC
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --insert-point "30ai [ICEBOX]"

# Find an EPIC by name (partial match)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --find-epic "30ai"

# Sprint items
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --sprint "backlog"
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --sprint 4

# List all EPICs
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --epics

# Validate rules (WIP, orphans, missing points)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --validate

# Statistics
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --stats

# Children of a heading
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --children-of "Second Brain"

# Find a heading by title regex
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --heading "Four-Stage RAG"

# Deterministic create todo (appends to inbox.org)
python3 ~/.hermes/scripts/org_query.py \
  --create-todo '{"title":"Set up xurl CLI","body":"Install at /data/.hermes/skills/social-media/xurl/"}'

# Preview without writing
python3 ~/.hermes/scripts/org_query.py \
  --dry-run '{"title":"New Story","destination":"Personal AI v1","keyword":"STORY","points":3}'

# Sprint retro report
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --retro 4

# Backlog stale detection
cd /data/.hermes/skills/coy/coy-sprint && python3 scripts/parse_backlog.py --stale 2

# Read back a specific line (bypasses read_file dedup)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/inbox.org --verify-line 42
```

## Habits (`habit_query.py`)

**Script:** `~/.hermes/scripts/habit_query.py` — dedicated parser for habit structure (SCHEDULED repeaters, LOGBOOK state history, streaks). Separate from `org_query.py`; habits don't fit the EPIC/STORY/TODO hierarchy.

```bash
# List all habits with status and streak
python3 ~/.hermes/scripts/habit_query.py --list

# Show overdue habits
python3 ~/.hermes/scripts/habit_query.py --overdue

# Show habits due today
python3 ~/.hermes/scripts/habit_query.py --due-today

# Check streak for a habit
python3 ~/.hermes/scripts/habit_query.py --streak "Bible study"

# Mark a habit DONE for today (advances SCHEDULED)
python3 ~/.hermes/scripts/habit_query.py --toggle "Bible study"

# Reschedule a habit — change SCHEDULED date (preserves repeater)
python3 ~/.hermes/scripts/habit_query.py --reschedule "Bible study" 2026-06-01

# Add a new habit
python3 ~/.hermes/scripts/habit_query.py --add '{"title":"Morning Prayer","schedule":"+1d","body":"Daily morning prayer at 5 AM"}'
```

Defaults to `/data/syncthing/Sync/org/personal/habits.org`. Pass alternate file as first arg.

**🚨 For habit state changes, use `habit_query.py` — NOT `patch`.** It handles LOGBOOK entries, SCHEDULED advancement, and LAST_REPEAT in one command. Do not default to `patch`.

## Deterministic Create Todo (`--create-todo` API)

**Script:** `~/.hermes/scripts/org_query.py` (also `~/.hermes/bin/org_query`)

The primary write method for all new todos. Accepts JSON, generates a deterministic org-mode block, and writes it to the right file. **NEVER asks follow-up questions about priority, project, or location.**

### Output

Successful writes return JSON with `success`, `action`, `todo_id`, `params`, and a `_gbrain_hook` key containing the hook analysis. The `_gbrain_hook` field shows whether the change merits a gbrain update (merits_gbrain), how many entities were affected (decision_count), and recommendations (decisions). See `references/org-change-hook.md` for interpreting this output.

### Parameters

| Param | Type | Default | When Required |
|-------|------|---------|---------------|
| `title` | string | (required) | Always — extract from Coy's sentence |
| `body` | string | "" | When Coy gave context — pass through verbatim |
| `destination` | string | "inbox" | "inbox" for fast capture; EPIC name for direct insert |
| `priority` | string | omitted | A, B, or C — only if Coy specified it |
| `tags` | array | [] | e.g. `["bug","urgent"]` |
| `points` | int | omitted | ONLY for non-inbox destinations (stories under EPICs) |
| `value` | string | omitted | Only if explicitly provided. Never auto-derive from priority. |
| `sprint` | string | "backlog" | Override only if Coy explicitly says a sprint number |
| `goal` | string | omitted | Only if explicitly provided. See pitfalls for Coy-override rule. |
| `keyword` | string | "TODO" | "TODO" for inbox, "STORY" for stories under EPICs |
| `type` | string | None | "feature", "bugfix", "hotfix", "chore". Auto-generates BRANCH when set. |
| `repo` | string | None | Optional repo link (e.g. "github.com/owner/repo") |
| `branch` | string | None | Explicit branch override. Auto-generated as `type/slugged-title` if TYPE given. |

### Deterministic Property Order (never vary)

```
:PROPERTIES:
:ID:       <auto-gen UUID — 16 hex chars>
:CREATED:  [YYYY-MM-DD Day]
:SPRINT:   backlog
:POINTS:   <only if non-inbox>
:VALUE:    <only if non-inbox>
:GOAL:     <only if non-inbox>
:TYPE:     <feature|bugfix|hotfix|chore — only if provided>
:BRANCH:   <auto or explicit — only if TYPE provided>
:REPO:     <optional — only if provided>
:END:
```

### Auto-generation Rules

- `ID`: `uuid.uuid4().hex[:16].upper()` — matches Emacs `org-id-get-create` format
- `CREATED`: System date in `[YYYY-MM-DD Day]` format
- `POINTS`: Omitted for inbox capture (triage fills later)
- `VALUE`: **Only included if user explicitly provides it.** Never auto-derive from priority.
- `GOAL`: **Only included if user explicitly provides it.** See pitfalls for Coy-override.

### Inbox vs EPIC Behavior

- **Inbox destination:** Appends to end of inbox.org. POINTS/VALUE/GOAL omitted.
- **EPIC destination:** Uses `--insert-point` anchor to insert under the EPIC in tasks.org via raw Python file I/O (NOT `patch`). Includes POINTS/VALUE/GOAL.
- **🚨 EPIC destination does NOT remove from inbox.** After insertion, the item exists in both places. Manually remove the source inbox entry as a separate step.

### Usage Patterns

```bash
# Fast capture (title + body only)
python3 ~/.hermes/scripts/org_query.py \
  --create-todo '{"title":"Fix login bug","body":"Users getting 401 after password reset"}'

# With priority and tags
python3 ~/.hermes/scripts/org_query.py \
  --create-todo '{"title":"Add rate limiting","priority":"A","tags":["security"]}'

# Under an EPIC (pre-triaged, includes metadata)
python3 ~/.hermes/scripts/org_query.py \
  --create-todo '{"title":"Auth middleware","body":"JWT validation layer","destination":"Personal AI v1","keyword":"STORY","points":3,"value":"High"}'

# Preview without writing
python3 ~/.hermes/scripts/org_query.py \
  --dry-run '{"title":"Refactor router","destination":"Personal AI v1","keyword":"STORY"}'

# Post-write verification (bypasses read_file dedup)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/inbox.org --verify-line 10
```

## Read State

```bash
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --summary 4
```

Returns structured JSON with: `active_tasks` (STARTED), UP NEXT (NEXT), `sprint_items` (SPRINT LOAD with points), `points_completed` / `points_remaining` / `capacity_used_pct`.

## Capture a Todo to Inbox

1. **No reads** — don't read inbox.org first. This is capture, not review.
2. Use `org_query.py --create-todo` with title + body
3. Confirm briefly — "Done. Captured to inbox."
4. **Todo body quality:** Include enough context for understanding during later triage. For Hermes/skill-related todos: name the system, include the full skill path, list concrete steps. A bare headline without body is useless.

## Show Dashboard

```
🔥 WORKING ON NOW: <started tasks, should be exactly 1>
⏭️ UP NEXT: <next tasks>
🏃 SPRINT 4 LOAD: <sprint tasks not started/next, with points>
📊 VELOCITY: X/Y pts completed this sprint
```

## Start a Task

1. Verify no other STARTED task exists
2. Task must be in NEXT or TODO state with SPRINT=current
3. Change state to STARTED (or STORY-STARTED for stories)
4. Add timestamp note

## Complete a Task

1. Change state to DONE
2. Add: `- State "DONE" from "STARTED" [YYYY-MM-DD Day HH:MM]`
3. Mark sub-task checkboxes [X] if applicable
4. If NEXT queue is empty, suggest promoting from sprint backlog

## Cancel a Task

1. Change state to CANCELLED
2. Add note explaining why
3. Never delete the task

## Add to Sprint

1. Check capacity (existing sprint points + new task ≤ 16)
2. Set SPRINT property to current sprint number
3. Ensure GOAL property exists
4. If story, set VALUE and POINTS

## Sprint Roll-Over

1. Find all unfinished tasks with SPRINT=current
2. Increment SPRINT by 1
3. Update `my/current-sprint` in config files
4. Archive completed sprint data for velocity history

## Triage Inbox

**Before triaging:** Load `read_file /data/.hermes/skills/coy/coy-sprint/references/org-triage.md`.

1. Read `/data/syncthing/Sync/org/inbox.org`
2. For each uncategorized item: present the **full body text** alongside the headline. Strip nothing.
3. Propose POINTS, VALUE, SPRINT, destination file (tasks.org vs personal.org)
   - **🚨 Default SPRINT to backlog** unless urgent/time-critical or Coy explicitly requests current sprint. `[#A]` priority does not mean "sprint now."
4. **Present refile targets as actual org text** — the exact `* STORY` or `** TODO` block that would be written, with all properties. Don't use summary tables.
5. **Present as a proposal, wait for confirmation** — never push without Coy's approval
6. After approval, move items to destination file with full metadata. Use the Python heredoc pattern from `references/refile-script-pattern.md`.
7. **🚨 Clean up refiled items from inbox.** After all refiles, do a final inbox pass: read inbox.org, identify refiled items by heading title match, and remove them. `--create-todo destination:"<EPIC>"` does NOT auto-remove source inbox entries.
8. Clean up DONE items from inbox
9. Present the resulting dashboard

**Triage output format:**

```
→ tasks.org:
* STORY Name
:PROPERTIES:
:ID:       ...
:END:

→ Cleanup: (DONE items to remove)
```

**Do NOT use summary tables for refile proposals.** Present the exact org content. Coy needs to see the full text to evaluate metadata and GOAL.

## Sprint Boundaries (Date Derivation)

Sprint start/end are derived from the Bi-Weekly Sprint Cleanup habit — no manual tracking needed.

| Boundary | Source |
|----------|--------|
| **Sprint Start** | Habit's LOGBOOK: last `- State "DONE" from ...` timestamp |
| **Sprint End** | Habit's `SCHEDULED:` date |

```bash
python3 ~/.hermes/scripts/habit_query.py /data/syncthing/Sync/org/work/sprint_habits.org --list
# → Find "Bi-Weekly Sprint Cleanup" → scheduled date + last LOGBOOK timestamp
```

## Personal Board

When asked about personal items, also read and present:

```bash
read_file /data/syncthing/Sync/org/personal/personal.org
```

### Personal State Keywords

| State | Meaning |
|-------|---------|
| TODO | Backlog, not sprinted |
| STORY | Active story in sprint |
| STORY-NEXT | Ready to start |
| STORY-STARTED | In progress |
| STORY-DONE | Completed story |
| STORY-WAITING | Blocked externally |
| WAITING | Blocked on external input |
| DONE | Finished |

### Personal Dashboard Format

```
🔴 BLOCKED / WAITING: items in WAITING or STORY-WAITING (with blocker)
🟡 BACKLOG — Actionable Now: TODO/STORY items not blocked, ordered by value
⚠️ OVERDUE: items past their DEADLINE
```

### Delegation Pattern

When a personal task is delegated (e.g., "Dad is buying the flights"), mark DONE with note:
```
- State "DONE" from "TODO" [YYYY-MM-DD Day HH:MM] \
  Delegated — <who> is handling <what>.
```

## Reminders vs Todos

| Coy says | System | Backend |
|----------|--------|---------|
| "remind me at 9 AM to X" | `reminder-db` | Google Tasks |
| "create a todo for X" / "add to my list" | org-mode inbox | inbox.org |
| "remind me tomorrow at 4 AM" | `reminder-db` | Google Tasks |
| "I need to remember to..." (no time) | org-mode inbox | inbox.org |
| "set reminders for upcoming events" | **cron job** | Hermes cron |

Never use org-mode inbox for time-based reminders. Use `reminder-db` skill (Google Tasks-backed).

**🚨 Don't create a todo when Coy asks you to set reminders for specific upcoming events.** Do the work immediately (look up schedule, set cron jobs). Only create a todo if you genuinely cannot find the data after a reasonable attempt.

## Org File Editing Conventions

- **Properties drawers** use exact format:
  ```
  :PROPERTIES:
  :ID:        UUID
  :SPRINT:    4
  :POINTS:    3
  :VALUE:     High
  :GOAL:      Description of done
  :END:
  ```

- **`:VALUE:`** uses only canonical values: `Essential`, `Important`, `Nice-to-have`. Priority mapping: `[#A]`→Essential, `[#B]`→Important, `[#C]`→Nice-to-have.
- **State changes** use logbook format: `- State "DONE" from "STARTED" [2026-05-03 Sat 14:30]`
- **Keywords** after stars: `** STORY My Story` or `*** TODO My Task`
- **Priority** after keyword: `** STORY [#A] My Story`
- **Tags** at end of heading: `** STORY My Story :tag1:tag2:`

## Todo Naming Conventions

- **Name explicitly**: "Set up xurl CLI for Hermes Agent" — not just "Set up xurl"
- **Include the skill path**: e.g., `xurl skill at /data/.hermes/skills/social-media/xurl/`
- **Distinguish system from user setup**: If it's for the Hermes server, say so
- **Tag appropriately**: `:tools:hermes:` for Hermes tooling, `:personal:` for personal items

## Point Reference

| Points | Hours | Meaning |
|--------|-------|---------|
| 0 | ≤1 | Quick fix |
| 1 | 1-3 | One deep-work block |
| 2 | 3-5 | Half day |
| 3 | 5-8 | Full day |
| 5 | 8-13 | Multi-day |
| 8 | 13-21 | Most of a week |
| 13 | 21-34 | Major initiative |
| 21 | 34-55 | Epic |

## Pitfalls (Todo Operations Only)

- **🚨 USE org_query.py, NOT regex/grep/search_files for ALL org file queries.** `search_files` regex breaks on org property whitespace. `grep 'SPRINT: 4'` silently fails on variable spacing. `read_file` line-number prefixes corrupt bulk moves. The parser at `~/.hermes/scripts/org_query.py` handles hierarchy, properties, inheritance, and whitespace correctly.
- **🚨 Shell-special characters in heading titles (`&`, `|`, `>`, `<`) break terminal commands.** Use `execute_code` with Python subprocess, or strip the character before passing to `org_query.py`. Even better: use JSON-based commands that avoid shell parsing.
- **🚨 `hermes_tools.read_file()` has session-level dedup** — re-reading a file returns stale "unchanged" message. **Fix:** Use `org_query.py <file> --verify-line N` or `open()` directly in `execute_code`.
- **🚨 CRITICAL — verify parent EPIC before inserting a `** STORY`.** Use `org_query.py --insert-point "<EPIC name>"` to get the correct insertion line. `patch` anchors can land under the wrong parent.
- **🚨 read_file content includes line number prefixes.** When extracting text from one file into another, you MUST strip the `NNN|` prefix from every line before writing.
- **🚨 EPIC destination does NOT remove from inbox.** After `--create-todo destination:"<EPIC>"`, manually clean up the source inbox entry.
- **🚨 ICEBOX sibling routing:** When an item belongs under an active EPIC but is non-urgent housekeeping, route to the [ICEBOX] sibling EPIC instead. Check `org_query.py --epics` for `[ICEBOX]`-suffixed EPICs with overlapping tags.
- **🚨 `--sprint N` output includes EPIC headings with cumulative child sums.** Use `--retro N` for accurate committed scope — it skips EPIC container headings.
- **🚨 Body-text sections inside a STORY should become proper org children**, not stay as bullet points. Convert to `**** TODO` children with proper properties.
- **🚨 `%^{...}` org capture templates in properties crash `int()` parsing.** Use try/except around `int()` calls on org properties — fall back to `0`.
- **🚨 Coy can override GOAL/VALUE auto-derivation rules.** When he says "infer the goal" or "you can figure it out," do auto-derive. The default rule is "only include if explicitly provided"; his explicit override supersedes it.
- **🚨 Reparenting existing org hierarchy requires raw Python file I/O** — `patch` can't handle level changes. Read both files with `open()`, extract the block, adjust indentation levels, remove original, insert at new position.
- **🚨 Verify WHICH repo/target a fix addresses before creating a todo.** When multiple repos are involved, confirm which one before writing.
- **Place items under existing EPICs** — do not create top-level STORYs when a parent EPIC exists. Find it with `org_query.py --find-epic`.
- **Don't add `:VALUE:` or `:SPRINT:` to TODO-level tasks** — they inherit from parent STORY.
- **Don't close a STORY until all its TODO children are DONE/CANCELLED.**
- **Don't start a new task without cancelling or finishing the current STARTED.**
- **Don't commit more than 16 pts to a sprint without explicit approval.** Coy can override this; when he does, proceed without pushback.
- **Point estimation is not guesswork** — consult the point-to-hour mapping table. A 5-minute task is 0 pts, not 1 pt. Round down when in doubt.
- **Shopping capture:** When Coy mentions wanting to buy something, capture immediately to shopping.org as a bare `** TODO` entry. No SPRINT/POINTS/VALUE.
- **For habit state changes, use `habit_query.py` — NOT `patch`.** Both `--toggle` and `--reschedule` handle LOGBOOK/SCHEDULED/LAST_REPEAT in one command.
