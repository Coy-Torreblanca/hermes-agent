---
name: sprint-planning
description: "Automate sprint planning with backlog grooming, stale detection, capacity checks, gbrain lessons injection, and plan persistence. Phase 4 Item 2."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [sprint, planning, backlog-grooming, stale-detection, gbrain, phase4]
    related_skills: [sprint-retro, coy-sprint, gbrain-query]
---

# Sprint Planning Skill

Automates sprint planning end-to-end: grooms backlog, checks for stale items, ranks by VALUE × recency × dependency, injects gbrain lessons, presents a ranked proposal, and saves the plan to gbrain.

## When to Use

- Coy says "sprint planning", "plan next sprint", "what should I sprint next"
- Coy says "groom the backlog", "check for stale items", "backlog review"
- Coy says "run sprint planning with stale checks"
- End of sprint as part of Bi-Weekly Sprint Cleanup
- On-demand backlog review before sprint planning

## Overview

This skill replaces the manual backlog-reading-and-ranking workflow. It orchestrates three data passes and one gbrain pass before producing a proposal:

```
Phase 1: Current state — sprint number, boundaries, WIP
Phase 2: Backlog grooming — stale checks, missing metadata, orphans
Phase 3: Ranking — VALUE × recency × dependency + capacity check
Phase 4: gbrain lessons — past sprint patterns from brain
Phase 5: Proposal — ranked list with rationale and grooming flags
Phase 6: Execution — set SPRINT on approved items + gbrain save
```

---

## Phase 1: Establish Current State

### 1a. Determine Sprint Number

```bash
# Read active (non-DONE) tasks to find most common SPRINT value
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --stats
```

Key fields: most common sprint number on active (non-DONE) items. This is the **current sprint**.

### 1b. Derive Sprint Boundaries

From the Bi-Weekly Sprint Cleanup habit:

```bash
python3 ~/.hermes/scripts/habit_query.py /data/syncthing/Sync/org/work/sprint_habits.org --list
```

Look for "Bi-Weekly Sprint Cleanup & Planning":
- **Sprint Start** = last LOGBOOK `- State "DONE" from ...` timestamp
- **Sprint End** = `SCHEDULED:` date
- See gbrain [[concepts/sprint-date-derivation]]

### 1c. Check Current WIP

```bash
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --find-active
```

If a STARTED or STORY-STARTED item exists, flag it before proposing sprint changes. The current WIP may need to complete or be cancelled before sprint planning.

---

## Phase 2: Backlog Grooming

### 2a. Read Full Backlog

```bash
# Tasks.org (work backlog)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --sprint "backlog"

# Personal.org (personal backlog — FULL MODE only)
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/personal/personal.org --sprint "backlog"
```

> **Work-hours context:** Skip personal.org during Mon–Fri 8 AM – 3 PM per coy-sprint work-hours rules. Flag "personal items available after 3 PM."

### 2b. Run Stale Detection

```bash
# Items stale for 2+ sprint cycles (~4 weeks)
cd /data/.hermes/skills/coy/coy-sprint && python3 scripts/parse_backlog.py --stale 2

# Items stale for 1+ sprint cycles (~2 weeks) — tighter filter
cd /data/.hermes/skills/coy/coy-sprint && python3 scripts/parse_backlog.py --stale 1
```

Items flagged with a `⏰` prefix have been untouched for N+ sprint cycles. Stale age is calculated from the `:CREATED:` property.

**What to do with stale items:** Present them in the grooming section. Propose one of:
- **Archive to ICEBOX** — move under an appropriate `[ICEBOX]` EPIC
- **Re-estimate** — points may be stale; ask Coy to confirm
- **Keep** — item remains in backlog but note why it's stale
- **Delete** — only if Coy explicitly confirms it's obsolete

### 2c. Metadata Grooming

Scan backlog items for missing or incomplete metadata:

| Check | What to Flag |
|-------|-------------|
| Missing `:POINTS:` | Item has no point estimate → suggest from title context |
| Missing `:GOAL:` | Story has no goal → ask Coy to define one |
| Missing `:VALUE:` | Story has no value → deduce from priority or ask |
| WAITING parent | Item's parent is WAITING/STORY-WAITING → note as blocked |
| Orphaned item | Item under no EPIC or under a CANCELLED parent → flag for routing |

**Grooming output format:**

```
🧹 BACKLOG GROOMING
⏰ Stale (2+ sprints): 8 items flagged
   - Story A (3pts) — untouched since Mar 23
   - Story B (5pts) — untouched since Feb 14
📋 Metadata issues: 3 items
   - Story C — missing :POINTS:
   - Story D — missing :GOAL:
🔗 Orphans: 1 item
   - Story E — under CANCELLED EPIC
```

---

## Phase 3: Ranking & Capacity

### 3a. Read Backlog for Planning

```bash
# Read all backlog items sorted by POINTS (default output)
cd /data/.hermes/skills/coy/coy-sprint && python3 scripts/parse_backlog.py
```

### 3b. Apply Ranking Algorithm

Rank backlog items by composite score:

```
score = VALUE_score × recency_multiplier × dependency_readiness
```

| Factor | Scoring | Source |
|--------|---------|--------|
| **VALUE** | Essential=4, Important=3, Nice-to-have=1 | `:VALUE:` property on item |
| **Recency** | Untouched 2+ sprints → 1.5× multiplier, 3+ sprints → 2× multiplier | `:CREATED:` date vs today |
| **Dependency** | WAITING/STORY-WAITING parent → skip (0 score) | Parent keyword |
| **GOAL clustering** | Items with same or similar GOAL text → group together | `:GOAL:` text, semantic similarity |

If the backlog is small (< 10 items), skip the ranking formula and present directly sorted by VALUE, then POINTS descending.

### 3c. Capacity Check

Count current sprint commitment (non-DONE items with SPRINT=current):

```bash
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --retro <current_sprint>
# → total_points_committed - total_points_completed = remaining
```

**Capacity rule:** Max **16 pts per sprint**. Calculate remaining capacity:

```
remaining_capacity = 16 - (current_committed_points - completed_points)
```

If Coy has previously overridden the cap for this sprint, use the overridden value instead of 16. Note: `-0` overrides are valid for the sprint they were made in, not future sprints.

Propose items up to remaining capacity. If the top-ranked items exceed capacity, present the overflow with a note.

---

## Phase 4: Lessons Learned from Past Sprints (GBrain)

**This is the primary integration point for lessons learned.** Before proposing a sprint plan, pull lessons from gbrain retro pages that the sprint-retro skill saved during previous sprints.

### 4a. Query GBrain for Retro Pages

Search for saved sprint retro pages:

```python
# Find meeting pages tagged with retro
mcp_gbrain_search(query="sprint retro lessons patterns underestimation")
mcp_gbrain_search(query="sprint retrospective")
mcp_gbrain_search(query="sprint planning lessons learned")
mcp_gbrain_list_pages(type="meeting", tag="retro")
```

### 4b. Extract Specific Lessons

From each retro page found, extract:
| Lesson Type | What to Look For | Example |
|-------------|-----------------|---------|
| **Recurring underestimation** | Items flagged as "took 2x estimated" | "30ai setup took 2x estimated" |
| **Repeated pain points** | Attention fragmentation, scope creep | "Sprint 3: 5 EPICs -> 40% completion" |
| **Historical velocity** | Points completed vs committed | Compare velocity trends across retros |
| **Action items** | Improvements suggested but never actioned | "Create sprint planning skill" |
| **What worked** | Practices worth repeating | "Thin vertical slice was effective" |

### 4c. Inject Lessons into Proposal

Inject findings into the proposal:

```markdown
## 📚 Lessons Learned From Past Sprints (from gbrain retro pages)
- 🔴 Sprint 4: Infrastructure stories took 2x estimated -> **padding +2pts for infra items**
- 🟡 Sprint 3: 5 EPICs -> 40% completion -> **limit to 2-3 EPICs this sprint**
- 💡 Sprint 4 retro: "Thin vertical slice worked well" -> **continue focused scoping**
- ⏳ Open: "Create sprint planning skill" -> **planned this sprint** 🎯
```

### 4d. Close the Loop — Lessons Feed Forward

The lessons learned flow is a continuous loop:

```
Sprint N Retro (sprint-retro)
  ↓  Saves lessons to gbrain as meetings/sprint-N-retro
Sprint N+1 Planning (sprint-planning)
  ↓  Reads lessons from gbrain retro pages
  ↓  Injects into planning proposal
Sprint N+1 Execution
  ↓
Sprint N+1 Retro (sprint-retro)
  ↓  Reports on whether lessons were applied
  ↓  New lessons saved to gbrain
  ↓  (loop continues)
```

This ensures lessons are NEVER lost between sprints. Every retro feeds the next planning session, and every planning session checks past retros.

---

## Phase 5: Present Proposal

### 5a. Full Planning Output

```markdown
📋 **SPRINT PLANNING — Sprint N → N+1**

## Sprint Boundaries
- Current: {start} → {end} ({duration})
- Next: {next_start} → {next_end}

## Current Sprint Status
- WIP: {active_task} — {points} pts
- Remaining capacity: {remaining_capacity} pts
- Override active: {yes/no}

## 🧹 Backlog Grooming
⏰ Stale items ({N}):
  - ⏰ Story A (3pts) — untouched since Mar 23 → propose archive
  - ⏰ Story B (5pts) — untouched since Feb 14 → propose re-estimate
📋 Metadata issues ({N}):
  - Story C — missing :POINTS:
🔗 Orphans ({N}):
  - Story E — under CANCELLED parent

## 🏃 Proposed Sprint {N+1} (capacity: {remaining} pts)
| # | Item | Pts | VALUE | EPIC | Rationale |
|---|------|:---:|:-----:|------|-----------|
| 1 | Story A | 5 | Essential | Personal AI | Completes Personal AI v1 EPIC |
| 2 | Story D | 3 | Important | Second Brain | High VALUE, untouched 3 sprints |
| … | | | | | |
|   | **TOTAL** | **14** | | | 2 pts buffer |

## 📚 Context From Past Sprints
- Sprint 4: Infrastructure took 2× → padding +2pts recommended
- Sprint 3: Breadth over depth (5 EPICs) → propose max 2-3 EPICs
```

### 5b. Coy Confirmation Process

After presenting the proposal, use `clarify` to ask for approval:

```python
clarify(
    question="Here's the proposed sprint plan. Which items should I commit to Sprint N+1?",
    choices=[
        "Accept full proposal",
        "Accept but remove [item]",
        "Modify and confirm",
        "Reject — let me adjust"
    ]
)
```

**Do NOT execute** SPRINT changes until Coy confirms.

---

## Phase 6: Execute & Save

### 6a. Set SPRINT on Approved Items

After Coy confirms, for each item:

```bash
# Use patch to change SPRING: backlog → SPRINT: <new_sprint_number>
patch(
    path="/data/syncthing/Sync/org/work/tasks.org",
    old_string="""** STORY Approved Story
:PROPERTIES:
:ID:       UUID
:SPRINT:   backlog""",
    new_string="""** STORY Approved Story
:PROPERTIES:
:ID:       UUID
:SPRINT:   <new_sprint_number>"""
)
```

**Bulk approach (preferred for 5+ items):** Use `execute_code` with chained `patch()` calls to process all approved items in a single turn. See coy-sprint pitfall: "Bulk sprint restructuring — batch patch() via execute_code."

**For items without `:SPRINT:` property:** Add the full property. For items with `:SPRINT: backlog` or `:SPRINT:   backlog`: replace with new sprint number.

**Verification:** After all patches:
```bash
grep -n 'SPRINT:' tasks.org | grep -E ':\s+<new_sprint_number>$'
```
Or use:
```bash
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --sprint <new_sprint_number>
```

