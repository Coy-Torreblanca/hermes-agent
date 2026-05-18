# Bulk EPIC Reparenting Workflow

When Coy asks to move multiple items between EPICs (e.g., promote backlog items to current sprint, defer items to a new ICEBOX EPIC, or re-parent orphaned stories), follow this workflow:

## Phase 1: Diagnose (org_query.py)

Before touching the file, understand the structure:

```bash
# Get all children of the source EPIC (shows titles, keywords, sprint, line numbers)
python3 ~/.hermes/scripts/org_query.py tasks.org --children-of "Source EPIC Name"

# Get exact content and boundaries of each item to move
python3 ~/.hermes/scripts/org_query.py tasks.org --heading "Item Title"

# Find the target EPIC's structure
python3 ~/.hermes/scripts/org_query.py tasks.org --find-epic "Target EPIC Name"

# Verify target has no existing items if creating new
python3 ~/.hermes/scripts/org_query.py tasks.org --children-of "Target EPIC Name"
```

## Phase 2: Execute (Raw Python File I/O)

**Use `open()` directly to read/write — never `read_file` (has session dedup that returns stale state).**

```python
# READ: open the file fresh
with open('/data/syncthing/Sync/org/work/tasks.org', 'r') as f:
    lines = f.read().split('\n')

# EXTRACT: collect blocks to move using line ranges from org_query.py
blocks_to_move = [lines[start:end] for start, end in ranges]

# REMOVE: delete from source (reverse order to preserve indices)
for start, end in reversed(sorted_ranges):
    del lines[start:end]

# CREATE/INSERT: find insertion point, add new EPIC/items
new_block_lines = [new_epic_header, ...] + [''] + blocks_text
lines = lines[:insert_at] + new_block_lines + lines[insert_at:]

# WRITE
with open('/data/syncthing/Sync/org/work/tasks.org', 'w') as f:
    f.write('\n'.join(lines))
```

**Key rules:**
- Process removals in reverse order (highest line number first) so deletions don't shift later indices
- Insert at a top-level `*` heading boundary to ensure correct parentage (not after body text)
- Use `org_query.py --validate` afterward to catch structural issues
- Verify with `org_query.py --children-of "EPIC Name"` on both source and target

## Phase 3: Verify

```bash
# Validate all rules (WIP, orphans, hierarchy violations)
python3 ~/.hermes/scripts/org_query.py tasks.org --validate

# Verify source EPIC no longer has moved items
python3 ~/.hermes/scripts/org_query.py tasks.org --children-of "Source EPIC"

# Verify target EPIC has the moved items
python3 ~/.hermes/scripts/org_query.py tasks.org --children-of "Target EPIC"

# Quick spot-check: are the moved items in the right sprint?
grep -n 'SPRINT:' tasks.org | grep -i "Item Name"
```

## Structural Decision: Top-Level Epic vs Sub-Epic

Before proposing a new EPIC, verify whether it should be a **child of an existing EPIC** or a new top-level EPIC.

**Rule of thumb:**
- If the new EPIC is a *feature or component* of an existing project → **sub-EPIC** (`** EPIC <name>` under `* EPIC Parent`)
- If the new EPIC is an entirely independent initiative → **top-level EPIC** (`* EPIC <name>`)

**Example from May 17, 2026 correction:** Personal Note System was proposed as a new top-level EPIC. User corrected: it belongs as `** EPIC Personal Note System — MVP :personal:` under the existing `* EPIC My Holy Bible v1`. [Source: User correction, Discord, 2026-05-17]

When in doubt, check the existing EPIC hierarchy first with `python3 ~/.hermes/scripts/org_query.py tasks.org --epics` and consider whether the new work is a component of an existing initiative before creating a new top-level heading.

## Tagging New Sub-EPICs

When creating sub-EPICs that belong to a personal/side domain, tag them appropriately. Personal-use items (not for public deployment, not work-related) get `:personal:`. Convention from the coy-sprint skill: "Tags: Reserve tags exclusively for defining domains of work or contexts (e.g., `:personal:`, `:tooling:`, `:development:`)."

## Common Pitfalls

- **🎯 Always load `coy-sprint` skill first** — don't start hacking on the org file directly. The skill has pitfalls, reference files, and the canonical org_query.py script. If you find yourself writing raw Python file I/O without the skill loaded, stop and load it first. The skill may have a pitfall or reference that saves you from a bug.
- **Don't mix insertion targets.** Bulk-moving items to a new EPIC and also to an existing EPIC in the same pass requires two separate insertions.
- **TODO-level items need a STORY parent.** If items at `** TODO` level exist at the EPIC's root, they're orphans. Wrap them under a `** STORY` during reparenting.
- **Don't skip `--validate`.** The org file has 42+ rules that can be silently violated by bulk edits. Always validate after.
- **Syncthing syncs immediately.** A corrupt write hits Coy's Emacs within seconds. Always write to a temp file first and validate before replacing if doing risky operations.

## Concrete Example: Defer 11 Backlog Items to New ICEBOX EPIC

From the May 16, 2026 session — 11 items moved from "Personal AI v1" (SPRINT:4) to new "Personal AI v2 [ICEBOX]":

1. `--children-of "Personal AI v1"` → identified backlog items by their SPRINT:backlog
2. `--heading "Food & Health Tracker"` → got exact line range (608-621)
3. Repeated for all 11 items to get precise 0-indexed ranges
4. Extracted blocks via `original[start:end]` slice
5. Deleted from original in reverse order
6. Built new EPIC header + inserted all blocks before `* STORY Clean up git repositories`
7. `--validate` → confirmed no new issues beyond pre-existing ones
8. `--children-of "Personal AI v2"` → confirmed all 11 items present
