---
name: sprint-retro
description: "Generate a full sprint retrospective report with point totals, risk analysis, gap analysis, root causes, and gbrain persistence."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [sprint, retro, analysis, risk, gbrain, lessons-learned, sprint-planning]
    related_skills: [sprint-planning, coy-sprint]
---

# Sprint Retro — Full Analysis Skill

Generates a comprehensive sprint retrospective by combining data from `org_query.py --retro` and `--summary`, computing risk and gap analysis, and saving the report to gbrain.

## When to Use

- Coy says "run sprint retro", "how's the sprint going", "retro analysis"
- At end of sprint (as part of Bi-Weekly Sprint Cleanup)
- Mid-sprint check-in on progress and risk

## Workflow

### Phase 1: Gather Data

```bash
# Get point totals, items, dates, completed list, pain points
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --retro <sprint_number>

# Get active tasks, capacity, velocity
python3 ~/.hermes/scripts/org_query.py /data/syncthing/Sync/org/work/tasks.org --summary <sprint_number>
```

Extract from `--retro` output:
| Field | Meaning |
|-------|---------|
| `sprint` | Sprint number |
| `total_points_committed` | All points scheduled in sprint — **this is the authoritative committed count** (see data interpretation note below) |
| `total_points_completed` | Points actually delivered |
| `completion_by_points` | Points ratio (0..1) |
| `committed` | Item count committed |
| `completed` | Item count done |
| `completion_ratio` | Item ratio (0..1) |
| `velocity_pts` | Same as total_points_completed |
| `blocked_count` / `blocked_items` | Blocked work |
| `completed_items` | What got done, with points per item |
| `pain_points` | What's still in progress |
| `sprint_start` / `sprint_end` | Derived from Bi-Weekly Cleanup habit |

Extract from `--summary` output:
| Field | Meaning |
|-------|---------|
| `active_tasks` | Currently STARTED items |
| `total_items` | Total items in sprint |
| `points_completed` | Same as retro's total_points_completed |
| `capacity_used_pct` | How overloaded the sprint is |

### Phase 2: Compute Risk Assessment

For each risk factor, determine level and provide evidence:

| Risk Factor | HIGH Threshold | MEDIUM Threshold | Evidence |
|------------|---------------|------------------|----------|
| **Overcommit** | `total_points_committed` > 48 (3× cap) | > 32 (2× cap) | Ratio of committed/cap |
| **Attention Fragmentation** | Items span 4+ EPICs | Items span 2-3 EPICs | Count distinct parent titles in pain_points |
| **Completion Velocity** | Completed < 10% of committed pts | 10-30% | completion_by_points |
| **Time Pressure** | Remaining days < remaining_pts / 3 | Remaining days < remaining_pts / 7 | sprint_end - today vs remaining work |
| **Blockers** | 5+ items blocked | 1-4 items blocked | blocked_count |

Risk levels:
- 🔴 **HIGH** — critical. Requires attention or scope cut.
- 🟡 **MEDIUM** — concerning. Monitor and adjust.
- 🟢 **LOW** — under control.

### Phase 3: Build Gap Analysis by EPIC

Group pain_points (items still in progress) by their `epic` field. For each EPIC:
- Count items remaining
- Sum remaining points
- Note if EPIC is at risk of not completing this sprint

### Phase 3.5: Lessons-Learned Integration (gbrain Query)

Before computing gap analysis, enrich the retro by querying gbrain for historical patterns:

```python
# Pseudocode — executed as part of the retro workflow
gbrain_search("sprint retro lessons patterns underestimation")
gbrain_search("sprint retrospective tags")
```

Look for:
- **Recurring underestimation themes**: e.g., "30ai setup took 2x estimated", "infrastructure stories consistently overrun"
- **Repeated pain points**: e.g., "attention fragmentation", "scope creep on EPIC X"
- **Historical velocity**: Compare this sprint's velocity to previous sprints from gbrain retro pages

Format as context injection in the retro report:
```
📚 Lessons From Previous Sprints
- Sprint 3: Infrastructure stories took 2x estimated — consider padding similar items
- Sprint 2: Attention fragmentation across 5+ EPICs caused 40% completion — focus scope
```

**Save retro findings back to gbrain:**
After generating the retro report, update gbrain pages with the sprint's lessons:
- Add timeline entries to `concepts/sprint-retro-format` noting what was learned
- Add timeline entries to related EPIC pages if specific under/overestimation patterns were found
- This builds the knowledge base for future lessons-learned queries

