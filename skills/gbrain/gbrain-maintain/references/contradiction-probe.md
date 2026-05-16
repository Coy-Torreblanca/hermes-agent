# Contradiction Probe — Full Command Reference

> gbrain v0.32.6+ — `gbrain eval suspected-contradictions`

## Architecture

The probe samples top-K retrieval results, asks an LLM judge whether any pair contradicts on a factual claim relevant to the query, and aggregates into a calibrated report. It never mutates the brain — only reads pages/takes/chunks, writes to `eval_contradictions_runs` and `eval_contradictions_cache`.

Cache (`eval_contradictions_cache`) is keyed on `(chunk_a_hash, chunk_b_hash, model, prompt_version, truncation_policy)` — re-runs against the same query set cost near-zero until `PROMPT_VERSION` bumps.

## Commands

### Run a probe

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions \
  --queries-file /tmp/queries.jsonl \
  --top-k 5 \
  --budget-usd 1 \
  --yes
```

Required: one of `--queries-file FILE`, `--query "..."`, or `--from-capture`.

Defaults (non-TTY):
| Flag | Default |
|------|---------|
| `--top-k` | 5 |
| `--judge` | `anthropic:claude-haiku-4-5` |
| `--budget-usd` | $1 (non-TTY), $5 (TTY) |
| `--max-pair-chars` | 1500 |
| `--sampling` | `deterministic` |
| `--no-cache` | false (cache ON) |

### No default queries file exists

`~/.gbrain/queries.jsonl` does NOT exist by default. You must either:
1. Create a `.jsonl` file with one `{"query": "..."}` per line, or
2. Pass `--query "..."` for a single-query probe, or
3. Use `--from-capture` (captures must exist — check with `gbrain eval export --since 7d`)

If no captures or queries file exist, generate a broad set from the brain's content:
- People slugs from `mcp_gbrain_list_pages(type="person")` or health dashboard
- Project/concept slugs for domain-specific queries
- General broad queries as fallback

### Trend tracking

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions trend --days 30
```

Shows ASCII bar chart with date, model, query count, flag count, and Wilson CI. Each row is one probe run.

### Review findings

```bash
cd /opt/gbrain && bun run src/cli.ts eval suspected-contradictions review --severity high
```

Surface findings from the most recent run, filtered by severity. Includes resolution proposals.

## Output interpretation

```
Queries with >=1 contradiction: 0 / 15 (0%)
Wilson CI 95%: 0–20%
Note: n=15 is below 30; the 95% CI is too wide to act on.
```

- **n < 30**: CI too wide to draw conclusions — run more queries
- **Wilson CI lower bound < 5%**: source-boost + recency-decay + curated pages handle the load
- **Wilson CI lower bound 5–15%**: real but bounded — operator decides
- **Wilson CI lower bound > 15%**: real and substantial — plan the bigger swing

## Severity rubric

| Level | Rubric | Example |
|-------|--------|---------|
| `low` | naming/format differences | "Alice Smith" vs "A. Smith" |
| `medium` | factual values that may be stale | revenue figure, headcount, valuation |
| `high` | identity / structural claims | founder/CEO/CFO role, company status |

## Resolution commands per finding

Each finding ships with a `resolution_command` field:

- `gbrain takes supersede <slug> --row N` — newer take replaces older chunk text (intra_page)
- `gbrain dream --phase synthesize --slug <slug>` — compiled_truth needs update (cross_slug curated-vs-bulk)
- `gbrain takes mark-debate <slug> --row N` — intentional disagreement, keep both
- `# manual review: <a> vs <b>` — judge wasn't sure

## Cost

- ~$0.0006 per judge call (claude-haiku-4-5, ~500 in / 80 out tokens)
- ~$0.005 per query (after date pre-filter + cache hits)
- ~$0.50 per 100 queries
- Re-runs with cache: near-zero

## MCP surface

- `mcp_gbrain_find_contradictions(limit, severity)` — reads most recent probe run. **Does NOT trigger a new probe.** Use CLI for that.
- Results cached in `eval_contradictions_runs` table. Re-check via the `--json` CLI flag.
