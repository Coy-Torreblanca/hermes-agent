---
name: gbrain-maintain
description: Active brain health maintenance — fix stale pages, connect orphans, detect dead links, trigger dream cycle, populate graph, audit citations. Complements the passive cron monitoring layer with interactive repair capabilities.
version: 1.3.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, maintenance, second-brain, health]
    related_skills: [second-brain, gbrain-query, gbrain-page-writer, gbrain-article-enrichment]
---

# GBrain Maintain — Active Brain Health

Interactive maintenance skill. The 5 Hermes cron jobs (`gbrain-contradictions`, `gbrain-doctor`, `gbrain-dream`, `gbrain-orphans`, `gbrain-article-enrichment`) do the passive monitoring and automated fixing — this skill lets you say "fix it" interactively for things the cron layer doesn't automate or can't resolve on its own.

## When to Use

- User says "how's the brain doing?", "brain health check", "run doctor"
- User says "fix stale pages", "re-embed", "clean up orphans"
- User says "check for dead links", "populate the graph", "connect these pages"
- User says "trigger the dream cycle", "run autopilot now"
- User says "audit citations" or "are there uncited facts?"
- User says "perform brain maintenance", "get the score up", "improve brain health"
- After major brain changes (imports, batch writes) — verify integrity

## Capabilities vs Cron

| Capability | Cron (Passive) | Skill (Active) |
|-----------|---------------|----------------|
| Health dashboard | Weekly report to Discord | On-demand, any time |
| Stale pages | Count in dream cycle | Identify + re-embed specific pages |
| Orphans | Weekly list to Discord | Connect specific orphans to graph |
| Article enrichment | Sunday via cron | Interactive enrichment via `gbrain-article-enrichment` skill |
| Dead links | ❌ Not covered | Find + fix broken links |
| Dream cycle | Nightly 2am only | Trigger on-demand |
| Graph population | ❌ Not covered | Suggest missing connections |
| Citation audit | ❌ Not covered | Check pages for uncited facts |
| Friction logging | ❌ Not covered | Log issues for operator review |
| CLI fallback cycle | ❌ Not covered | Run `gbrain embed --stale` + `check-backlinks fix` + `sync --skip-failed` via terminal |
| Contradiction probe | Daily via cron (doctor surfaces findings) | On-demand probe run via CLI with custom queries |

## Step 0: Load Conventions

Before any maintenance operation, load the quality rules and friction protocol:

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_friction-protocol.md
```

If Minions is suspected down also load the CLI fallback reference:

```
read_file /data/.hermes/skills/gbrain/gbrain-maintain/references/cli-fallbacks.md
```

---

## Operation 1: Brain Health Check & Score Interpretation

**Trigger:** "how's the brain", "health check", "run doctor"

```mcp_gbrain_get_health()
mcp_gbrain_run_doctor()
```

Report the dashboard with clear severity indicators:

**Brain score (0–100):** 🔴 <30, 🟡 30–70, 🟢 >70

The score is composed of 5 weighted components. Analyze each:

| Component | Max | Interpretation | Lever |
|-----------|-----|----------------|-------|
| `embed_coverage_score` | 35 | % of chunks with embeddings | Once at 35, never touch again |
| `link_density_score` | 25 | % of pages with graph edges | Manual linking OR autopilot cycle |
| `timeline_coverage_score` | 15 | % of pages with timeline entries | Add entries during enrichment |
| `no_orphans_score` | 15 | Inverse of orphan count | Connect orphans to graph |
| `no_dead_links_score` | 10 | 0 dead links = max | Doctor detects broken links |

**Structural ceiling awareness:** If the brain has a high proportion of auto-synced project docs (>80%), link density and timeline coverage will be structurally limited. Project docs (imported markdown from repos) typically have no wikilinks or timelines. Connecting orphan concept/note/person pages helps but moves the needle slowly against a large denominator. Acknowledge this to the user rather than promising unrealistic improvements.

Also report:
- **Embed coverage**: % of chunks with embeddings
- **Stale pages**: count + list if manageable
- **Orphan pages**: count + worst offenders
- **Dead links**: count (0 = 🟢)
- **Link/timeline coverage**: graph health indicators (absolute numbers)
- **Most connected pages**: top entities — these are the hubs of the graph
- **Doctor warnings**: sync failures, queue health, search mode

## Operation 2: Fix Stale Pages

**Trigger:** "fix stale pages", "re-embed", "embed stale"

### Via Minions (preferred)
1. Run `mcp_gbrain_get_health()` to identify stale page count
2. If > 0, submit the embed job via Minions:
   ```mcp_gbrain_submit_job(name="embed", data={})```
3. Poll progress:
   ```mcp_gbrain_get_job_progress(id=<job_id>)```
4. Report: pages processed, embeddings generated, any failures

### Via CLI (Minions down fallback)
1. Run `bun run src/cli.ts embed --stale` from `/opt/gbrain/`
2. If that reports "0 stale found" but health shows stale pages, try `embed --all`
3. CAUTION: `embed --all` requires `OPENAI_API_KEY` in the terminal environment. The MCP server has it, but a bare terminal session may not. If all pages fail with "OpenAI embedding requires OPENAI_API_KEY", report it as friction.
4. See `references/cli-fallbacks.md` for full command details.

## Operation 3: Orphan Enrichment

**Trigger:** "connect orphans", "enrich orphan pages", "fix orphan X", "surface orphans", "orphan report"

### 3a. Find Orphans

Primary — MCP tool:
```mcp_gbrain_find_orphans(include_pseudo=false)```

**⚠️ Truncation pitfall:** When the brain has many orphans (800+), the MCP tool result can exceed 190K chars and get truncated. The tool output includes top-level keys: `orphans` (array), `total_orphans`, `total_linkable`, `total_pages`, `excluded`. If you see a truncated response, fall back to CLI.

CLI fallback (avoids truncation — `gbrain` is on PATH via `/usr/local/bin/gbrain`):
```bash
gbrain call find_orphans '{}' 2>&1 > /tmp/orphans.json
```
Then parse with Python:
```python
import json
with open('/tmp/orphans.json') as f:
    data = json.load(f)
