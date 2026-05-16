# gbrain CLI Fallbacks (When Minions Is Down)

> Reference for running gbrain maintenance via CLI when the Minions worker is unavailable.
> gbrain CLI lives at `/opt/gbrain/`. It is NOT on $PATH — run via `cd /opt/gbrain && bun run src/cli.ts`.

## IMPORTANT: Environment Quirks

| Quirk | Detail |
|-------|--------|
| **Two gbrain entry points** | `gbrain` (the compiled binary) is on `$PATH` at `/usr/local/bin/gbrain` and supports `call`, `config`, `get`, `put`, `search`, `query`, etc. `bun run src/cli.ts` from `/opt/gbrain/` is the source-level runner. Prefer `gbrain` on PATH for simple queries; use `bun run src/cli.ts` for subcommands that aren't compiled into the binary (e.g., `embed`, `check-backlinks`, `sync`). |
| **`autopilot` needs binary** | `autopilot` subcommand expects the compiled `gbrain` binary on $PATH. `bun run src/cli.ts autopilot` will fail with "Could not resolve the gbrain CLI path." |
| **Embed needs API key** | `embed --all` requires `OPENAI_API_KEY` in the terminal environment. The MCP server has it, the terminal may not. If missing, all pages fail with "OpenAI embedding requires OPENAI_API_KEY." |
| **No interactive prompts** | CLI commands are batch/scriptable but may produce verbose output. Pipe to `grep`, `head`, or redirect. |

## Commands

### Embed Stale Pages

```bash
cd /opt/gbrain && bun run src/cli.ts embed --stale
```

- Re-embeds only pages with stale/changed content since last embed
- Fast — skips pages that don't need re-embedding
- If no stale pages: `Embedded 0 chunks (0 stale found)`

### Embed All Pages

```bash
cd /opt/gbrain && bun run src/cli.ts embed --all
```

- Re-embeds ALL pages (slow — processes 1,000+ pages)
- Can be interrupted and resumed
- Shows progress: `[embed.pages] N/1125 (X%)`

### Fix Missing Back-Links

```bash
cd /opt/gbrain && bun run src/cli.ts check-backlinks fix
```

- Scans all pages for markdown wikilinks (`[[slug]]`) that don't have a corresponding graph back-link
- Creates missing back-links automatically
- If none missing: `No missing back-links found.`

### Check Back-Links (Dry Run)

```bash
cd /opt/gbrain && bun run src/cli.ts check-backlinks check
```

- Same scan as `fix` but only reports — does NOT create links

### List Orphans

**⚠️ PRIMARY CLI (gbrain on PATH):**
```bash
gbrain call find_orphans '{}' 2>&1 > /tmp/orphans.json
```
- `gbrain` is on `$PATH` at `/usr/local/bin/gbrain` — no `cd` needed
- The `call` subcommand invokes the `find_orphans` MCP tool and writes raw JSON to stdout
- Stderr has non-fatal log messages like `[orphans.scan] start / done` — redirect with `2>&1`
- **Avoids truncation:** The MCP tool response can exceed 190K chars on a large brain (800+ orphans). Saving to a file lets you parse fully via `python3 -c "import json; d=json.load(open('/tmp/orphans.json')); print(len(d['orphans']))"`
- Output JSON structure (top-level keys): `orphans` (array of `{slug, title}`), `total_orphans`, `total_linkable`, `total_pages`, `excluded`

**Alternative (compiled binary only, NOT via bun):**
```bash
cd /opt/gbrain && bun run src/cli.ts orphans --json
cd /opt/gbrain && bun run src/cli.ts orphans --count
```
- `--json` — full list of orphan slugs and titles (can be huge — 800+ entries)
- `--count` — just the number
- ⚠️ This subcommand only exists in the compiled `gbrain` binary. If the local gbrain `bun run src/cli.ts` doesn't have it, use `gbrain call find_orphans` instead.

### Get Recency Data for Orphans

To sort orphans by most recently updated (for report formatting):
1. Save orphans to a file (see above)
2. Fetch recently updated pages via MCP:
   ```mcp_gbrain_list_pages(sort="updated_desc", limit=200)
   ```
3. Cross-reference orphan slugs against the returned pages to find update timestamps
4. Report format:
   - **0 orphans:** "🎮 Zero orphan pages — brain graph is fully connected."
   - **≤ 50 orphans:** List all with type + last-updated date
   - **> 50 orphans:** Report count + breakdown by prefix + top 10 most recent

### Sync / Acknowledge Failures

```bash
cd /opt/gbrain && bun run src/cli.ts sync --skip-failed
```

- Acknowledges and clears queued/pre-existing sync failures
- Doctor warning `"N unacked failure(s)"` will clear after this

### Doctor (Deep Inspection)

```bash
cd /opt/gbrain && bun run src/cli.ts doctor --json
```

- Runs all deep checks (not just health score)
- Outputs JSON with check-by-check status

## Workflow: Full CLI Maintenance Cycle

When Minions is down and you need to run maintenance from scratch:

```bash
cd /opt/gbrain

# 1. Check if there's anything to do
bun run src/cli.ts embed --stale

# 2. Fix any missing back-links from markdown wikilinks
bun run src/cli.ts check-backlinks fix

# 3. Clear sync failures if doctor reports them
bun run src/cli.ts sync --skip-failed

# 4. Verify
bun run src/cli.ts doctor --json | head -20
```

> ⚠️ Note: `autopilot` (full dream cycle) does NOT work via CLI. It requires the compiled `gbrain` binary on $PATH. The dream cycle only runs properly when the Minions worker is active.
