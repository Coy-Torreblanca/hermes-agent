# Org Triage (absorbed from org-triage skill)

The Manager half of Maker/Manager. Reads inbox.org, proposes destination + hierarchy + metadata for each item, then moves approved items to their permanent home. Mirrors what `C-c C-w` + the linter does in Emacs.

## Before You Start: Batch Triage Is in a Dedicated Skill

For **batch triage with auto-inference** (project detection, point estimation, context enrichment), use the dedicated skill instead of this reference file:

```
skill_view(name="coy-sprint-inbox-triage")
```

That skill implements all Phase 3 Inbox Intelligence features:
- **Auto-project detection** — scores EPIC keywords, proposes best parent (or new EPIC if warranted)
- **Auto-point estimation** — estimates hours → maps to canonical points table
- **Context enrichment** — adds context where possible, asks where not
- **Batch presentation** — all items in one proposal block
- **Batch execution** — approved moves run in one pass with final inbox cleanup

This reference file documents the base per-item workflow. The **inbox triage skill references this file** for its per-item foundation — it's the base layer, not the orchestrator. For daily triage, load the batch skill directly; use this reference only when you need to understand the underlying per-item logic.

## When to Use

- Coy says "triage my inbox", "refile these", "clean up inbox"
- After a capture burst — move items to permanent files
- Daily grooming (morning briefing triggers this)
- **Prefer loading `coy-sprint-inbox-triage` skill for batch operations**

## Process (per item)

### 1. Read the landscape
Read `/data/syncthing/Sync/org/inbox.org` for uncategorized items. Read `/data/syncthing/Sync/org/work/tasks.org` for existing EPIC/STORY hierarchy. Read `/data/syncthing/Sync/org/personal/personal.org` if personal items exist.

### 2. For each TODO without DONE

**Parent decision:**
- **ALWAYS check tasks.org first** for existing EPICs/STORYs — even for personal-topic items. Trip goals, personal projects, and side-work often have EPIC homes in the work board (e.g., Bible site EPIC, Personal AI EPIC). Don't assume "personal topic = personal.org."
- Only route to personal.org if NO relevant EPIC/STORY exists in tasks.org AND the item is purely personal (health, family logistics, household, shopping)
- If a relevant EPIC exists: place under it as a child STORY or TODO
- If no good parent exists anywhere, determine: should this become a new STORY (multi-step) or EPIC (major initiative)?

**Priority:**
- `[#A]` — urgent, blocking, or time-sensitive
- `[#B]` — important, should do this sprint
- `[#C]` — nice to have, backlog

**Body context:**
- Preserve existing body text — Coy needs it to remember what the task is about
- If body is too thin (bare headline), enrich with context from the conversation that spawned it
- Strip nothing — context loss during triage is irreversible

**Sprint placement:**
| **⚠️ Default to backlog.** New items go to backlog or next sprint — NOT the current sprint — unless urgent or explicitly requested for current sprint. See gbrain [[concepts/org-triage-backlog-default]].

- Current sprint: if critical + capacity allows (≤ 16 pts total when added)
- Backlog: if non-critical OR sprint is full
- Consider existing sprint load before committing

**Metadata proposal:**
- POINTS: Fibonacci (1, 2, 3, 5, 8, 13, 21) per the point-to-hour table
- VALUE: Critical, High, Medium, or Low
- SPRINT: current sprint number or `backlog`

### 2b. 🚨 Dry-run validation (before presenting)

Before presenting any proposal that inserts a STORY/TODO under an EPIC in tasks.org, run `org_query.py --dry-run` with the exact params:

```bash
org_query=/data/.hermes/scripts/org_query.py
python3 "$org_query" --dry-run '{"title":"...","body":"...","destination":"EPIC Name","keyword":"STORY","points":3,"value":"Important","sprint":"backlog"}'
```

- If result has `"action": "rejected"` with sprint hierarchy error → adjust child SPRINT to match parent sprint, re-run dry-run
- If result is error-free → ✅ safe to present
- **Never present a proposal that would fail dry-run validation.** The proposal must be pre-validated.

Flag any adjustments in the proposal text: `(SPRINT adjusted from backlog to 4 to match parent)`

### 3. Present proposal
Show the exact org text that will be written — full properties drawer, priority cookie, body, hierarchy. Present parent assignment.

### 4. Coy confirms or adjusts

### 5. Execute move
Delete from `/data/syncthing/Sync/org/inbox.org`, append to destination file under correct parent.

### 6. Cleanup
Remove DONE items from `/data/syncthing/Sync/org/inbox.org` after triage.

## Routing Rules

| Capture method | Already in | Triage action |
|---|---|---|
| `C-c c i` (Quick Inbox) | `/data/syncthing/Sync/org/inbox.org` | Route to tasks.org or personal.org |
| `C-c c w` (Work) | `/data/syncthing/Sync/org/inbox.org` | Route to tasks.org under EPIC/STORY |
| `C-c c t` (Task w/ metadata) | `/data/syncthing/Sync/org/inbox.org` | Route + verify metadata |
| `C-c c p` (Personal) | `/data/syncthing/Sync/org/personal/personal.org` | Already in place — skip routing |
| Hermes `org-capture` | inbox.org | Full triage needed |

## Metadata Rules

- **TODO children inherit** POINTS/VALUE/SPRINT from parent STORY — don't duplicate
- **STORY/EPIC** get full metadata: POINTS, VALUE, SPRINT, GOAL
- **0 pts**: ≤1 hr quick fix. **1 pt**: 1-3 hrs. **2 pts**: 3-5 hrs. **3 pts**: 5-8 hrs.
- **Capacity**: max 16 pts/sprint. Warn if committing would exceed.
- **VALUE**: Critical > High > Medium > Low

## Sprint Hierarchy Invariant (MANDATORY)

**Rule:** A child's SPRINT must be ≤ its parent's SPRINT (child completes before or at same time as parent).

- Backlog child under a numeric-sprint parent → **INVALID**. The child must be planned in the same sprint or earlier.
- Numeric child under backlog parent → **OK** (unplanned parent can't constrain).
- Same sprint → **OK**.
- Child sprint < parent sprint → **OK** (child completes first).

This is enforced by `org_query.py --create-todo` — it will **reject** any insertion that violates the invariant with a clear error message. The `--validate` flag also checks the entire hierarchy and reports violations.

During triage: if you propose an item under a parent with an incompatible sprint, adjust the child's SPRINT to match the parent, or choose a different parent.

## Implementation

Move items with Python heredoc pattern via terminal — never `read_file` → extract → write (causes line-number corruption). See `references/refile-script-pattern.md`.

Remove from inbox with sed (delete lines by pattern match on heading + body).

## Pitfalls

- **Never move without confirming** — Coy needs to see the exact org text first
- **Don't strip body context** — a bare headline in tasks.org is useless months later
- **Check capacity before committing to sprint** — count existing sprint points first
- **Personal items from `C-c c p` are already routed** — they're in personal.org, not inbox
- **Line number corruption** — never extract via `read_file` and write to another file without stripping line prefixes
- **DONE items in inbox are historical record** — remove them during cleanup, not as part of individual item moves
- **Don't default to personal.org for personal-topic items** — trip goals, personal projects, and side-work often have EPIC homes in tasks.org (e.g., Bible site, Personal AI). Always search tasks.org for relevant EPICs before proposing personal.org as destination.
