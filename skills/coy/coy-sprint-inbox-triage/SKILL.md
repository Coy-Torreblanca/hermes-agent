---
name: coy-sprint-inbox-triage
description: Batch inbox triage for Coy's sprint system — reads all inbox items, applies auto-project detection (EPIC scoring), auto-point estimation (hours→points table), context enrichment (ask if unsure), presents all proposals as one org-text block, executes approved moves in batch, and rotates daily habits. Phase 3 Inbox Intelligence.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [coy, sprint, triage, inbox, refile, batch, Phase3]
    related_skills: [coy-sprint]
---

# Coy Sprint Inbox Triage

> **Phase 3: Inbox Intelligence** — Created 2026-05-16 per CoyDiego specifications.

Batch inbox triage skill. Reads all inbox items in one pass, applies auto-inference for project (EPIC), points, and context, then presents everything as a single org-text proposal block. Coy approves per-item, then all moves execute in one batch.

## When to Use

- Coy says "triage my inbox", "refile these", "clean up inbox"
- Coy says "present all inbox items"
- After a capture burst with multiple items
- As part of daily briefing / morning routine

## Pre-Flight

Before beginning triage, understand the per-item workflow by reading:

```
read_file /data/.hermes/skills/coy/coy-sprint/references/org-triage.md  — base per-item workflow (concepts, not a load target)
read_file /data/.hermes/skills/coy/coy-sprint/references/org-capture.md  — property format
read_file /data/syncthing/Sync/org/work/tasks.org  — for EPIC list
```

## Workflow

### Phase 1: Read All Inbox Items (single pass)

```
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/inbox.org --summary
```

Then read the full inbox content to get body text and properties for each item. Use `open()` directly via execute_code to bypass `read_file` dedup if the file was already read this session.

Extract: heading, keyword, priority, body text, all `:PROPERTIES:`.

### Phase 2: For Each Item — Apply Auto-Inference

For every non-DONE item in inbox, run the three inference passes:

#### Pass A: Auto-Project Detection (Task 1)

1. Extract key terms from item title + body (strip stopwords, keep nouns and product names)
2. Get all EPICs: `org_query.py --epics`
3. Score each EPIC by keyword overlap:
   - Substring match on EPIC title → high score (e.g., "30ai" in title matches "Set up 30ai workers")
   - Partial keyword overlap → medium score
   - No match → low score
4. **Decision logic:**
   - **High score** (≥ ~50% term overlap): propose as parent EPIC — `→ tasks.org > * EPIC Name`
   - **Low score but task is multi-faceted** (project-level scope like "build X system", "implement Y pipeline", "design Z feature list"): propose creating a new EPIC — `→ tasks.org > * NEW EPIC [proposed name] [ICEBOX]`
   - **Low score and task is a simple one-off** (install a tool, fix a bug, configure a setting, read a doc, small refactor): propose as top-level `** STORY` under the nearest umbrella EPIC, or standalone if no umbrella fits
5. **Never present low-score item as "no EPIC found" without a clear proposal.** Always recommend one of the three outcomes above.

#### Pass B: Auto-Point Estimation (Task 2)

1. Read the task description
2. Estimate the **hours** it would take to complete (genuine estimation, not trigger-word mapping)
3. Map to the canonical Points→Hours table:

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

4. Propose as `:POINTS: N` in the properties drawer
5. If genuinely can't estimate (too vague), propose points as 1 (default) and flag "rough estimate — verify"

#### Pass C: Context Enrichment (Task 3)

1. If body is < 50 chars (thin):
   - Look at title, referenced skill paths, referenced projects, your knowledge — can you fill in meaningful body context?
   - **If yes:** add inferred body with flag `(context inferred — verify)`
   - **If no:** flag `⚠️ Thin context — can you elaborate?`
2. If body ≥ 50 chars: leave as-is (context is sufficient)
3. **Never hallucinate.** If you don't have the information, don't make it up. Ask Coy.

#### Pass D: Sprint Hierarchy Check (Sprint Invariant)

After determining the parent EPIC and proposed SPRINT, validate the sprint hierarchy:

