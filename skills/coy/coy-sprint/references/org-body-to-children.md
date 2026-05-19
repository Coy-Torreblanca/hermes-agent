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
