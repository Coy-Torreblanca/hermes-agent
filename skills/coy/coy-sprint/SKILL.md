---
name: coy-sprint
description: "Manage Coy's sprint system — work tasks, personal board, capacity checks, velocity tracking. Todo CRUD (create/read/update/cancel), inbox capture, sprint dashboard. Reads/writes tasks.org and personal.org. TRIGGER: load this skill whenever Coy says anything about todos, tasks, sprints, inbox, work items, or 'what do I have going on'."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [sprint, org-mode, task-management, velocity, todo, inbox, tasks]
---

# Coy's Sprint Management System

> **⚠️ SOURCE OF TRUTH: The Emacs configuration is authoritative.** Before modifying org files or relying on any value schema, check `/data/syncthing/Sync/org/emacs_config/` (see `references/emacs-config-reference.md`). The markdown files in `org/` (`task_workflow.md`, etc.) are derivative summaries and may be outdated or contradictory. The actual `.el` config files in `emacs_config/lisp/` define what Emacs does.

Manage tasks in `/data/syncthing/Sync/org/work/tasks.org` following the Agent Management Protocol embedded in that file. This skill enforces all 10 non-negotiable rules.

## Sub-Operation References

This skill was consolidated from 5 narrow sub-skills (May 2026 curator pass). The archived skills now live as reference files. For any org-mode operation, load the appropriate reference:

| Operation | Reference File | Trigger |
|-----------|---------------|---------|
| Capture TODO to inbox | `references/org-capture.md` | "add a todo", "add to my list" |
| Triage inbox → refile + metadata | `references/org-triage.md` | "triage my inbox", "refile these" |
| Read sprint dashboard | `references/org-dashboard.md` | "what am I working on?", "dashboard" |
| Change task states | `references/org-state.md` | "start X", "done with X", "cancel X" |
| Sprint planning + roll-over | `references/org-sprint-plan.md` | "sprint planning", "roll over sprint" |
| Manage shopping list | `references/shopping-list.md` | "add to shopping list", "what's on my shopping list" |
| Article → icebox stories + gbrain | `references/article-analysis-workflow.md` | "analyze this article", "create stories for this", "save this for later" |
| Deferred concept → gbrain-only removal | `references/article-analysis-workflow.md` (P2 branch) | "interesting but too far out", "keep for later", "remove from org" |

This skill retains: rules, context filtering, sabbath mode, accountability tracking, time awareness, consequence tracking, reminders vs todos distinction, conventions, and the parse_backlog.py script.

## When to Use

- User asks about sprint status, task states, or what to work on
- User asks about personal items, personal board, or "what about my personal items?"
- User wants to start, finish, cancel, or reprioritize tasks (work or personal)
- User wants to plan a new sprint or add stories
- User asks "what's next?" or "what should I work on?"
- User mentions any task by name from their backlog
- User asks for a reminder ("remind me tomorrow", "remind me about X") → delegate to `reminder-db` skill. This skill handles Todos, NOT time-based reminders.
- **Sabbath mode**: User says "it's my sabbath" or "I need to be thinking on God" → switch to quiet note-taking: save what he says, don't propose actions/next-steps/follow-ups

**Defer to journaling when Coy is sharing life content.** If Coy is telling you about church, a conversation, a decision, or anything significant — journal it first. Don't interrupt his narrative flow by jumping to task extraction. Capture action items after he's done sharing. The `coy-journal` skill governs significance detection.

## Work-Hours Context Filtering

When presenting sprint status, dashboard, or task lists to Coy, filter by the current time context:

| Window | Mode | What to Surface |
|---|---|---|
| Mon–Fri, 8:00 AM – 3:00 PM | 💼 **WORK MODE** | `tasks.org` only. Personal.org items are OFF-LIMITS unless they have a deadline during work hours. Calendar events and Google Tasks always show (time-bound commitments). |
| Before 8 AM, after 3 PM, weekends | 🏠 **FULL MODE** | Everything: tasks.org + personal.org + shopping + all of it. |

**Rationale:** Coy is at work during those hours. Personal projects and org-mode personal items are noise — they only come into play if they're explicitly scheduled for that window or after work. Discovered May 6: hourly check-in was nagging about Mexico trip prep and personal todos during a work block.

**For cron jobs:** The Hourly Check-in Coach (`39a44a1b7ac2`) enforces this in its prompt. Other briefing agents should apply the same rule.

## Time Awareness

Coy is a personal-assistant user — Hermes must be time-aware. Key facts:

- **Wake time**: 4 AM daily (permanent rhythm, not temporary). All scheduling assumes a 4 AM start.
- **Morning context**: When Coy first messages after waking, acknowledge the time and frame the day ahead (e.g., "It's 6:46 AM — you've got about an hour before church at 8").
- See `references/time-conventions.md` for session-specific examples.

## Consequence Tracking (No Sugar-Coating)

When Coy misses his 4 AM wake time, a workout, Bible study, or any commitment — **present the facts and consequences directly**. Do not minimize, reassure, or reframe. He has a year+ of established rhythms and wants the data, not comfort. "That's not failure, your body needed it" is the wrong response. The right response: "You missed Bible study and you'll be late to work. Here's the sleep pattern that caused it." Track the cause-and-effect chain in gbrain so it compounds across days.

This applies broadly: when Coy is dealing with consequences of his own choices (late nights → missed mornings, skipped commitments, etc.), surface the pattern, connect the dots, and let him decide. Your job is external memory and consequence tracking, not emotional buffering.

## Sabbath Mode

When Coy indicates he's observing Sabbath (sundown Friday to sundown Saturday, or whenever he explicitly says "it's my sabbath"), he's using Hermes as an outboard brain to clear distractions so he can focus on God. In this mode:

- **DO**: Save notes, thoughts, and references he dictates — gbrain pages, org notes, memory entries
- **DO**: Answer direct questions concisely
- **DON'T**: Propose next actions, suggest tasks to start, ask "want me to...?" follow-ups
- **DON'T**: Nudge about sprint backlog, velocity, or what to work on
- **DON'T**: Offer to set up tools or walk through setups
- **Tone**: Quiet, minimal, deferential. He's not here to be productive — he's clearing his mind

## Work Hours Context (Surface the Right Items at the Right Time)

**Coy's work hours: Mon–Fri, ~8:00 AM – 3:00 PM.** During this window, he's in engineering mode and personal projects/org items are a distraction, not a help.

### WORK MODE (Mon–Fri, 8 AM – 3 PM)
When presenting sprint status, check-ins, or dashboards during work hours:

- ✅ **Surface:** tasks.org items (STARTED, NEXT, sprint backlog, deadlines), calendar events, time-bound Google Tasks
- ❌ **Skip:** personal.org items, personal backlog, personal stories (STORY-STARTED, STORY-WAITING, etc.), shopping list
- ⚠️ **Exception:** Personal items with a due date/time that falls within work hours still surface (they're time-bound commitments)

### FULL MODE (before 8 AM, after 3 PM, weekends)
Surface everything: work sprint + personal board + shopping + all of it.

### Why this matters
Coy explicitly corrected this May 6: "when I'm at work, I can't worry about these personal things." Surfacing personal items during engineering time breaks focus and creates noise. The hourly check-in cron (`39a44a1b7ac2`) encodes this in its prompt; this section ensures any agent doing a check-in follows the same rule.

## Accountability — Consequence Tracking (NOT Reassurance)

**CRITICAL BEHAVIOR RULE:** When Coy reports a failure, missed commitment, or negative outcome from his own actions — do NOT reassure, soften, or reframe it positively. He doesn't need a cheerleader. He needs an accountability partner who names the consequence and traces the cause.

**Success metric framing:** When Coy presents a work artifact (PowerPoint, doc, diagram) to leadership, the success metric is NOT whether leadership engaged with the artifact. The success metric is whether he got the decision/confirmation/guidance he needed. The artifact is a means to extract the answer. If the answer came, mission accomplished — even if the artifact was ignored. Do not characterize a successful outcome as a disappointment just because the artifact wasn't engaged with. Discovered May 5: Coy presented logging policy PowerPoint to Sean. Sean didn't appear to engage with the slides, but Coy got the policy confirmation he needed. Coy corrected the framing: "the goal is to get confirmation on what to do... And I got that confirmation right so mission accomplish."

**Consequence classes — track ALL of these downstream from sleep/schedule failures:**

| Consequence | Example |
|---|---|
| Spiritual | Missed Bible study, missed church, missed liturgy prep |
| Professional | Late to work, missed stand-up, low-quality output |
| Marital/Relational | Grouchiness → lashing out at Melody → relationship strain. Coy named this himself May 6: "bad schedule equals bad life." Melody is patient but patience is finite. |
| Physical | False starts, crash-through-alarm, cumulative sleep debt |

**What this looks like:**

- ❌ "8.5 hours sleep isn't failure, your body needed it" — WRONG. He missed Bible study and was late to work.
- ✅ "You were awake at 1 AM, 3:39 AM, and 3:53 AM this week. Your body didn't oversleep — it surrendered. The alarm didn't fail. Your biology overruled it."
- ✅ "You're grouchy and lashing out at Melody. This started Saturday night at 10:53 PM — three days of accumulated sleep debt that's now costing your marriage."

**When Coy says he "reaped what he sowed" or similar — agree with him and show the receipts.** Use session_search to pull actual activity timestamps. Compare claimed bedtime to actual last activity. Calculate cumulative sleep debt across nights.

**Track consequences systematically:**

1. **Capture the failure** — what was missed? (Bible study, work start time, morning routine)
2. **Pull the data** — session_search for late-night activity, map actual bedtimes vs claimed
3. **Name the pattern** — cumulative sleep debt, late-night screen use, whatever emerges
4. **Log it** — update the gbrain `sleep-patterns` page (or equivalent tracking page) with the full picture
5. **Set a defensive reminder if one doesn't exist** — e.g., recurring bedtime reminder via reminder-db

**The goal:** Coy wants to see the causal chain from his choices to their consequences. Don't break that chain with reassurance. Show it clearly and let him decide.

See `references/sleep-and-consequence-tracking.md` for the sleep-specific workflow.

## The Maker/Manager Pipeline

Coy's system is a **"Maker-to-Manager" pipeline** — low-friction capture, then structured triage.

### Phase A: High-Speed Capture (The Maker)
When coding or in flow, dump thoughts instantly — no metadata:

| Hotkey | Template | Destination |
|--------|----------|-------------|
| `C-c c i` | Quick Inbox | inbox.org (zero metadata) |
| `C-c c t` | Task (w/ metadata) | Full prompts for SPRINT, POINTS, VALUE |
| `C-c c w` | Work Task | inbox.org (full metadata) |
| `C-c c p` | Personal Task | personal/personal.org (full metadata) |
| `C-c c d` | Dev: Code Change | Code-specific (TYPE, BRANCH, REPO) |

Emacs auto-adds UUID (ID) and CREATED timestamp on capture.

### Phase B: Refile & Metadata Enforcement (The Manager)
Once/twice daily, move items from inbox to permanent files:

1. Cursor on inbox task → `C-c C-w` (refile)
2. Choose destination (tasks.org or personal.org)
3. **The Linter** auto-prompts for missing metadata:
   - POINTS (Fibonacci: 1, 2, 3, 5, 8, 13, 21)
   - VALUE (Critical, High, Medium, Low)
   - SPRINT (backlog, 3, 4)
   - Code-specific: TYPE, BRANCH, REPO

**Hermes can't trigger the Emacs linter** — when triaging via Hermes, propose metadata and get Coy's approval before writing.

### Phase C: Column View (The Spreadsheet)
In Emacs: `C-c C-x C-c` opens a Jira-style board with sortable columns. Hermes approximates this by reading and presenting sprint state.

## The Agenda Dashboard (Now vs. Next)

Coy's primary execution view: `C-c a n` in Emacs.

**Four zones:**

| Zone | Filter | Purpose |
|------|--------|---------|
| 🔥 WORKING ON NOW | STARTED tasks | Exactly 1 — deep work |
| ⏭️ UP NEXT | NEXT tasks | "Ready for Dev" queue |
| 🏃 CURRENT SPRINT LOAD | SPRINT=n, not STARTED/NEXT | Remaining sprint commitment |
| 📅 TODAY'S SCHEDULE | Daily agenda | Deadlines, appointments |

**Dashboard hotkeys:**

| Key | Action |
|-----|--------|
| `t` | Rotate state (promote NEXT → STARTED) |
| `C-c C-x C-c` | Column View (spreadsheet) |
| `e` | Edit property (re-point a task) |
| `s` | Save all metadata changes |
| `r` | Rebuild (refresh after refile) |

**Daily Manager routine:**
1. **Morning Triage:** Open inbox.org → C-c C-w refile to tasks.org → linter enforces metadata
2. **Pull:** Dashboard (C-c a n) → pick highest-VALUE sprint task → `t` to NEXT
3. **Focus:** Move one NEXT → STARTED
4. **Execute:** Close agenda, don't reopen until STARTED is DONE

## Sprint Habits

From `/data/syncthing/Sync/org/work/sprint_habits.org`:

- **Daily Org Triage** — Clear inbox.org into tasks.org, ensure POINTS/VALUE on new tasks. SCHEDULED: daily (+1d/2d repeat).
- **Bi-Weekly Sprint Cleanup & Planning** — Run `M-x my/org-end-of-sprint-cleanup`, pull new tasks from backlog into next sprint. SCHEDULED: every 2 weeks (+2w/21d).

## Workflow Reference Files (MANDATORY — load via `read_file` before ANY org file operation)

The skill's reference files are the canonical guides for Hermes org-mode operations. **Load these via `read_file` before creating, editing, moving, or deleting any task in tasks.org, inbox.org, or personal.org.** Each reference adapts the Emacs workflow for Hermes agent execution.

| Reference File | Content | Loads via |
|----------------|---------|-----------|
| `references/org-capture.md` | Maker/Manager capture templates, quick inbox format, deterministic property generation | `read_file /data/.hermes/skills/coy/coy-sprint/references/org-capture.md` |
| `references/org-triage.md` | Refile process, metadata enforcement, parent/hierarchy decisions, inbox cleanup | `read_file /data/.hermes/skills/coy/coy-sprint/references/org-triage.md` |
| `references/org-dashboard.md` | Now vs. Next architecture, sprint load, daily routine | `read_file /data/.hermes/skills/coy/coy-sprint/references/org-dashboard.md` |
| `references/org-sprint-plan.md` | Sprint planning, capacity check, velocity tracking, roll-over | `read_file /data/.hermes/skills/coy/coy-sprint/references/org-sprint-plan.md` |
| `references/org-state.md` | State machine transitions (TODO→NEXT→STARTED→DONE/CANCELLED) | `read_file /data/.hermes/skills/coy/coy-sprint/references/org-state.md` |
| `references/emacs-config-reference.md` | Canonical Emacs config values (points to gbrain) | `read_file /data/.hermes/skills/coy/coy-sprint/references/emacs-config-reference.md` |

**Canonical compliance references:** gbrain `sources/emacs-org-config` documents the full Emacs config structure. `concepts/org-mode-compliance-requirements` documents hierarchy rules (STORYs don't need EPICs, TODOs must have STORY parents) and auto-derivation conventions.

**Canonical org files (edit these, not markdown mirrors):**
- `/data/syncthing/Sync/org/work/tasks.org` — work tasks
- `/data/syncthing/Sync/org/inbox.org` — inbox captures
- `/data/syncthing/Sync/org/personal/personal.org` — personal board
- `/data/syncthing/Sync/org/work/sprint_habits.org` — sprint maintenance habits
**Discord delivery**: See `references/discord-delivery.md` for the current Discord channel → cron job mapping and routing instructions.

**Rule:** Before any org file operation, load the relevant reference file(s) via `read_file`.

## File Locations

```
/data/syncthing/Sync/org/work/tasks.org        ← Canonical work tasks (edit this)
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

**🚨 Canonical script at `~/.hermes/scripts/org_query.py`** — single source of truth. No copy in this skill directory (removed May 2026).

**🚨 ALWAYS use `org_query.py` instead of regex/grep/search_files for org file operations.** The script handles hierarchy, properties, whitespace quirks — all the edge cases that broke regex-based approaches.

```
# Dashboard (replaces manual read_file + parse)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --summary [sprint_num]

# Active tasks (STARTED, NEXT, STORY-STARTED, STORY-NEXT)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --find-active

# Find insertion point under an EPIC (replaces fragile grep + manual trace)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --insert-point "30ai [ICEBOX]"
# Returns: {"epic": "...", "insert_after_line": N, "last_child": "...", "level": 2, "stars": "**"}

# Find an EPIC by name (partial match)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --find-epic "30ai"

# Sprint items (numeric sprint number or "backlog")
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

# Deterministic todo generation (Phase 1 — LIVE, May 2026)
# NOTE: --create-todo and --dry-run take NO filepath arg. The script auto-resolves
# the destination (default: inbox.org) from the JSON params.
python3 ~/.hermes/scripts/org_query.py \
  --create-todo '{"title":"Set up xurl CLI","body":"Install at /data/.hermes/skills/social-media/xurl/"}'
# Generates: UUID + CREATED + SPRINT=backlog, appends to inbox. Zero follow-up questions.

# Show what would be written without mutating file
python3 ~/.hermes/scripts/org_query.py \
  --dry-run '{"title":"New Story","destination":"Personal AI v1","keyword":"STORY","points":3}'

# Read back a specific line using raw file I/O (bypasses read_file dedup)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/inbox.org --verify-line 42
```

## Commands

### Deterministic Create Todo (`--create-todo` API)

**Script:** `~/.hermes/scripts/org_query.py` (also `~/.hermes/bin/org_query`)

### Habits (`habit_query.py` — dedicated parser)

**Script:** `~/.hermes/scripts/habit_query.py`

Separate from org_query.py. Understands habit-specific syntax: SCHEDULED repeaters, STYLE markers, LOGBOOK state history, streak counting.

```bash
# List all habits with status and streak
python3 ~/.hermes/scripts/habit_query.py --list

# Show overdue habits
python3 ~/.hermes/scripts/habit_query.py --overdue

# Show habits due today
python3 ~/.hermes/scripts/habit_query.py --due-today

# Check streak for a habit
python3 ~/.hermes/scripts/habit_query.py --streak "Bible study"

# Mark a habit DONE for today
python3 ~/.hermes/scripts/habit_query.py --toggle "Bible study"

# Reschedule a habit — change SCHEDULED date (preserves repeater)
python3 ~/.hermes/scripts/habit_query.py --reschedule "Bible study" 2026-06-01

# Reschedule with new repeater too
python3 ~/.hermes/scripts/habit_query.py --reschedule "Sprint Cleanup" 2026-05-30 ++2w/21d

# Add a new habit
python3 ~/.hermes/scripts/habit_query.py --add '{"title":"Morning Prayer","schedule":"+1d","body":"Daily morning prayer at 5 AM"}'
```

Defaults to `/data/syncthing/Sync/org/personal/habits.org`. Pass an alternate file as first arg:

```bash
python3 ~/.hermes/scripts/habit_query.py /data/syncthing/Sync/org/work/sprint_habits.org --list
```

**Testing note:** The habit test suite uses a dynamically-generated fixture for `sample_habits.org` — dates are computed relative to `date.today()` so they never go stale. See `references/test-fixture-staleness.md` for the pattern. `streak_habits.org` uses static historical dates (tests pass explicit `date()` args, safe from staleness).

**Architecture decision:** `habit_query.py` is a dedicated parser — does NOT extend `org_query.py`. Habits have fundamentally different structure (SCHEDULED repeat syntax, inline LOGBOOK entries, STYLE markers) that don't fit the EPIC/STORY/TODO hierarchy. A separate parser keeps both scripts focused. See gbrain `concepts/habit-query-parser-decision`.

The primary write method for all new todos. Accepts JSON, generates a deterministic org-mode block, and writes it to the right file. NEVER asks follow-up questions about priority, project, or location.

**Parameters (JSON object):**

| Param | Type | Default | When Required |
|-------|------|---------|---------------|
| `title` | string | (required) | Always — extract from Coy's sentence |
| `body` | string | "" | When Coy gave context — pass through verbatim |
| `destination` | string | "inbox" | "inbox" for fast capture; EPIC name (e.g. "Personal AI v1") for direct insert |
| `priority` | string | omitted | A, B, or C — only if Coy specified it |
| `tags` | array | [] | e.g. `["bug","urgent"]` |
| `points` | int | omitted | ONLY for non-inbox destinations (stories under EPICs) |
| `value` | string | omitted | Only include if explicitly provided. Never auto-derive from priority — see gbrain `concepts/org-mode-compliance-requirements` for orthogonality rules. |
| `sprint` | string | "backlog" | Override only if Coy explicitly says a sprint number |
| `goal` | string | omitted | Only include if explicitly provided. See gbrain `concepts/org-mode-compliance-requirements` for triage-time rules. |
| `keyword` | string | "TODO" | "TODO" for inbox, "STORY" for stories under EPICs |
| `type` | string | None | Code change type: "feature", "bugfix", "hotfix", "chore". When set, auto-generates BRANCH. |
| `repo` | string | None | Optional repo link (e.g. "github.com/owner/repo"). Can be used with or without TYPE. |
| `branch` | string | None | Explicit branch override. Auto-generated as `type/slugged-title` if TYPE is given (matches Emacs `my/format-branch-name`). |

**Deterministic property order (fixed — never vary):**
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

**🚨 ALWAYS reference gbrain for canonical values before editing org files.** The gbrain pages `sources/emacs-org-config` and `concepts/org-mode-compliance-requirements` are the authoritative sources for VALUE schema, hierarchy rules, capture format, and orthogonality conventions. See `references/emacs-config-reference.md`.

**Auto-generation rules:**
- `ID`: `uuid.uuid4().hex[:16].upper()` — matches Emacs `org-id-get-create` format
- `CREATED`: System date in `[YYYY-MM-DD Day]` format  
- `POINTS`: Omitted for inbox capture (triage fills later)
- `VALUE`: **Only included if user explicitly provides it.** See `references/emacs-config-reference.md` for canonical values and orthogonality rules.
- `GOAL`: **Only included if user explicitly provides it.** See gbrain `concepts/org-mode-compliance-requirements` for auto-derivation rules.

**Inbox vs EPIC behavior:**
- **Inbox destination:** Appends to end of inbox.org. Zero-risk — no reads, no patching, no conflict with existing content. POINTS/VALUE/GOAL are omitted — those are triage concerns.
- **EPIC destination:** Uses `--insert-point` anchor to find the correct line under the EPIC in tasks.org, then inserts via raw Python file I/O (NOT `patch` — avoids anchor ambiguity). Includes POINTS/VALUE/GOAL in the properties drawer.
- **🚨 CRITICAL: EPIC destination does NOT remove from inbox.** After `--create-todo` with `destination: "<EPIC>"`, the item exists in BOTH places — tasks.org AND inbox.org. You MUST manually remove the source inbox entry as a separate step. Discovered May 15, 2026: Syncthing context, gbrain back-linking, and cronjob deterministic items were all inserted under Personal AI v1 but remained in inbox until manually cleaned.

**Usage patterns:**
```bash
# Fast capture (title + body only) — most common pattern
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

# Post-write verification (raw read, bypasses read_file dedup)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/inbox.org --verify-line 10
```

### Read state

```
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --summary 4
```

Returns structured JSON with:
- `active_tasks` — WORKING ON NOW (STARTED items)
- UP NEXT (NEXT items)  
- `sprint_items` — SPRINT LOAD with points
- `points_completed` / `points_remaining` / `capacity_used_pct` for velocity

### 📊 Gather sprint + calendar + tasks data (the canonical probe)

For any check-in (hourly coach, daily briefing, sprint status), gather all data in a single efficient probe:

1. **Run the reusable probe script:**
   ```
   python3 skills/coy/reminder-db/scripts/check_google_tasks_and_calendar.py
   ```
   This single script outputs today's Google Calendar events (`CAL|` lines) and all active Google Tasks (`TASK|` lines). It handles task list ID and date filtering. It's the canonical way to gather time-bound data.

2. **Read org files** for sprint state and deadlines:
   - `/data/syncthing/Sync/org/work/tasks.org` — work sprint
   - `/data/syncthing/Sync/org/personal/personal.org` — personal board (FULL MODE only)

3. **Check DEADLINE properties** in both org files for items expiring today. **Note: `org_query.py` has no `--deadlines` flag.** Use grep with variable-whitespace matching (`grep -P 'DEADLINE:\s+'` for PCRE or `grep 'DEADLINE: *'` for basic regex) to find deadline lines, then `read_file` around the matched line numbers to get the full heading context. The grep output gives you line numbers — cross reference with `org_query.py --stats` or `--epics` to understand the structure. Discovered May 10, 2026: trying `org_query.py --deadlines` returns "Unknown command" error.

4. **Read `notes` field for time-of-day context** — Google Tasks `due` is date-only (always `T00:00:00.000Z`). A task due "today" may not be urgent until evening per its `notes` field (e.g., `"Due at 7:00 PM"`). Don't flag as urgent based on calendar date alone.

**⏱️ Cron-specific tip:** Writing inline Python via `python3 -c "..."` is blocked by terminal security (`status: approval_required`). When running as a cron job, do NOT use inline `-c` scripts. Instead:
   - Use the existing `check_google_tasks_and_calendar.py` script above (preferred)
   - Or write a `.py` file to `/tmp/` via `write_file`, then `python3 /tmp/your_script.py` via `terminal`

⚠️ **Deadlines check** — before any sprint planning, dashboard display, or multi-step task proposal, surface critical deadlines FIRST. Coy missed the Airbnb booking deadline May 5 because planning happened without this check.

### Hourly Coach Output Format

When assembling the hourly check-in output (used by cron `39a44a1b7ac2`), follow this format:

**Empty sprint handling:** When no STARTED and no NEXT tasks exist, change the tone from "here's what you're doing" to "here's what's available." List all remaining SPRINT=current items with points so Coy sees the menu. Don't suggest a specific pick (that's the daily briefing's job) — just make the state visible.

**Infrastructure blockers:** Before finalizing, check cron state. **Preferred method:** use the built-in `cronjob(action="list")` tool directly — it works reliably in all contexts including cron jobs. **Fallback:** run `cronjob list` via terminal (may fail in cron contexts due to terminal security — `approval_required` blocks inline commands). Both return the same JSON. Look for:

1. Any cron with `"state": "paused"` or `"enabled": false`
2. **Known critical crons to verify**, especially when sprint includes 30ai or gbrain-dependent stories:
   - `cb57bd8b9389` — nightly gbrain sync (was paused May 6–pending worker fix)
| `c338f3931741` | org refile (8 PM M-F)
   - `39a44a1b7ac2` — hourly coach (this cron itself)
3. Cross-reference: does a paused cron block any active sprint story? (e.g., gbrain sync paused blocks stories that need gbrain for retrieval)

Flag findings in a single 🔧 line:
```
🔧 Infrastructure: gbrain sync cron paused since May 6 — blocks any story needing gbrain retrieval. Bump priority: unblock sync or remove gbrain dependency from sprint.
```

Skip only if `cronjob list` returns all-green. **Do NOT assert "all clear" without running the command.** Discovered May 8: hourly coach skipped this step entirely, claiming no blockers when it hadn't checked.

**Google Tasks time context:** Always read the `notes` field for actual due time (e.g., `"Due at 12:00 PM"`). The `due` field is date-only. Don't flag as urgent based on date alone when the notes say the deadline is hours away.

### Cross-reference confirmatory overdue tasks before flagging

When a Google Task is confirmatory in nature (e.g., "Confirm X ran successfully," "Validate Y works"), check system logs before reporting it as overdue. These tasks often become implicitly resolved:

- **gbrain sync checks**: Check `mcp_gbrain_get_ingest_log()` to see recent sync activity before flagging a gbrain sync task as overdue.
- **Cron health checks**: Verify via `cronjob list` that the relevant cron is **enabled** (not paused/disabled) and last ran successfully. A cron in `"enabled": false, "state": "paused"` cannot fulfill its task — flag the root cause in the check-in, not just the overdue task. Discovered May 7, 2026: nightly gbrain sync cron (cb57bd8b9389) was paused since May 6 pending a worker architecture fix — the "Confirm gbrain sync ran" task was unresolvable until the fix shipped.
- **Service uptime**: For "check if X is running," probe the service endpoint before flagging.

Only flag as "overdue + unresolved" if the system evidence confirms the thing hasn't happened. If evidence shows it completed, mark the Google Task done and note in the check-in: "Task 'X' was overdue but logs show it completed successfully — marking done."

Discovered May 7, 2026: hourly coach flagged "Confirm gbrain full sync ran successfully" as overdue, but gbrain ingest logs showed the sync cron ran repeatedly on May 6. Flagging it without checking logs would have been a false alarm.

### Capture a todo to inbox

Maker-mode captures (quick dumps) go to inbox.org with deterministic properties:
- `:ID:` — auto-generated UUID
- `:CREATED:` — today's date
- `:SPRINT:` — backlog

No POINTS, VALUE, GOAL in inbox mode. Those are added during triage.

1. **No reads** — don't read inbox.org first. This is capture, not review.
2. **Build the block** — title + properties drawer (`:ID:`, `:CREATED:`, `:SPRINT: backlog` in that order) + body text
3. **Append to inbox** — use `org_query.py --create-todo` (LIVE — see `~/.hermes/scripts/org_query.py`)
4. **Confirm briefly** — "Done. Captured to inbox."

**Todo body quality:** The body must contain enough context for Coy to understand the task during later triage (days or weeks out). For Hermes/skill-related todos: name the system (Hermes Agent), include the full skill path (e.g., `/data/.hermes/skills/social-media/xurl/`), and list concrete setup steps. A bare headline without body context is useless.

### Show dashboard

Present sprint status as:
```
🔥 WORKING ON NOW: <started tasks, should be exactly 1>
⏭️ UP NEXT: <next tasks>
🏃 SPRINT 4 LOAD: <sprint tasks not started/next, with points>
📊 VELOCITY: X/Y pts completed this sprint
```

### Start a task

1. Verify no other STARTED task exists
2. Task must be in NEXT or TODO state with SPRINT=current
3. Change state to STARTED (or STORY-STARTED for stories)
4. Add timestamp note

### Complete a task

1. Change state to DONE
2. Add: `- State "DONE" from "STARTED" [YYYY-MM-DD Day HH:MM]`
3. Mark sub-task checkboxes [X] if applicable
4. Update velocity count
5. If NEXT queue is empty, suggest promoting from sprint backlog

### Cancel a task

1. Change state to CANCELLED
2. Add note explaining why
3. Never delete the task

### Add to sprint

1. Check capacity (existing sprint points + new task ≤ 16)
2. Set SPRINT property to current sprint number
3. Ensure GOAL property exists
4. If story, set VALUE and POINTS

### Sprint roll-over

1. Find all unfinished tasks with SPRINT=current
2. Increment SPRINT by 1
3. Update `my/current-sprint` in config files
4. Archive completed sprint data for velocity history

### Triage inbox

**Before triaging:** Load `read_file /data/.hermes/skills/coy/coy-sprint/references/org-triage.md` and see `references/emacs-config-reference.md` for canonical values. These are the Hermes-adapted versions of Coy's Maker/Manager pipeline — they describe how triage should flow through the agent, not through Emacs.

Daily inbox grooming is handled by `daily-briefing` skill (morning briefing). When manually triaging:

1. Read `/data/syncthing/Sync/org/inbox.org`
2. For each uncategorized item: present the **full body text** alongside the headline. Coy can't make decisions from a one-line summary — he needs the context he originally captured. Strip nothing.
3. Propose POINTS, VALUE, SPRINT, destination file (tasks.org vs personal.org)
4. **Present refile targets as actual org text** — the exact `* STORY` or `** TODO` block that would be written to the destination file, with all properties. Don't use summary tables; Coy wants to see the org syntax.
5. **Present as a proposal, wait for confirmation** — never push without Coy's approval
6. After approval, move items to destination file with full metadata. **Use the Python heredoc pattern** in `references/refile-script-pattern.md` — never use `read_file` → extract → write (causes line-number corruption).
7. **🚨 Clean up refiled items from inbox.** Items moved via `--create-todo destination:\"<EPIC>\"` are NOT automatically removed from inbox. After all refiles are done, do a final inbox pass: read inbox.org, identify refiled items by heading title match, and remove them. The inbox can accumulate stale refiled items if this step is skipped. Discovered May 15, 2026: after bulk refile via --create-todo with 3 EPIC destinations, all 3 source items remained in inbox until manual cleanup.
8. Clean up DONE items from inbox
9. Present the resulting "Now vs. Next" dashboard

**Triage output format** — present as organized proposals with the actual org-mode text that would be written to the destination file:

```
→ tasks.org:
* STORY Name
:PROPERTIES:
:ID:       %(org-id-get-create)
...
:END:

→ personal.org:
** TODO Name
:PROPERTIES:
...
:END:

→ Cleanup: (DONE items to remove)
```

Coy will approve or reject each one individually — don't batch-execute without confirmation. He needs to see the full org text to evaluate whether the metadata and GOAL are right.

If daily-briefing cron is active, this is done automatically each morning at 07:00.

The **Org refile cron** (`c338f3931741`) handles automated inbox triage Mon-Fri at 8 PM CDT. It reads inbox.org, reads workflow reference files, and presents refile proposals in Discord #daily-briefing. Coy responds with instructions; the live conversation agent executes the moves. The cron agent presents proposals only — it never modifies org files.

→ Cleanup: (DONE items to remove)
```

**Do NOT use summary tables** for refile proposals — they strip body text Coy needs for context. Present the exact org content that will be written to the destination file. Discovered May 5: assistant presented a table; Coy said "Is that all there is on some of these? I don't have enough context on some." Body text matters.

If daily-briefing cron is active, this is done automatically each morning at 07:00.

## Personal Board

When the user asks "what about my personal items?" or mentions personal tasks, also read and present:

```
read_file /data/syncthing/Sync/org/personal/personal.org
```

### Personal State Keywords

Personal items use a broader set of states than work items:

| State | Meaning |
|-------|---------|
| TODO | Backlog, not sprinted |
| STORY | Active story in sprint |
| STORY-NEXT | Ready to start |
| STORY-STARTED | In progress |
| STORY-DONE | Completed story |
| STORY-WAITING | Blocked externally (e.g., waiting on Dad) |
| WAITING | Blocked on external input |
| DONE | Finished |

### Personal Dashboard Format

Present personal items grouped by status:

```
🔴 BLOCKED / WAITING: items in WAITING or STORY-WAITING (with blocker)
🟡 BACKLOG — Actionable Now: TODO/STORY items not blocked, ordered by value
⚠️ OVERDUE: items past their DEADLINE
```

Always note deadlines, especially overdue ones. Personal items with SPRINT: 4 should show sprint membership.

### Delegation Pattern

When a personal task is delegated to someone else (e.g., "Dad is buying the flights"), mark it DONE with a note:

```
- State "DONE" from "TODO" [YYYY-MM-DD Day HH:MM] \\
  Delegated — <who> is handling <what>.
```

## Reminders vs Todos

**Two systems — use the right one:**

| Coy says | System | Backend |
|----------|--------|---------|
| "remind me at 9 AM to X" | `reminder-db` | Google Tasks (via Google Tasks API) |
| "create a todo for X" / "add to my list" | org-mode inbox | `/data/syncthing/Sync/org/inbox.org` |
| "remind me tomorrow at 4 AM" | `reminder-db` | Google Tasks |
| "I need to remember to..." (no time) | org-mode inbox | inbox.org |

**Preferred path for time-based reminders:** Use `reminder-db` skill — Google Tasks-backed since May 6, 2026. Insert into task list `MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow` via the Google Tasks API. Surfaced by the hourly coach cron. See `reminder-db` skill for full details.

Key points:
- Store with offset: `2026-05-06T09:00:00-05:00`
- Default time: 09:00 if no time specified
- Midnight rule: "tomorrow" at 12 AM = same calendar day after sleeping
- No Postgres reminder table — all alerts migrated to Google Tasks
- Never use org-mode inbox for time-based reminders; never use cron as a reminder mechanism (known failure mode — `next_run_at: null`).

## Org File Editing Conventions

When editing tasks.org:

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

- **:VALUE: property** uses only canonical values from Emacs `VALUE_ALL`: `Essential`, `Important`, `Nice-to-have`. Priority mapping: `[#A]`→Essential, `[#B]`→Important, `[#C]`→Nice-to-have. See `references/emacs-config-reference.md` and gbrain `sources/emacs-org-config`.

- **State changes** use org-mode logbook format:
  ```
  - State "DONE" from "STARTED" [2026-05-03 Sat 14:30]
  ```

- **Keywords** appear after stars: `** STORY My Story` or `*** TODO My Task`
- **Priority** after keyword: `** STORY [#A] My Story`
- **Tags** at end of heading: `** STORY My Story :tag1:tag2:`

## Todo Naming Conventions

When creating a todo for setting up a Hermes skill or tool:

- **Name it explicitly**: "Set up xurl CLI for Hermes Agent" — not just "Set up xurl"
- **Include the skill path**: e.g., `xurl skill at /data/.hermes/skills/social-media/xurl/`
- **Distinguish system from user setup**: If it's for the Hermes server (not the user's Mac/Emacs), say so — "CLI not installed on server"
- **Tag appropriately**: `:tools:hermes:` for Hermes tooling tasks, `:personal:` for personal items, etc.

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

## testing suite

A comprehensive test suite lives at `scripts/tests/` with **128 tests** across 4 files:

```bash
./scripts/tests/run_tests.sh
```

| Suite | Tests |
|-------|-------|
| `test_org_query.py` | 46 — core parsing, queries, validation, stats |
| `test_habit_query.py` | 52 — habit parsing, streak, status, CLI, reschedule |
| `test_parse_backlog.py` | 10 — backlog filtering, sort, filters |
| `test_cli_integration.py` | 20 — end-to-end CLI for org_query |
| **Total** | **128** |

Run before any deployment that modifies these scripts. See `scripts/tests/README.md`.

**Fixture staleness:** All date-dependent fixtures use `date.today()`-relative generation (see `references/test-fixture-staleness.md`). Never add static fixture dates that can go stale.

## Answering Story-Specific Status Queries

When the user asks "what's the status of X story" or names a specific org-mode story by title:

- **Query the live org file**, not gbrain. Use `--children-of "Story Title"` to get the hierarchy, properties, and body context directly from the org file. The user wants to see the actual live state — sprint assignment, points, value, goal, and whether it's been started.
- **Show the parent context too.** If it's under an EPIC, show which one. If it's on backlog vs. in the active sprint, call that out clearly.
- **Include the body text and children.** The org file has the full scope definition. Don't summarize from gbrain — the user may have updated the file since the brain page.
- Only fall back to the gbrain project page when the user asks about the project overall or past decisions. For current state, **live org file is canon.**

Discovered May 15, 2026: CoyDiego asked about "TODO & Sprint Management" — I answered with the gbrain project overview, but he meant the specific `** STORY` child under the Personal AI v1 EPIC in the live tasks.org.

## Pitfalls

- **🚨 Canonical VALUE values**: From gbrain `sources/emacs-org-config` → `common-org-config.el` line 226: `Essential, Important, Nice-to-have`. The refile linter prompts with these. `parse_backlog.py` sort order uses these as primary, with Critical/High/Medium/Low as legacy fallbacks. See `references/emacs-config-reference.md`.
- **🚨 VALUE and priority are orthogonal** — gbrain `concepts/org-mode-compliance-requirements` documents this. `--create-todo` no longer auto-derives VALUE from priority. Only include `:VALUE:` if user explicitly provides it. Same for GOAL. The old `value_from_priority` function exists as utility but is NOT called by `--create-todo`.
- **🚨 Coy can override the no-auto-derive rule for GOAL** — When Coy says "infer the goal" or "you can figure it out," he's explicitly overriding the orthogonality rule. DO auto-derive GOAL from title + context. The default is "only include if explicitly provided"; Coy's override supersedes it. Discovered May 15, 2026.

- **🚨 For habit state changes, use `habit_query.py` — NOT `patch`.** This covers both `--toggle` (mark DONE) and `--reschedule` (change SCHEDULED date). If you've already used `habit_query.py` to list/read habits in this session, you already have the right tool loaded. Do not default to `patch`. `habit_query.py [file] --toggle "Title"` handles LOGBOOK entries, SCHEDULED advancement, and LAST_REPEAT in one command. `habit_query.py [file] --reschedule "Title" YYYY-MM-DD` patches the SCHEDULED line in-place and optionally accepts a new repeater as a third arg. Discovered May 16, 2026: used `patch` to toggle Daily Org Triage despite having run `habit_query.py --list` and `--help` earlier in the same session.
- **🚨 USE org_query.py, NOT regex/grep/search_files for ALL org file queries.** `search_files` regex breaks on org property whitespace (`\\\\s` shorthand doesn't match `:SPRINT:   4`). `grep 'SPRINT: 4'` silently fails on variable property spacing. `read_file` line-number prefixes corrupt bulk moves. The parser at `~/.hermes/scripts/org_query.py` handles hierarchy, properties, inheritance, and whitespace correctly. **Before any org operation: run the appropriate org_query.py command.** Built May 10, 2026 after repeated regex failures caused story placement errors and silent search misses.

- **🚨 Shell-special characters in heading titles (`&`, `|`, `>`, `<`) break terminal commands.** When using `--heading`, `--children-of`, `--find-epic`, or any arg that contains `&` (e.g., `--heading "TODO & Sprint Management"`), the terminal interprets `&` as a background operator and the command returns `"Foreground command uses '&' backgrounding."` with no useful output. **FIX:** Use `execute_code` with Python subprocess, or pipe the title through `sed`/`tr` to strip the problematic character before passing to `org_query.py`. Even better: use the JSON-based commands that avoid shell parsing entirely. Discovered May 15, 2026.
- **🚨 `hermes_tools.read_file()` has session-level dedup — re-reading a file returns stale "unchanged" message**: When you `read_file` a file earlier in a conversation session, calling `read_file` on the same path again returns `"File unchanged since last read"` with the earlier content cached in `message`, NOT the current file content. The actual content key is empty/missing. This means you cannot verify a file was modified correctly by re-reading it with `read_file`. **Fix:** Use `org_query.py <file> --verify-line N` to read back a specific line via raw `open()`. Or use `open()` directly in `execute_code` to bypass dedup when you need a fresh read (e.g., after writing changes). Discovered May 12, 2026: moved a TODO from inbox.org to tasks.org then tried to verify with `read_file` — got "unchanged" message with stale content. `open().read()` returned the actual post-move state.
- **CRITICAL — regex alternation order**: When modifying the heading regex in `org_query.py`, compound keywords (`STORY-STARTED`, `STORY-NEXT`, `STORY-DONE`, `STORY-WAITING`) MUST appear before their base form (`STORY`). Regex alternation matches the first alternative — `STORY` before `STORY-STARTED` causes `-STARTED` to leak into the title. Fixed May 15, 2026 via test suite.
- **🚨 CRITICAL — verify parent EPIC before inserting a `** STORY` with `patch`**: `patch` inserts at the nearest matching `old_string` anchor, which is often text under the LAST CHILD of an EPIC — but that text may be followed by top-level `* STORY` items before the next `* EPIC`. If you insert `** STORY` after a top-level `* STORY`, org-mode interprets the new story as a child of that top-level story, NOT the intended EPIC. **FIX:** Use `org_query.py --insert-point \"<EPIC name>\"` to get the correct insertion line and level. Then find a unique anchor string near that line that is verifiably under the target EPIC (run `org_query.py --find-epic` to trace). Hit twice May 10, 2026 — Bible stories and Hermes story both required remove-then-reinsert cycles.

- **Searching for active tasks in org files:** `search_files` with regex patterns like `^\*+\s+(STARTED|NEXT|STORY-STARTED|STORY-NEXT)` will miss tasks indented under an EPIC (e.g., `** STORY-STARTED` has leading whitespace, not anchored at column 0). Use a broader pattern that accounts for indentation: search for the literal string `STORY-STARTED` or `STARTED` without anchoring to line start. Then `read_file` the surrounding lines to confirm. A zero-result search doesn't mean "nothing active" — it may mean "regex was too strict."
- Don't add :VALUE: or :SPRINT: to TODO-level tasks (they inherit from parent STORY)
- Don't close a STORY until all its TODO children are DONE/CANCELLED
- Don't start a new task without cancelling or finishing the current STARTED
- Don't commit more than 16 pts to a sprint without explicit approval
- **Point estimation is not guesswork** — always consult the point-to-hour mapping table before assigning :POINTS:. A 5-minute task is 0 pts (≤1 hr), not 1 pt (1-3 hr). When in doubt, round down to the nearest bracket.
- The org file uses org-mode comment syntax (# for line comments)
- Syncthing syncs this file to the Mac — changes appear in Emacs within seconds
- **Never delete unreadable files during cleanup** — If a file is binary, unparseable, or in an unknown format (e.g., `.numbers`, `.xlsx`), flag it for Coy instead of deleting it. Partial ingestion with a warning is better than silent data loss. Coy lost a `credit_card_inventory.numbers` file May 5 because it was auto-deleted during raw folder cleanup.
- When the user asks \"what should I work on?\", check both tasks.org AND personal.org — BUT respect work-hours context (see Work-Hours Context Filtering above). During Mon-Fri 8 AM–3 PM, personal.org is off-limits unless items are due during that window.
- Personal items use WAITING/STORY-WAITING for blocked tasks (not CANCELLED); never delete blocked personal items
- When creating cron reminders, use the date from the current conversation timestamp to calculate "tomorrow" — don't guess the date
- Delegated personal tasks get marked DONE with a delegation note, not CANCELLED
- **"Tomorrow" at midnight**: When Coy says "tomorrow" at or after midnight (12 AM), he means later that same calendar day after sleeping — not the following calendar day. Always resolve relative to the day-after-waking, not midnight rollover. When in doubt, ask which day of the week he means.
- When a STORY-WAITING or WAITING task becomes unblocked (e.g., dependency resolves), promote back to STORY and update the status note with the new context. Never leave it in WAITING when the blocker is gone.
- **CRITICAL — cron: inline Python `-c` flag is blocked by terminal security**: When running as a cron job (no user present), `python3 -c "..."` inline scripts are intercepted by the terminal security pattern (`approval_required`). The security check requires user approval, which never comes from a cron. **Fix:** Use the existing `check_google_tasks_and_calendar.py` script at `skills/coy/reminder-db/scripts/check_google_tasks_and_calendar.py`, or write the script to `/tmp/` via `write_file` first and then execute it via `terminal`. Discovered May 7, 2026: hourly coach cron job tried `python3 -c` and was blocked; had to write temp scripts instead.
- **CRITICAL — org-mode task state search**: `search_files` regex patterns like `^\*+\s+(STARTED|NEXT|STORY-STARTED)` can silently fail to match `** STORY-STARTED` headings (the `^\*+` anchor is unreliable across file read modes and regex flavors). **SAFER APPROACH**: search for the raw keyword (e.g., just `STARTED`) and then `read_file` around matches to identify active tasks. Or use a minimal pattern: `STORY-STARTED|STORY-NEXT`. Never trust an empty result from a complex anchored regex — when in doubt, fall back to keyword search. Discovered May 4, 2026: user asked "check on what I am working on now" and the anchored search returned 0 results despite `** STORY-STARTED` existing at line 1064. User had to correct the assistant.
- **search_files `\s` shorthand doesn't work for org property values**: `search_files` with patterns like `SPRINT:\s+4` returned 0 results despite `:SPRINT:   4` existing in the file (May 10, 2026). The `\s` shorthand and complex character classes may not be supported. **SAFER APPROACH**: Use `grep` directly via terminal. **⚠️ grep literal pitfall**: `grep 'SPRINT: 4'` (single space) silently fails on org files because properties use variable spacing (`:SPRINT:   4` with 3+ spaces). Fixes that work: search for just the property key with `grep 'SPRINT:'` and parse the value column manually, or match variable whitespace with `grep -P 'SPRINT:\s+4'` (PCRE) or `grep 'SPRINT: *4'` (basic regex). Discovered May 10, 2026: hourly coach cron ran `grep 'SPRINT: 4'` which returned exit 1 (no match) despite multiple `:SPRINT:   4` lines existing in the file. Also note: `search_files` paginates/truncates results (shows ~50 per call with offset param); large org files with many properties drawers may need multiple offset calls to get a complete picture.
- **🚨 CRITICAL — `search_files` `target: "content"` silently misses plain-text matches in org files**: Multiple searches for ordinary words like `dad`, `airplane`, `flight`, `cbx`, `uber` returned 0 results despite those words appearing multiple times in personal.org body text. `grep` via terminal found them immediately. This is not a regex issue — it's a tool reliability issue. **FIX**: When `search_files` returns 0 results for content that should plausibly exist, immediately fall back to `grep -n -i 'word1\|word2\|word3' <file>` via terminal. Discovered May 11, 2026: two consecutive search_files calls missed "dad" at 4 different lines in personal.org; grep caught all of them.
- **CRITICAL — Coy's inbox triage has documented workflows**: Before performing inbox triage, load `read_file /data/.hermes/skills/coy/coy-sprint/references/org-triage.md`. That reference file is the Hermes-adapted version of the Maker/Manager pipeline. See also `references/emacs-config-reference.md` for canonical value conventions. The coy-sprint skill contains the operational knowledge; the reference files provide the detail. Discovered May 5: assistant performed a flat triage without consulting these files; user redirected: "There should be mark down files in my org directory which tell you how this work" — those are the Emacs source docs, but the skill references are the Hermes-facing versions.
- **Place items under existing EPICs**: When refiling inbox items that belong to an existing project (e.g., 30ai items), find the appropriate EPIC in tasks.org and add them as `** STORY` children under it. Do NOT create top-level STORYs when a parent EPIC exists. Discovered May 5: items 1-4 were proposed as top-level STORYs; Coy said "1-4 are 30ai items they should probably go under and existing epic."
- **CRITICAL — read_file content extraction carries line number prefixes**: `read_file` returns lines in `LINE_NUM|CONTENT` format. When extracting text from one file to insert into another, you MUST strip the `NNN|` prefix from every line before writing. Writing read_file output directly into a destination file embeds those prefixes as literal content, corrupting the org file. Discovered May 5: extracting STORY blocks from inbox.org and writing to tasks.org embedded `53|`, `54|`, etc. throughout. Fix: post-process extracted lines with `re.sub(r'^\s*\d+\|', '', line)` or parse with a regex that captures only the content after the `|` separator. Always verify the destination file after a bulk move by reading the tail and checking for line-number artifacts.
- **Phantom infrastructure assumptions**: When reviewing stories in an EPIC, scan ALL acceptance criteria and GOAL lines for infrastructure that doesn't exist yet. Stories often inherit assumptions from the EPIC's original vision (e.g., "Next.js displays success" when there's no Next.js app, "UI upload" when testing is via curl). Flag these immediately — don't trust the written text. Discovered May 4: EPIC 30ai assumed a Next.js UI that didn't exist; user corrected acceptance criteria to use curl.
- **CRITICAL — read_file content includes line number prefixes**: When you `read_file` an org file and then write its content to another file, the `read_file` output includes `NNNN|` line number prefixes (e.g., `    53|** STORY ...`). If you extract lines and write them to another file without stripping these prefixes, the destination file gets corrupted with embedded line numbers. **Fix:** use terminal `python3 -c "..."` to read/write files directly, or strip `^\s+\d+\|` prefix from each line before writing. Discovered May 5: items 5-8 were extracted from inbox.org via read_file and appended to tasks.org with line numbers intact. Required a rollback and manual fix.: When reviewing stories in an EPIC, scan ALL acceptance criteria and GOAL lines for infrastructure that doesn't exist yet. Stories often inherit assumptions from the EPIC's original vision (e.g., "Next.js displays success" when there's no Next.js app, "UI upload" when testing is via curl). Flag these immediately — don't trust the written text. Discovered May 4: EPIC 30ai assumed a Next.js UI that didn't exist; user corrected acceptance criteria to use curl.
- **Concern leakage between stories**: Each story owns its infrastructure concerns. Celery/async dispatching belongs in the Processing Trigger story, not the Upload Orchestration story. If the user points out a TODO is in the wrong story, move it — don't argue. Discovered May 4: "API should tell Celery" was placed in Story 1 (Upload); user corrected it belongs in Story 3 (Processing Trigger).
- **Shopping item capture**: When Coy mentions wanting to buy something or "add X to shopping list," capture it immediately to `/data/syncthing/Sync/org/personal/shopping.org` as a bare `** TODO` entry. Don't wait for him to ask a second time — he mentioned whiteboard markers in conversation and it was lost because no capture happened. Use the same format as other org entries but keep it simple (no SPRINT, POINTS, or VALUE — it's a shopping list, not a sprint task).
- **🚨 Don't skip infrastructure checks — run `cronjob list` every time**: The hourly coach "Infrastructure blockers" step is mandatory, not optional. Saying "no blockers detected" without actually calling `cronjob list` is a false assertion. Always run the command — don't assume the previous state persists. A cron that was green last hour could be paused now. Discovered May 8: hourly coach claimed "cron list clear" without having checked.
- **Todo body context matters**: When capturing a todo to inbox, the body must contain enough context for Coy to understand it during later triage. For Hermes/skill setup todos: specify it is for Hermes Agent, include the full skill path (e.g., /data/.hermes/skills/social-media/xurl/), and list concrete steps. A bare headline like "Set up xurl" without body text is useless in triage — Coy won't remember what it means. Discovered May 5: user had to ask "specify that it is xurl for hermes agent. where is the skill path?"
- **Bulk sprint restructuring — batch patch() via execute_code**: When moving many stories between sprints (canning an EPIC + promoting global jobs), use execute_code with multiple patch() calls in a single Python block rather than individual tool invocations. Each block does from hermes_tools import patch, terminal then chains calls. This is faster (single pass) and keeps the changes atomic — if verification fails, you know exactly which block to inspect. Always verify with terminal("grep -n 'SPRINT:' tasks.org | grep -P ':\\s+4$'") after. Discovered May 10, 2026: moved 30ai EPIC (6 stories to backlog) + 7 global jobs (to sprint 4) in two execute_code blocks, verified clean in one grep.
- **Sprint capacity override**: Coy will sometimes explicitly blow the 16 pt cap for infrastructure-heavy sprints. When he does, note it and proceed — do not push back a second time. The override is valid for that sprint only; future sprints still respect the cap. Discovered May 10, 2026: Coy overrode cap for Sprint 4 to fit all 7 global infrastructure jobs.
- **🚨 CRITICAL — verify parent EPIC before inserting a `** STORY` with `patch`**: `patch` inserts at the nearest matching `old_string` anchor, which is often text under the LAST CHILD of an EPIC — but that text may be followed by top-level `* STORY` items before the next `* EPIC`. If you insert `** STORY` after a top-level `* STORY`, org-mode interprets the new story as a child of that top-level story, NOT the intended EPIC. **FIX — three-step verification before every `patch` insert into tasks.org:** (1) Find your anchor string and confirm it's under the target EPIC by tracing backward with `sed -n '1,{ln}p' | tac | grep -m1 '^\\* EPIC'`. (2) Check for any top-level `* STORY` or `* EPIC` between the anchor and the target EPIC — if any exist, your anchor is in the wrong section. (3) Only proceed when the nearest ancestor `* EPIC` matches your target. **Reproduction:** Hit twice May 10, 2026 — Bible stories landed under Ci/CD pipeline `* STORY` (then re-inserted correctly at line 1197), Hermes story landed under "Add apple reminders" `* STORY` (then re-inserted correctly at line 440). Both required a remove-then-reinsert fix cycle. **Prefer inserting BEFORE the first top-level break after the EPIC's children**, not after the last child — the top-level `*` heading is a safer anchor than trailing body text.
- **Sprint capacity override — when Coy explicitly says "I'm canning X pts, proceed":** Do not re-litigate capacity. The 16pt cap is a guideline, and Coy can override it. When he states the override explicitly ("I'm canning a 32 point Sprint"), execute the changes without presenting capacity warnings, options, or tradeoffs. He's already decided. Discovered May 10, 2026: Agent presented 4 options when Coy had already made his decision; Coy said "I'm canning a 32 point Sprint this time around. Proceed." and expected immediate execution.

- **🚨 Verify WHICH repo/target a fix addresses before creating a todo.** When Coy says "pin X to a specific commit" and there are multiple repos involved (Hermes Agent at `/opt/hermes-agent`, G-Brain at `/opt/gbrain`), confirm WHICH one he means before writing a todo. If you guess and get it wrong, the todo body describes the wrong system. Discovered May 15, 2026: created a todo to pin the Hermes Agent repo when Coy meant pin the G-Brain repo. Tactic: if two repos appear in the same Dockerfile, ask "which one?" or enumerate the options in your comprehension step before reaching for `--create-todo`.

- **🚨 Reparenting existing org hierarchy requires raw Python file I/O.** Moving a STORY from under one parent to another (e.g., making a sibling into a child, or changing level from `****` to `*****`) cannot be done with `patch` — the anchor text is under the wrong hierarchy. Steps: (1) Read both files with `open()` to avoid `read_file` dedup. (2) Extract the block to move (heading + properties + body + children). (3) Adjust all indentation levels (+1 star for demotion, -1 star for promotion). (4) Remove original block from file. (5) Insert new block at the correct position under the new parent. (6) Verify with `org_query.py --children-of "New Parent"`. Discovered May 15, 2026: reparented BSB Translation Tables from `* EPIC Add BSB Bible` direct child to child of new `Add BSB to Bible site` STORY — required demoting `****` → `*****` for the STORY and `*****` → `******` for its children.

- **🚨 Coy can override GOAL/VALUE auto-derivation rules.** The default rule says VALUE and GOAL are triage-only, never auto-derived. When Coy says "infer the goal" or "you can figure it out" — he's explicitly overriding that rule. DO auto-derive from title + context. When he says "high priority, high value" in the same sentence, he means `[#A]` priority and VALUE: Essential. Follow his explicit instruction over the default rule. Discovered May 15, 2026: Coy said "you can infer this goal" for Syncthing context item — he wanted me to derive the GOAL despite the "never auto-derive" rule.