1. **Get the parent EPIC's SPRINT** from `org_query.py --epics` or `--find-epic`
2. **Enforce the invariant:** child SPRINT must be ≤ parent SPRINT
   - If parent has SPRINT: 4 and child is SPRINT: backlog → ❌ REJECT. Child must be planned in sprint 4 or earlier.
   - If parent has SPRINT: 4 and child is SPRINT: 4 → ✅ OK.
   - If parent has SPRINT: 4 and child is SPRINT: 3 → ✅ OK (child completes before parent).
   - If parent has SPRINT: backlog → no constraint (unplanned parent can't constrain child).
3. **If violated:** adjust the proposal to match the parent's sprint, or propose a different parent EPIC with a compatible sprint. Flag the adjustment in the proposal text: `(SPRINT adjusted from backlog to 4 to match parent)`
4. **The `--create-todo` command enforces this automatically** — if you forget this check, the script will reject the insertion with a clear error.

### Phase 3: Present All Proposals (single block)

Format as a single message:

```
📥 INBOX TRIAGE — N items

Item 1: "Title"
→ tasks.org > * EPIC Name > ** STORY Title
:PROPERTIES:
:POINTS:   N
:VALUE:    Critical|High|Medium
:SPRINT:   backlog|N
:END:
Body: <truncated or enrichment note>
Flags: ⚠️ Thin context

Item 2: "Title"
→ personal.org > ** STORY Title
:PROPERTIES:
:POINTS:   N
:VALUE:    Medium
:SPRINT:   backlog
:END:
Body: <context>

Item N: "Title"
→ tasks.org > * New EPIC [Proposed Name] [ICEBOX]
:PROPERTIES:
:POINTS:   N
:VALUE:    High
:END:
Body: <context>

Approve per-item or adjust. I'll batch-execute the confirmed moves.
```

**Crucial:** Strip NOTHING from body text. Coy needs full context to evaluate the proposal.

### Phase 4: Execute Approved Moves (batch)

For each approved item:

1. Use `org_query.py --create-todo` with the approved params (destination EPIC, points, value, etc.)
2. 🚨 `--create-todo destination:"EPIC"` does NOT auto-remove from inbox — the source item remains

### Phase 5: Final Cleanup

1. After all moves executed, do a final inbox pass: read inbox.org, identify items that were moved (heading match), remove them
2. Clean up any DONE items from inbox
3. Verify: read tail of destination files to confirm items landed correctly

### Phase 6: Rotate Daily Habit

After triage is complete, also rotate Coy's daily habit:

1. Check what's due today:
   ```
   python3 ~/.hermes/scripts/habit_query.py --due-today
   python3 ~/.hermes/scripts/habit_query.py --overdue
   ```
2. Present to Coy:
   ```
   🔄 HABITS:
   - Due today: 📖 Morning Prayer — toggle? (y/n)
   - Overdue: 🙏 Bible Study (2 days) — catch up?
   ```
3. For each habit Coy approves, toggle it:
   ```
   python3 ~/.hermes/scripts/habit_query.py --toggle "Habit Title"
   ```
4. Include in final summary:

   ```
   ✅ Inbox triage + habit rotation complete:
   - Moved to tasks.org: N items
   - Moved to personal.org: N items
   - Created new EPICs: N
   - Removed from inbox: N items
   - Needs context: N items (flagged)
   - 🔄 Habits rotated: N (toggle titles)
   ```

## Pitfalls

- **Never hallucinate context.** If you can't reliably add context, flag it — don't make up task details
- **Points come from hours estimation, not trigger words.** "Set up X" is not always 1 pt — it depends on complexity. Estimate honestly.
- **Low score for EPIC match doesn't mean "no parent."** Always recommend one of: existing EPIC, new EPIC, or top-level STORY
- **One-off tasks (install, fix, configure) don't warrant new EPICs.** Propose under nearest umbrella or standalone
- **Line-number corruption:** never `read_file` → extract → write. Use `org_query.py --create-todo` for creation, raw file I/O for removal
- **read_file dedup:** `read_file` on inbox.org returns stale "unchanged" if called twice in same session. Use `open()` directly via `execute_code` for fresh reads after writes
- **Always remove source from inbox after move.** `--create-todo destination:"EPIC"` leaves the inbox item intact. This is the most common triage bug. Do a final cleanup pass.

## See Also

- `coy-sprint/references/org-triage.md` — base triage workflow (updated for batch integration)
- `coy-sprint/references/org-capture.md` — capture property format
- `coy-sprint/SKILL.md` — points reference table, full sprint management
- [[projects/personalai/todo-sprint-management]] — Phase 3 project page