orphans = data['orphans']        # list of {slug, title}
total = data['total_orphans']    # count
total_pages = data['total_pages']
total_linkable = data['total_linkable']
```

The `gbrain call` subcommand invokes any MCP tool directly and writes the raw JSON to stdout. Stderr has log messages (safe to redirect with `2>&1`). The JSON file can then be parsed without truncation.

### 3b. Report Orphans

Sort orphans by recency — most recent first (they're the active content). To get recency data:

1. Fetch recently updated pages: `mcp_gbrain_list_pages(sort="updated_desc", limit=200)`
2. Cross-reference orphan slugs against the returned pages to find the most recently updated ones
3. Follow these reporting conventions:

| Orphan count | Format |
|-------------|--------|
| **0** | Respond: "🎮 Zero orphan pages — brain graph is fully connected." |
| **≤ 50** | List all orphans with their `type` and `updated_at` date |
| **> 50** | Report count + breakdown by prefix + top 10 most recently updated orphans |

When reporting >50, include:
- Total orphans, linkable pages, connectivity rate (%)
- Breakdown by prefix (e.g. `projects/`, `people/`, `brain/`, `concepts/`)
- Top 10 most recently updated orphan pages with type and date
- Notable root-level orphans (no prefix)

**Structural ceiling note:** When >80% of pages are auto-synced project docs (imported markdown from repos with no wikilinks), orphan rates of 80%+ are expected and structurally normal. Explain this rather than alarming the user.

### 3c. Connect Orphans

For each orphan the user wants to connect:
1. Read the page: `mcp_gbrain_get_page(slug="<orphan>")`
2. Search for related pages: `mcp_gbrain_query(query="<page topic>")`
3. **Check for missing reciprocal links:** Use `mcp_gbrain_get_backlinks(slug="<orphan>")` to see if any pages already link TO the orphan. If a page backlinks the orphan but the orphan doesn't link back, that's a missing reciprocal — create it.
   - Example: A research-paper page has inbound backlinks from concept pages derived from it, but the original page doesn't link forward to those concepts. Fix the symmetry.
4. Propose links: "Connect `<orphan>` to `<target>`? They both reference `<shared topic>`."
5. Create links with user approval:
   ```mcp_gbrain_add_link(from="<orphan>", to="<target>", link_type="references")```
6. Log a friction entry if an orphan can't be connected (missing related pages → ingestion gap)

### Batch Approach (When Many Related Orphans)

When you find orphans that are obviously related to a parent project or hub page, batch-connect them:

1. Read each orphan page to confirm relevance (parallel reads)
2. Present the batch proposal: "These 5 concept pages all relate to projects/second-brain. OK to connect them all?"
3. Execute approved links + add timeline entries to each orphan page
4. This is faster than one-at-a-time proposals

## Operation 4: Dead Link Detection

**Trigger:** "check dead links", "find broken links"

1. Run doctor to get dead link count:
   ```mcp_gbrain_run_doctor()```
2. If dead links found, iterate through linked pages to identify broken references
3. For each dead link found:
   a. Check if the target page exists (search/resolve slug)
   b. If target exists but slug changed → update the link
   c. If target was deleted → remove the dead link or replace with correct slug
   d. Use `mcp_gbrain_remove_link(from, to)` to prune dead edges

## Operation 5: Dream Cycle (On-Demand)

**Trigger:** "run dream cycle", "trigger autopilot", "run maintenance now"

### Via Minions (preferred)
1. Submit the autopilot-cycle job:
   ```mcp_gbrain_submit_job(name="autopilot-cycle", data={})```
2. Poll until complete:
   ```mcp_gbrain_get_job_progress(id=<job_id>)```
3. Report summary: pages processed, embeddings generated, backlinks populated, pages purged
4. If the Minions worker is down, this will fail — report and offer alternatives

### Via CLI (Minions down fallback)
**Does NOT work.** The `autopilot` subcommand requires the compiled `gbrain` binary on $PATH (`bun run src/cli.ts autopilot` will fail). Instead, run the individual CLI commands from the full cycle:
1. `bun run src/cli.ts embed --stale`
2. `bun run src/cli.ts check-backlinks fix`
3. `bun run src/cli.ts sync --skip-failed`
4. See `references/cli-fallbacks.md` for full details.

## Operation 6: Graph Population

**Trigger:** "populate the graph", "suggest links", "connect the brain"

1. Get the most-connected entities:
   ```mcp_gbrain_get_health()```
   (The `most_connected` field shows link counts)
2. For pages with 0 links (orphans), follow Operation 3
3. For pages with low link counts (1–2), traverse to find connection opportunities:
   ```mcp_gbrain_traverse_graph(slug="<page>", depth=2)```
4. Suggest: "`<page_a>` and `<page_b>` both link to `<hub>` — should they connect directly?"

## Operation 7: Fix Missing Back-Links

**Trigger:** "fix back-links", "check backlinks", "populate back-links"

Minions handles this in the dream cycle. When Minions is down:

1. Run the CLI tool:
   ```bash
   cd /opt/gbrain && bun run src/cli.ts check-backlinks fix
   ```
2. This scans all pages for markdown wikilinks (`[[slug]]`) and creates any missing graph back-links automatically
3. Report: "No missing back-links found" or "Created N back-links"

For a dry-run first: `bun run src/cli.ts check-backlinks check`

## Operation 8: Citation Audit

**Trigger:** "audit citations", "check for uncited facts", "verify sources"

1. Search for pages with potential uncited claims:
   ```mcp_gbrain_search(query="...")  # broad search across pages```