This is the "Lessons-Learned Integration" requirement from Phase 4 Item 3.

### Phase 4: Root Cause Analysis

Check common patterns against the data:
- **Scope overload**: If total_points_committed >> 16pt cap
- **Breadth over depth**: Items spread across many EPICs, no single EPIC close to done
- **Infrastructure creep**: Completed items are all infra/tooling, feature stories untouched
- **Understarted**: Most pain_points are STORY state (not STARTED/NEXT), meaning they were never begun
- **Cancellation rate**: cancelled > 20% of committed

### Phase 5: Format and Save

Output format (follows gbrain concepts/sprint-retro-format):

```markdown
📊 **SPRINT N RETRO — Full Analysis**

## 1. The Numbers
| Metric | Value |
|--------|-------|
| Duration | start → end |
| Points scheduled | X pts |
| Points completed | Y pts |
| Completion by points | X% |
| Items completed | Z/N |
| Velocity | Y pts |

## 2. What's Been Done
- ✅ Item (Npts) — context

## 3. What's Lacking (by EPIC)
- **EPIC Name**: N items, M pts remaining
  - Item 1 (Npts)
  - Item 2 (Npts)

## 4. Risk Assessment
| Risk | Level | Why |
|------|-------|-----|
| Overcommit | 🔴/🟡/🟢 | Evidence |

## 5. Root Causes
- Cause 1
- Cause 2

## 6. Lessons Learned (Saved to GBrain)
- **Recurring pattern**: <description> → carry into next sprint planning
- **Underestimation**: <story type> took <factor>× estimated → adjust points next time
- **What worked**: <practice worth repeating>
- **Action items**: <specific improvement for next sprint>

## 7. Verdict & Recommendations
- Recommendation for remainder of sprint
```

**Lessons learned are saved to gbrain** (Phase 3.5 handles this) — making them available for the sprint-planning skill to read before the next sprint.

**Save to gbrain:**
After presenting, save the full report to gbrain as a meeting page:
- Slug: `meetings/YYYY-MM-DD-sprint-N-retro`
- Includes timeline entry for future reference

### Phase 6: Forward to Sprint Planning

The lessons learned saved to gbrain in Phase 3.5 and Section #6 are **consumed by the sprint-planning skill** (coy/sprint-planning/SKILL.md). This creates a continuous feedback loop:

```
Sprint N Retro (sprint-retro)
  ↓  Saves lessons to gbrain as meetings/sprint-N-retro
Sprint N+1 Planning (sprint-planning)
  ↓  Reads lessons from gbrain retro pages (Phase 4)
  ↓  Injects into the next sprint proposal
Sprint N+1 Execution
  ↓
Sprint N+1 Retro (sprint-retro)
  ↓  Reports on whether lessons were applied
  ↓  New lessons saved to gbrain
  ↓  (loop continues)
```

**After running this retro, add timeline entries to:**
- `concepts/sprint-retro-format` — note the retro was run and what lessons were saved
- `concepts/phase4-sprint-intelligence-plan` — note progress on Phase 4
- `concepts/sprint-planning-skill` — note lessons available for next sprint planning

## Pitfalls

- **`total_points_committed` vs raw `--sprint` sum: they differ.** The `--retro` output excludes EPIC headings (containers). If you naively sum `--sprint N` output you'll include EPIC cumulative child sums, double-counting children. In Sprint 4: `--retro` = 97pts committed, raw `--sprint` = 188pts. Always use the retro's numbers for sprint scope.
- **Don't report item counts without point totals.** Points are the currency of sprint completion. Always show both.
- **Don't skip risk assessment.** The numbers alone don't tell the story — risk levels make the retro actionable.
- **Don't forget the sprint dates.** Duration context matters for velocity calculations.
- **gbrain save is optional but valuable.** Saved retros build a history for lessons-learned integration (Phase 4 requirement #3).

## See Also

- gbrain `concepts/sprint-retro-format` — retro output format standard
- gbrain `concepts/sprint-date-derivation` — how sprint boundaries are computed
- gbrain `concepts/phase4-sprint-intelligence-plan` — parent implementation plan
- gbrain `concepts/sprint-planning-skill` — consumes retro lessons for next sprint planning
- `coy/sprint-planning/SKILL.md` — sister skill: consumes lessons saved here
- `coy-sprint/SKILL.md` — sprint system overview
