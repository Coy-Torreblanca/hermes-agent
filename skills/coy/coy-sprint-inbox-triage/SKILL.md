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

## Cardinal Rule: Default Sprint Placement

**New inbox items go to backlog or next sprint — NOT the current sprint — unless they are urgent or Coy explicitly requested them for the current sprint.**

| Condition | Sprint Assignment |
|-----------|------------------|
| Default (no urgency signal) | `:SPRINT: backlog` |
| Clearly needed soon but not urgent | `:SPRINT: N+1` (next sprint) |
| Urgent (blocking, breaking, time-critical deadline) | Present as sprint candidate with rationale |
| Coy explicitly said "put in current sprint" | `:SPRINT: current N` — no further justification needed |

**🚨 Do not infer urgency from topic or priority cookie alone.** "Important" or `[#A]` does not mean "sprint now." The triaged item must be genuinely blocking or time-bound.

**Exception:** If the parent EPIC has a numeric sprint (e.g., SPRINT: 4) and the item must live under it, the sprint hierarchy invariant (child ≤ parent) may force the child into that sprint. In that case:
1. Note the forced adjustment explicitly in the proposal: `(SPRINT adjusted to 4 to match parent EPIC hierarchy)`
2. Flag it for Coy's attention — he may want to move the item to a different EPIC instead

See [[concepts/org-triage-backlog-default]] for the full rationale. [Source: User, Coral, 2026-05-18]

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

#### Pass A.5: ICEBOX Sibling Routing (Detour Check)

After scoring EPICs, check if the highest-scoring EPIC has an **ICEBOX sibling** EPIC (same umbrella concept, `[ICEBOX]` suffix in title). Example: `Personal AI v1` (active, Sprint 4) has `Personal AI v2 [ICEBOX]` (backlog) as a sibling.

Route the item to the ICEBOX sibling when:
- The item is a **non-urgent improvement or housekeeping task** that conceptually relates to the active EPIC's domain
- The active sprint is already full or near-full (capacity concerns)
- Coy hasn't explicitly said "put this in the current sprint"

Decision logic:
1. If the active EPIC has an ICEBOX sibling EPIC → propose the ICEBOX sibling as destination
2. Flag in the proposal: `(routed to ICEBOX sibling — non-urgent, active sprint full)`
3. Only use the active EPIC as destination if the item is urgent/time-critical or Coy explicitly assigned it there
4. See gbrain `concepts/org-triage-backlog-default` for the backlog-default rationale, and the ICEBOX Protocol in `wiki/sources/org-work-summary`
[Source: User, Discord, 2026-05-18]

#### Pass D: Sprint Hierarchy Validation via `--dry-run` 🚨 MANDATORY

After determining the parent EPIC, points, value, and sprint for a non-inbox item, run `org_query.py --dry-run` with the exact params you intend to propose. This validates the sprint hierarchy invariant automatically and catches errors BEFORE presenting to Coy.

**Procedure:**

1. Build the JSON params for the proposed insertion (same shape as `--create-todo`):
   ```json
   {
     "title": "Story Title",
     "body": "Body text...",
     "destination": "EPIC Name",
     "keyword": "STORY",
     "points": 3,
     "value": "Important",
     "sprint": "backlog"
   }
   ```

2. Run dry-run validation:
   ```bash
   org_query=/data/.hermes/scripts/org_query.py
   python3 "$org_query" --dry-run '{"title":"...","body":"...","destination":"EPIC Name","keyword":"STORY","points":3,"value":"Important"}'
   ```

3. **Interpret the result:**
   - If `"action": "rejected"` with `"error"` containing "Sprint hierarchy violation" → **SPRINT mismatch.** The child's sprint is incompatible with the parent EPIC's sprint. **Fix:** Adjust the child's sprint to match the parent EPIC's sprint, then re-run the dry-run to confirm.
   - If `"action": "rejected"` with other error → **Other validation failure.** Flag the issue in the proposal and present both the proposed params and the error.
   - If no `"error"` field → ✅ **Valid.** Proceed with the proposal as-is.

4. **Always adjust before presenting.** Never propose an item to Coy that would fail dry-run validation. The proposal must be pre-validated.

5. **Flag adjustments in the proposal text:**
   ```
   (SPRINT adjusted from backlog to 4 to match parent EPIC "Personal AI v1")
   ```

**Example fixing flow — backlog item under Sprint 4 EPIC:**
```
Proposed: {'title':'Fix gbrain org split','destination':'Personal AI v1','sprint':'backlog'}

→ Dry-run result: REJECTED — Sprint hierarchy violation:
  Child has SPRINT: backlog but parent "Personal AI v1" has SPRINT: 4.
  Child must be planned in sprint 4 or earlier.

→ Adjust: change sprint to 4 to match parent

→ Re-run dry-run: ✅ VALID

→ Present: "→ tasks.org > Personal AI v1 > ** STORY Fix gbrain org split
   :SPRINT:   4  (adjusted from backlog to match parent)
   ..."
```

**Why this matters (CoyDiego correction, 2026-05-18):** Without dry-run validation before presenting, the triage skill proposes insertions that violate the sprint hierarchy invariant. Coy discovers the rule violation instead of the agent catching it proactively. Running `--dry-run` on every proposed EPIC insertion before presenting is the gate that keeps proposals rule-compliant.

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

### Phase 6: Rotate Daily Habits (including sprint_habits.org)

After Coy approves moves and refiling is complete, explicitly rotate the **Daily Org Triage** habit (lives in `sprint_habits.org`, not the default personal habits file):

1. Check the sprint habits file for the Daily Org Triage habit:
   ```
   SPRINT_HABITS=/data/syncthing/Sync/org/work/sprint_habits.org
   python3 ~/.hermes/scripts/habit_query.py "$SPRINT_HABITS" --due-today
   python3 ~/.hermes/scripts/habit_query.py "$SPRINT_HABITS" --overdue
   ```
2. Present the Daily Org Triage habit to Coy for toggle:
   ```
   🔄 SPRINT HABIT:
   - Daily Org Triage (📆 ${status}) — toggle now that refile is done? (y/n)
   ```
3. When Coy approves, toggle it:
   ```
   python3 ~/.hermes/scripts/habit_query.py "$SPRINT_HABITS" --toggle "Daily Org Triage"
   ```
4. Also check personal habits for Coy convenience:
   ```
   python3 ~/.hermes/scripts/habit_query.py --due-today
   python3 ~/.hermes/scripts/habit_query.py --overdue
   ```
   Present for toggle approval if anything is due/overdue:
   ```
   🔄 HABITS:
   - Due today: 📖 Morning Prayer — toggle? (y/n)
   - Overdue: 🙏 Bible Study (2 days) — catch up?
   ```

5. Include in final summary:

   ```
   ✅ Inbox triage + habit rotation complete:
   - Moved to tasks.org: N items
   - Moved to personal.org: N items
   - Created new EPICs: N
   - Removed from inbox: N items
   - Needs context: N items (flagged)
   - 🔄 Daily Org Triage toggled (refile complete)
   - 🔄 Other habits: N (toggle titles)
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