2. For each candidate page, read content and check:
   - Every factual claim has `[Source: ...]` inline
   - Source dates are valid
   - No paraphrasing that lost the original source
3. Flag pages with missing or weak citations
4. Offer to reload `gbrain-page-writer` to fix citation gaps

## Operation 9: Friction Logging

**Trigger:** (automatic — log whenever maintenance hits friction)

When any maintenance operation encounters friction (confusing errors, missing data, broken assumptions), log it:

```mcp_gbrain_add_timeline_entry(
    slug="wiki/friction-log",
    date="YYYY-MM-DD",
    summary="<severity>: <one-line-what-happened>",
    detail="Phase: gbrain-maintain. Hint: <what-could-be-better>."
)
```

Severities: `blocker`, `error`, `confused`, `nit`.

If `wiki/friction-log` doesn't exist, create it first (type: note, title: gbrain Friction Log).

---

## Operation 10: Run Contradiction Probe

**Trigger:** "run contradiction probe", "check for contradictions", "gbrain eval suspected-contradictions", "run the probe"

The contradiction probe samples retrieval results and asks an LLM judge whether any pair contradicts on a factual claim. It is the interactive counterpart of the `gbrain-contradictions` cron job.

### Prerequisites

The probe requires one of:
- `--queries-file FILE.jsonl` — each line: `{"query": "..."}`. **No default file exists** — you must create one or use an alternative.
- `--query "..."` — single-query probe (quick but n=1 gives unactionably wide CI).
- `--from-capture` — uses captured queries from prior searches (check with `gbrain eval export --since 7d`).

If none exist, generate queries from the brain's content: list people pages via `mcp_gbrain_list_pages(type="person")`, project slugs, and domain concepts to build a representative set (aim for 15–50 queries).

### Run the probe

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions \
  --queries-file /tmp/queries.jsonl \
  --top-k 5 \
  --budget-usd 1 \
  --yes
```

Defaults (non-TTY): `--top-k 5`, `--judge anthropic:claude-haiku-4-5`, `--budget-usd $1`.

### Check the trend

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions trend --days 30
```

Each row is one probe run showing: date, model, query count, flags, and Wilson 95% CI.

