# Converting Body Text to Org Children

When a STORY or TODO has sections/requirements as raw body text (markdown bullet points, numbered sections, etc.), each section likely represents a distinct work item that should be a proper `****` child.

## When to Use

- A STORY's body contains `=== Section ===` headings, `- bullet point` lists, or numbered requirements
- You need to mark some items DONE and leave others as TODO
- You want items to be trackable via `--children-of`, `--find-active`, or `--sprint`

## Workflow

### Step 1: Assess the Sections

Identify which body sections represent distinct work items vs. descriptive text:

| Body Pattern | Likely Children | Keep in Body |
|-------------|----------------|--------------|
| `=== 1. Thing ===` then bullet points | ✅ Each section is a child | Summary line only |
| `- Requirement 1`, `- Requirement 2` | ✅ If each is independently completable | Descriptive intro |
| `- Note: this depends on X` | ❌ Not a work item | Keep as body |
| Plain paragraph explaining the feature | ❌ Description | Keep as body |

### Step 2: Check Status of Each Section

For each work-item section, determine:
- **DONE**: If the feature described in those bullets has been implemented
- **TODO**: If it hasn't been started
- **Being enriched**: If the user wants to redefine the scope (happens during triage)

### Step 3: Generate the Children

Each child gets:
- Proper keyword (`TODO`, `DONE`, `STORY`, etc.) — TODOs under a STORY parent don't get :SPRINT: or :VALUE: (inheritance)
- Priority tag if the parent had one, or `[#C]` as default
- `:ID:` — auto-generated 16-char hex UUID
- `:CREATED:` — today in `[YYYY-MM-DD Day]` format
- State transition note for DONE items: `- State "DONE" from "TODO" [YYYY-MM-DD Day]`
- Concise body: the key bullet points from the original section, reworded for clarity

### Step 4: Condense the Parent Body

Replace the detailed body with a one-line summary. The detail lives in the children now.

### Step 5: Verify

Run `org_query.py <file> --children-of "Parent Name"` to confirm all children are in place with correct keywords.

## Example

**Before:**
```
*** STORY [#C] Phase 4: Sprint Intelligence
:PROPERTIES:
:POINTS:   2
:END:

=== 1. Sprint Retrospective Analysis ===
- Completion analyzer: Parse DONE/STARTED/CANCELLED state transitions
- Output: Structured retro report in markdown

=== 2. Smart Backlog Suggestion ===
- Ranking algorithm with VALUE × recency × dependency
- Capacity-aware: respect 16pt cap
```

**After (if section 1 is done):**
```
*** STORY [#C] Phase 4: Sprint Intelligence
:PROPERTIES:
:POINTS:   2
:END:

Sprint retro analysis, stale detection, sprint planning, and lessons-learned.

**** DONE [#C] Sprint Retrospective Analysis
:PROPERTIES:
:ID:       14C96C14FD414608
:CREATED:  [2026-05-18 Mon]
:END:

- Completion analyzer via --retro: point totals, completion ratios, sprint dates
- Output: sprint-retro skill with risk/gap/root cause analysis

- State "DONE" from "TODO" [2026-05-18 Mon]

**** TODO [#C] Sprint Planning Skill
:PROPERTIES:
:ID:       C52C00788DFA4E9B
:CREATED:  [2026-05-18 Mon]
:END:

Hermes skill that automates sprint planning:
- Reads backlog, ranked by VALUE × recency × dependency
- Capacity-aware: respects 16pt cap
```

[Source: CoyDiego, Discord Lab/#secondbrain, 2026-05-18 — phase 4 items converted from body to children]

## Pattern: Prose Sentence Requirements → Implementation Plans

When a STORY body contains plain-prose sentences (not markdown headers or bullet points), each sentence that describes a distinct requirement should become a child TODO with a numbered implementation plan.

### Signal Detection

Look for body text that is:
- 2-5 standalone prose sentences, each describing a distinct work item
- Not structured as markdown (`===`, `- bullets`, numbered lists)
- Each sentence starts with "Any changes to...", "The system should...", or similar requirement language

### Workflow

**Step 1: Identify Requirements.** Each complete sentence that describes one capability or constraint is a candidate. Sentences linked by "and" may need splitting.

**Step 2: Assess Implementability.** If a sentence describes a concrete thing to build/integrate/check, it's a child. If it's a constraint note or context, keep it in the parent body.

**Step 3: Generate numbered implementation plan.** Each child gets:
- `**** TODO` keyword (no :SPRINT: or :VALUE: — inherited from STORY parent)
- `:ID:` — auto-generated 16-char hex UUID
- `:CREATED:` — today in `[YYYY-MM-DD Day]` format
- `:GOAL:` — one-line restatement of the requirement
- `Implementation Plan:` body with 3-6 numbered steps, each a concrete build action
- Numbered steps should be explicit: file paths, tool names (e.g., "pip install orgparse"), existing tools to extend (e.g., "add --validate checks for...")

### Example

**Before:**
```
*** STORY Create a scripts for deterministic org changes
:PROPERTIES:
:ID:       B1B82159-CC6C-447D-9432-AD4515611FDB
:GOAL:     Org changes ensure org syntax and gbrain is updated
:END:

Any changes to an org file needs to run a llm which has context of changes and gbrain tooling with requirement that it updates gbrain.

Any changes to an org file need to be followed up with a org syntax checker to validate that changes were valid.
```

**After:**
```
*** STORY Create a scripts for deterministic org changes
:PROPERTIES:
:ID:       B1B82159-CC6C-447D-9432-AD4515611FDB
:GOAL:     Org changes ensure org syntax and gbrain is updated
:END:

Two post-change hooks: LLM-driven gbrain update on structural changes, and org syntax validator using orgparse + --validate.

**** TODO LLM-driven gbrain update on org changes
:PROPERTIES:
:ID:       A9ED83B358424080
:CREATED:  [2026-05-19 Tue]
:GOAL:     When org-change scripts modify .org files, an LLM pass automatically updates gbrain with context of changes
:END:

Implementation Plan:
1. Design post-change hook architecture
2. Build gbrain update adapter using gbrain page-writer skill
3. Handle diff analysis (new stories, metadata edits, state transitions)
4. Route to LLM via Hermes subagent with gbrain context
5. Auto-classify which changes merit gbrain updates
6. Add audit logging

**** TODO Org syntax checker for post-change validation
:PROPERTIES:
:ID:       B9401435D0F745E2
:CREATED:  [2026-05-19 Tue]
:GOAL:     After any org file change, a validator catches syntax errors before they corrupt the file
:END:

Implementation Plan:
1. Install orgparse (pip) — REQUIRED dependency for AST-based structural validation
2. Build validation layer using orgparse (drawer pairing, heading tree integrity, property correctness)
3. Keep existing org_query.py --validate for business rules (SINGLE WIP, ORPHAN_TODO, etc.)
4. Integrate as automatic post-hook after any org-writing operation
5. Return structured pass/fail with line-level errors
6. Gate on validation — fail the write if invalid
```

### Pitfalls

- **Don't write vague steps.** "Set up validation" is too vague — specify the tool (orgparse), the flag to add (--validate), and what it checks.
- **Don't forget tool choices on iterative correction.** When the user specifies a tool (orgparse, --validate) during feedback, capture it as a REQUIRED dependency in the plan. Don't treat it as optional or subject to revision without user confirmation.
- **Don't skip the :GOAL: field.** Each child needs a one-line GOAL so the sprint dashboard shows what it's for.

[Source: CoyDiego, Discord, 2026-05-19 — deterministic org changes story split into 2 child TODOs with implementation plans]
