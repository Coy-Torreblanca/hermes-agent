---
name: gbrain-maintain
description: Active brain health maintenance — fix stale pages, connect orphans, detect dead links, trigger dream cycle, populate graph, audit citations. Complements the passive cron monitoring layer with interactive repair capabilities.
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, maintenance, second-brain, health]
    related_skills: [second-brain, gbrain-query, gbrain-page-writer]
---

# GBrain Maintain — Active Brain Health

Interactive maintenance skill. The 5 Hermes cron jobs (`gbrain-sync`, `gbrain-dream`, `gbrain-contradictions`, `gbrain-orphans`, `gbrain-doctor`) tell you what's wrong — this skill lets you say "fix it" and the agent does the work.

## When to Use

- User says "how's the brain doing?", "brain health check", "run doctor"
- User says "fix stale pages", "re-embed", "clean up orphans"
- User says "check for dead links", "populate the graph", "connect these pages"
- User says "trigger the dream cycle", "run autopilot now"
- User says "audit citations" or "are there uncited facts?"
- After major brain changes (imports, batch writes) — verify integrity

## Capabilities vs Cron

| Capability | Cron (Passive) | Skill (Active) |
|-----------|---------------|----------------|
| Health dashboard | Weekly report to Discord | On-demand, any time |
| Stale pages | Count in dream cycle | Identify + re-embed specific pages |
| Orphans | Weekly list to Discord | Connect specific orphans to graph |
| Dead links | ❌ Not covered | Find + fix broken links |
| Dream cycle | Nightly 2am only | Trigger on-demand |
| Graph population | ❌ Not covered | Suggest missing connections |
| Citation audit | ❌ Not covered | Check pages for uncited facts |
| Friction logging | ❌ Not covered | Log issues for operator review |

## Step 0: Load Conventions

Before any maintenance operation, load the quality rules and friction protocol:

```
skill_view(name="second-brain", file_path="references/quality.md")
skill_view(name="second-brain", file_path="references/_friction-protocol.md")
```

---

## Operation 1: Brain Health Check

**Trigger:** "how's the brain", "health check", "run doctor"

```
mcp_gbrain_get_health()
mcp_gbrain_run_doctor()
```

Report the dashboard with clear severity indicators:
- **Brain score** (0–100): 🔴 <30, 🟡 30–70, 🟢 >70
- **Embed coverage**: % of chunks with embeddings
- **Stale pages**: count + list if manageable
- **Orphan pages**: count + worst offenders
- **Dead links**: count (0 = 🟢)
- **Link/timeline coverage**: graph health indicators

## Operation 2: Fix Stale Pages

**Trigger:** "fix stale pages", "re-embed", "embed stale"

1. Run `mcp_gbrain_get_health()` to identify stale page count
2. If > 0, submit the embed job via Minions:
   ```
   mcp_gbrain_submit_job(name="embed", data={})
   ```
3. Poll progress:
   ```
   mcp_gbrain_get_job_progress(id=<job_id>)
   ```
4. Report: pages processed, embeddings generated, any failures
5. If Minions worker is down, tell the user and offer to submit the job for when the worker comes back

Fallback (if Minions is down): offer to run `gbrain embed --stale` directly via terminal.

## Operation 3: Orphan Enrichment

**Trigger:** "connect orphans", "enrich orphan pages", "fix orphan X"

1. Find orphans:
   ```
   mcp_gbrain_find_orphans(include_pseudo=false)
   ```