### Review high-severity findings

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions review --severity high
```

### MCP surface (read-only, cached)

```mcp_gbrain_find_contradictions(limit=50, severity="high")```

This reads the **most recent probe run** — it does NOT trigger a new probe. Always use the CLI to run a fresh evaluation.

### Interpreting results

| Signal | Meaning |
|--------|---------|
| n < 30 | CI too wide to act on — run more queries |
| Wilson CI lower bound < 5% | Existing mechanisms (source-boost, recency-decay) handle the load |
| Wilson CI lower bound 5–15% | Real but bounded — operator decides |
| Wilson CI lower bound > 15% | Real and substantial — plan the bigger swing |

### Pitfalls

- **MCP is read-only** — `mcp_gbrain_find_contradictions()` returns cached results. Use CLI to trigger a new probe.
- **Cron job may already cover this** — the daily cron runs a probe and surfaces findings via `gbrain doctor`. Only run manually when investigating specific concerns or after large imports.
- **Budget matters** — default $1 non-TTY caps at ~200 judge calls. For 50 queries × top-5 pairs, bump to $5.
- **Cache is your friend** — re-runs with the same query set cost near-zero. Don't skip it.

### See also

- `references/contradiction-probe.md` — full command reference, severity rubric, cost model, resolution commands.

---

## Common Pitfalls

- **Doctor vs Health** — `mcp_gbrain_get_health()` gives the dashboard summary; `mcp_gbrain_run_doctor()` runs deeper checks. Use health for quick status, doctor for deep inspection.
- **Minions dependency** — embed jobs, autopilot-cycle, and dream cycle all require the Minions worker. If it's down, operations queue but never execute. Check `mcp_gbrain_list_jobs(status="waiting")` to detect queue buildup.
- **CLI embed needs API key** — `embed --all` will fail on every page if `OPENAI_API_KEY` isn't in the terminal environment. The MCP server and terminal are separate contexts.
- **autopilot CLI is broken** — `bun run src/cli.ts autopilot` always fails. It needs the compiled `gbrain` binary on $PATH. Run individual CLI commands instead.
- **Score ceiling** — when >80% of pages are imported project docs, link density and timeline coverage scores are structurally capped. Don't promise 100/100; explain the composition.
- **Orphan ≠ garbage** — an orphan page may be perfectly valid but unlinked. Don't suggest deletion; suggest enrichment.
- **Don't auto-fix without approval** — propose fixes, get user confirmation, then execute. The brain is Coy's memory; don't modify it blindly.
- **Friction log is mandatory** — every maintenance session should leave at least one timeline entry (even if it's "no friction — all operations clean").
- **Batch-connect where obvious** — concept/note pages clearly relating to a parent project can be proposed in a batch, not one at a time. Saves turns.
- **Always add timeline entries with links** — linking an orphan page without adding a timeline entry to it is a missed opportunity to improve timeline coverage score.
- **gbrain must be on PATH for migrations** — `apply-migrations` calls `gbrain init --migrate-only` as a subprocess. If `gbrain` isn't on $PATH, Phase A will fail silently. Fix: `ln -sf /opt/gbrain/src/cli.ts /usr/local/bin/gbrain` (the `#!/usr/bin/env bun` shebang handles execution).
- **Migration v0.12.0 link extraction is slow** — scanning 1,145+ pages for wikilinks can take 60–300+ seconds. Set generous timeouts when running `apply-migrations --yes` for the first time on a populated brain. Subsequent runs are no-ops.
- **Lint issue triage** — 95% of lint issues (`no-frontmatter`, `missing-type`, `missing-created`) are structural/benign on imported project docs (READMEs, RELEASE notes). Only ~5% are actionable. See `references/lint-remedies.md` for the full triage guide.
- **`--fix` only handles code-fence-wrap and LLM preambles** — YAML parse errors, nested quotes, no-frontmatter, missing-type, and all other lint categories are NOT auto-fixable by `--fix`. Run `gbrain lint <file|dir> --fix` to clear the 1-2% fixable issues, then fix remaining actionable issues individually.
- **Orphan rate is structurally normal** — when >80% of pages are auto-synced project docs with no wikilinks, 80%+ orphan rates are expected. Don't alarm the user; explain the composition.

## Reference Files

- `references/cli-fallbacks.md` — Full gbrain CLI command reference, environment quirks, and non-interactive maintenance cycle for when Minions worker is down.
- `references/lint-remedies.md` — Lint issue category triage: which issues are actionable vs structural/benign, with exact fix commands for each type.
- `references/contradiction-probe.md` — Full command reference for `gbrain eval suspected-contradictions`: architecture, severity rubric, cost model, resolution commands, and output interpretation.

## Verification Checklist

After any maintenance session:
- [ ] Health score checked and reported with component breakdown
- [ ] Friction logged (even if "no issues")
- [ ] Any fixes confirmed by user before execution
- [ ] Job status polled if jobs were submitted (via MCP or CLI)
- [ ] CLI fallbacks attempted if Minions was down
- [ ] Link changes verified (re-read the page after linking)
- [ ] Timeline entries added alongside each orphan link
- [ ] Score ceiling communicated honestly if structural