### 6b. Save Plan to GBrain

After execution, persist the plan as a gbrain page:

```python
mcp_gbrain_put_page(
    slug=f"meetings/{date}-sprint-{new_sprint_number}-plan",
    content=f"""---
tags:
  - sprint
  - planning
  - sprint-{new_sprint_number}
  - plan
---

# Sprint {new_sprint_number} Plan — {date}

> Generated by sprint-planning skill.

## Sprint Boundaries
- Start: {next_start}
- End: {next_end}

## Committed Items
| Item | Pts | VALUE | EPIC |
|------|:---:|:-----:|------|
| Story A | 5 | Essential | Personal AI |
| Story D | 3 | Important | Second Brain |

## Backlog Grooming Applied
- Stale items flagged: {N}
- Items archived to ICEBOX: {N}
- Metadata fixed: {N}

## GBrain Context Used
- {lesson_1}
- {lesson_2}

[Source: sprint-planning Hermes skill, {date}]
"""
)
```

### 6c. Add Timeline Entries

```python
mcp_gbrain_add_timeline_entry(
    slug="concepts/sprint-planning-skill",
    date="{date}",
    summary=f"Sprint {new_sprint_number} planned — {total_committed} pts committed",
    detail="..."  
)

mcp_gbrain_add_timeline_entry(
    slug="concepts/phase4-sprint-intelligence-plan",
    date="{date}",
    summary=f"Sprint planning skill used for Sprint {new_sprint_number}",
    detail="..."
)
```

---

## Special Cases

### First Sprint Planning (No Current Sprint)
If no active sprint is found (no items with SPRINT=current):
- Sprint number starts at 1
- All items are in backlog
- Propose from highest-VALUE items up to 16pts
- Skip stale check (nothing to be stale against)

### Full Backlog (50+ Items)
If backlog has 50+ items:
1. Run stale checks first to cull candidates
2. Filter to items with `:VALUE:` = Essential or Important
3. Apply ranking only on the filtered set
4. Note: "{N} Nice-to-have items excluded by filter"

### Empty Backlog
If no backlog items exist:
1. Check if all items are in the current sprint (overcommitted)
2. Check if any EPICs are incomplete and need stories
3. Suggest creating new stories from gbrain project pages
4. Output: "Backlog is empty. Consider creating stories from gbrain project goals."

### Personal Sprint Planning (FULL MODE)
When Coy explicitly asks about personal sprint planning (outside work hours), also include:
```bash
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/personal/personal.org --sprint "backlog"
```
Personal and work items should be presented as SEPARATE proposals. Do not mix them in the same sprint — they use different velocity tracking.

---

## Relationship to Other Skills

| Skill | Relationship |
|-------|-------------|
| **sprint-retro** | Generates reports about the past. Planning skill reads those retro pages (from gbrain) for lessons. |
| **coy-sprint** | Provides the underlying org tools (`org_query.py`, `parse_backlog.py`). Planning skill orchestrates them. |
| **gbrain-query** | Searches for sprint patterns. Planning skill imports gbrain context into proposals. |
| **coy-sprint-inbox-triage** | Triage refines inbox → backlog. Planning skill reads from backlog. Pipeline: Inbox → Triage → Backlog → Sprint Planning. |

## See Also

- gbrain `concepts/sprint-planning-skill` — design document and scope
- gbrain `concepts/sprint-retro-format` — retro format (lessons flow to planning)
- gbrain `concepts/sprint-date-derivation` — boundary computations
- gbrain `concepts/org-triage-backlog-default` — why items default to backlog
- gbrain `concepts/phase4-sprint-intelligence-plan` — parent implementation plan
- `coy/sprint-retro/SKILL.md` — retro skill (sister skill)
- `coy/coy-sprint/references/org-sprint-plan.md` — sprint planning reference
- `coy/coy-sprint/references/org-retro-and-stale.md` — stale detection reference
- `coy/coy-sprint/SKILL.md` — sprint system overview
