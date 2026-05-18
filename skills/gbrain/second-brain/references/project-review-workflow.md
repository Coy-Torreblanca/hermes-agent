# Project Review Workflow (Brain + Org)

When the user asks to "review [project] goals and todos" or get a comprehensive overview of a project's planned features, use this dual-query pattern to combine brain knowledge with org task state.

## Workflow

### Phase 1: Brain — Gather Vision & Context

Search the brain for all concept/idea pages related to the project. Use multiple search strategies in parallel:

1. **Keyword search** for the project name across all page types
2. **Semantic query** for related concepts (strategy, vision, architecture)
3. **Get full pages** for any vision/concept pages found (e.g., `wiki/concepts/holy-bible-project`, `concepts/three-project-strategy`)
4. **Search for related context** — life direction pages, goals pages, trip goals, any page that describes the project's strategic role

The brain holds the **what and why**: vision, goals, features list, architecture decisions, and strategic context.

### Phase 2: Org — Get Task State

Load `coy-sprint` skill and use `org_query.py` to query the org files for task-level detail:

1. **Find project EPIC**: `--find-epic "<project name>"` — returns the EPIC heading, properties (GOAL, SPRINT, VALUE), and top-level body
2. **Get children**: `--children-of "<epic name>"` — returns all stories, sub-EPICs, and TODOs nested under the epic
3. **Check icebox**: Repeat find-epic with "[ICEBOX]" suffix — e.g., `--find-epic "<project name> [ICEBOX]"`
4. **Check backlog items**: `--sprint "backlog"` — filter for items whose title or parent contains the project name
5. **Check active sprint**: `--sprint <current_sprint>` — filter for project items in the active sprint
6. **Drill into specific items**: `--heading "<exact heading title>"` — get full body text, properties, parent context for each item found

The org files hold the **what and when**: concrete features, point estimates, sprint assignments, acceptance criteria in body text, and hierarchy (EPIC → STORY → TODO).

### Phase 3: Synthesize

Combine both sources into a structured overview:

- **Vision** (from brain): project purpose, long-term architecture, strategic role
- **Active sprint items** (from org): what's being worked on now
- **Backlog** (from org): planned but unstarted features
- **Icebox/deferred** (from org): future or aspirational features
- **Brain-only features** (from brain): features mentioned in concept pages but not yet broken into org tasks — these signal undecomposed scope
- **Strategic alignment**: how this project fits into the user's broader goals (life-direction, three-project-strategy, saas-builder-capability)

### Common Drill Path

For a full picture of any project EPIC:

```
1. brain: search "<project>" → get concept/vision pages
2. brain: search related concepts → get strategic context
3. org: --find-epic "<Epic Name>" → EPIC header + properties
4. org: --children-of "<Epic Name>" → feature breakdown
5. org: --find-epic "<Epic Name> [ICEBOX]" → deferred ideas
6. org: for each child, --heading "<title>" → body text with acceptance criteria
7. org: --sprint "backlog" | grep -i "<project>" → orphan items
8. org: --sprint <current> | grep -i "<project>" → active items
```

## Pitfalls

- **Brain pages can be stale.** Check `updated_at` timestamps — a brain page last updated in April may describe plans that have since been restructured in the org files. The org file is the operational source of truth.
- **Org EPICs don't always have matching brain pages.** A project may have detailed task breakdown in org but no corresponding brain concept page. In that case, the org file IS the full picture.
- **Inverse: brain-only features.** Features described in brain concept pages may never have been broken into org tasks. Flag these as "undecomposed scope" — they're aspirations, not commitments.
- **Icebox items may still have full body text** with rich context (source articles, implementation notes). Always drill into icebox stories with `--heading` to check for this.
- **Backlog items may be orphaned** — TODOs without a parent STORY or STORYS without a parent EPIC. The `--sprint "backlog"` query returns everything in backlog regardless of hierarchy, so cross-reference against the EPIC's known children.

### Bonus: Story Completion Audit (STORY-Level Drill)

When the user asks "are we done with X story" or wants a completeness check on a specific STORY (not an EPIC), use this deeper drill pattern that emerged from the TODO & Sprint Management audit (2026-05-16):

1. **Load the STORY**: Use `--heading "Exact Story Title"` or `--children-of "Exact Story Title"` via execute_code (shell special chars like `&` break terminal commands — use Python subprocess)
2. **Get the GOAL** from the STORY's `:PROPERTIES:` — this is the canonical definition of done
3. **Map each child** against the GOAL statement:
   - For each child STORY/TODO: what phase of the GOAL does it cover?
   - Is it DONE? STORY-STARTED? STORY (not started)?
4. **Cross-reference against gbrain page**:
   - Does the gbrain page describe features that aren't in the org children? → undecomposed scope
   - Does the gbrain page have stale stats, status fields, or counts? → flag drift
   - Does the gbrain page say something is "missing" that's actually delivered? → update
5. **Check for state transitions**:
   - Were any children just marked DONE this session? Note the timestamp
   - Was anything promoted/demoted between sprints?
6. **Identify unresolved items**:
   - Children with "should" language in body text (aspirational, not actionable)
   - STORYS with empty body text (scope undefined)
   - TODOs under no STORY parent (orphans)
7. **Synthesize** as a requirements table:

```
| Requirement | Status | Evidence |
|-------------|--------|----------|
| CRUD todos | ✅ | --create-todo live, tested |
| Habit CRUD | ✅ | habit_query.py, all CRUD |
| Sprint retro | ❌ | Phase 4, not started |
```

Then answer: "The story GOAL is X%. Here's what's delivered, what's partial, and what's missing."

**Pitfall — shell special chars in titles.** Titles with `&`, `|`, `>`, `<` will silently fail in terminal commands. Use `execute_code` with Python `subprocess.run(["python3", script, args...])` to bypass shell parsing.

## Example Output Structure

```
# 📖 Project Name — Complete Overview

### Vision (from brain)
<project purpose, architecture, strategic role>

### Active Sprint
<none or items with state>

### Backlog Items
| Item | Type | Pts | Value |
|------|------|:---:|:-----:|
| Feature A | STORY | 3pt | High |

### Icebox / Deferred
| Item | Pts | Goal |
|------|:---:|------|

### Brain-Only Features (not in org)
- <features mentioned in brain but not taskified>

### Strategic Alignment
<how this project fits into broader goals>
```
