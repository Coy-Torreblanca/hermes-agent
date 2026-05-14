# gbrain CLI Fallbacks (When Minions Is Down)

> Reference for running gbrain maintenance via CLI when the Minions worker is unavailable.
> gbrain CLI lives at `/opt/gbrain/`. It is NOT on $PATH — run via `cd /opt/gbrain && bun run src/cli.ts`.

## IMPORTANT: Environment Quirks

| Quirk | Detail |
|-------|--------|
| **Not on PATH** | Must run from `/opt/gbrain/` via `bun run src/cli.ts <command>` |
| **`autopilot` needs binary** | `autopilot` subcommand expects a compiled binary on $PATH. `bun run src/cli.ts autopilot` will fail with "Could not resolve the gbrain CLI path." |
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

```bash
cd /opt/gbrain && bun run src/cli.ts orphans --json
cd /opt/gbrain && bun run src/cli.ts orphans --count
```

- `--json` — full list of orphan slugs and titles (can be huge — 800+ entries)
- `--count` — just the number

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