2. Present orphans sorted by recency — most recent first (they're the active content)
3. For each orphan the user wants to connect:
   a. Read the page: `mcp_gbrain_get_page(slug="<orphan>")`
   b. Search for related pages: `mcp_gbrain_query(query="<page topic>")`
   c. Propose links: "Connect `<orphan>` to `<target>`? They both reference `<shared topic>`."
   d. Create links with user approval:
      ```
      mcp_gbrain_add_link(from="<orphan>", to="<target>", link_type="references")
      ```
4. Log a friction entry if an orphan can't be connected (missing related pages → ingestion gap)

## Operation 4: Dead Link Detection

**Trigger:** "check dead links", "find broken links"

1. Run doctor to get dead link count:
   ```
   mcp_gbrain_run_doctor()
   ```
2. If dead links found, iterate through linked pages to identify broken references
3. For each dead link found:
   a. Check if the target page exists (search/resolve slug)
   b. If target exists but slug changed → update the link
   c. If target was deleted → remove the dead link or replace with correct slug
   d. Use `mcp_gbrain_remove_link(from, to)` to prune dead edges

## Operation 5: Dream Cycle (On-Demand)

**Trigger:** "run dream cycle", "trigger autopilot", "run maintenance now"

1. Submit the autopilot-cycle job:
   ```
   mcp_gbrain_submit_job(name="autopilot-cycle", data={})
   ```
2. Poll until complete:
   ```
   mcp_gbrain_get_job_progress(id=<job_id>)
   ```
3. Report summary: pages processed, embeddings generated, backlinks populated, pages purged
4. If the Minions worker is down, this will fail — report and offer alternatives

## Operation 6: Graph Population

**Trigger:** "populate the graph", "suggest links", "connect the brain"

1. Get the most-connected entities:
   ```
   mcp_gbrain_get_health()
   ```
   (The `most_connected` field shows link counts)
2. For pages with 0 links (orphans), follow Operation 3
3. For pages with low link counts (1–2), traverse to find connection opportunities:
   ```
   mcp_gbrain_traverse_graph(slug="<page>", depth=2)
   ```
4. Suggest: "`<page_a>` and `<page_b>` both link to `<hub>` — should they connect directly?"

## Operation 7: Citation Audit

**Trigger:** "audit citations", "check for uncited facts", "verify sources"

1. Search for pages with potential uncited claims:
   ```
   mcp_gbrain_search(query="..." )  # broad search across pages
   ```
2. For each candidate page, read content and check:
   - Every factual claim has `[Source: ...]` inline
   - Source dates are valid
   - No paraphrasing that lost the original source
3. Flag pages with missing or weak citations
4. Offer to reload `gbrain-page-writer` to fix citation gaps

## Operation 8: Friction Logging

**Trigger:** (automatic — log whenever maintenance hits friction)

When any maintenance operation encounters friction (confusing errors, missing data, broken assumptions), log it:

```
mcp_gbrain_add_timeline_entry(
    slug="wiki/friction-log",
    date="YYYY-MM-DD",
    summary="<severity>: <one-line-what-happened>",
    detail="Phase: gbrain-maintain. Hint: <what-could-be-better>."
)
```

Severities: `blocker`, `error`, `confused`, `nit`.

If `wiki/friction-log` doesn't exist, create it first (type: log, title: Friction Log).

---

## Common Pitfalls

- **Doctor vs Health** — `mcp_gbrain_get_health()` gives the dashboard summary; `mcp_gbrain_run_doctor()` runs deeper checks. Use health for quick status, doctor for deep inspection.
- **Minions dependency** — embed jobs and autopilot-cycle require the Minions worker to be running. If it's down, these operations will queue but never execute. Check `mcp_gbrain_list_jobs(status="waiting")` to detect queue buildup.
- **Orphan ≠ garbage** — an orphan page may be perfectly valid but unlinked. Don't suggest deletion; suggest enrichment.
- **Don't auto-fix without approval** — propose fixes, get user confirmation, then execute. The brain is Coy's memory; don't modify it blindly.
- **Friction log is mandatory** — every maintenance session should leave at least one timeline entry (even if it's "no friction — all operations clean").

## Verification Checklist

After any maintenance session:
- [ ] Health score checked and reported
- [ ] Friction logged (even if "no issues")
- [ ] Any fixes confirmed by user before execution
- [ ] Job status polled if jobs were submitted
- [ ] Link changes verified (re-read the page after linking)
