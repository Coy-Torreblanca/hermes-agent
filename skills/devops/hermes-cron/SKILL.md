---
name: hermes-cron
description: "Create and manage long-running Hermes cron jobs using the /app/hermes_cron pattern. Declarative config-driven cron jobs with deterministic sync. Covers config.yaml structure, sync.py, field reference, and when to use cron vs skills."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [cron, scheduling, devops, infrastructure]
    related_skills: [coy-daily-briefing, gbrain-reports]
---

# Hermes Cron — Long-Living Cron Job Management

Declarative, config-driven cron jobs using `/app/hermes_cron/`. Cron jobs are
defined in `config.yaml` and synced deterministically into Hermes cron state
via `sync.py`. This pattern replaces shell-loop maintenance scripts and manual
cronjob tool invocations.

## When to Use This Skill

- **Creating a new cron job** — add an entry to `/app/hermes_cron/config.yaml`
- **Converting a skill to a cron job** — the skill's workflow becomes the cron prompt
- **Updating an existing cron job** — edit config.yaml, then run sync.py
- **Wondering "should this be a skill or a cron job?"** — consult the decision guide below
- **Onboarding a new developer** — this is the canonical reference for the cron system

## Architecture

```
/app/hermes_cron/
├── config.yaml        # Declarative job definitions (the source of truth)
├── requirements.md    # Design requirements for the sync system
├── sync.py            # Idempotent syncing engine (config.yaml → Hermes cron state)
├── test_sync.py       # Tests for sync.py
├── README.md          # Full canonical documentation
```

**Flow:**
1. Edit `config.yaml` to add/update a cron job definition
2. Run `python3 /app/hermes_cron/sync.py` to sync config → Hermes cron state
3. (Optional) `python3 /app/hermes_cron/sync.py --dry-run` to preview changes
4. Hermes executes the job on schedule

**Key properties:**
- **Idempotent** — running sync.py multiple times is safe. No-ops if nothing changed.
- **Deterministic** — config.yaml IS the source of truth. Runtime state is derived.
- **Preserves orphans** — jobs in state but not in config are NEVER deleted (safe rollback).
- **Path-independent** — sync.py finds config.yaml relative to its own script location.

## Config.yaml Structure

```yaml
jobs:
  - name: <unique-job-name>        # stable identity key — never change after creation
    schedule: <cron-expression>     # "0 9 * * *" or "every 2h" or "30m"
    prompt: <string>                # Self-contained instruction for the job (MANDATORY)
    skills:                         # Skills to load before running (optional)
      - <skill-name>
    deliver: <target>               # "origin" (default), "discord", "telegram", or "local"
    enabled_toolsets:               # Restrict tools to reduce context (optional)
      - terminal
      - file
    model:                          # Model override (optional)
      provider: <provider-name>
      model: <model-name>
    repeat: <number>                # Run N times then stop (optional)
    workdir: <path>                 # Working directory for the job (optional)
    script: <path>                  # Pre-run script path (optional)
    context_from:                   # Inject output from other jobs (optional)
      - <other-job-name>
```

### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | ✅ | string | Stable identity key. Never change after creation — it's the matching key for sync.py's idempotent update. Max 64 chars, lowercase, hyphens. |
| `schedule` | ✅ | string | Cron expression (`"0 9 * * *"`), interval (`"every 2h"`, `"30m"`), or ISO timestamp (`"2026-05-20T09:00:00"`). |
| `prompt` | ✅ | string | **Self-contained instruction.** The cron job runs in a fresh session with no conversation context. The prompt must be complete enough that a new agent session can execute it without any prior knowledge. Include all steps, tool calls, and format instructions. |
| `skills` | ❌ | list | Skills to load before the job runs. The cron session loads these via `skill_view()` before following the prompt. Example: `["second-brain", "gbrain-maintain"]`. |
| `deliver` | ❌ | string | Where to deliver the job's final response. `"origin"` = return to current chat (default), `"discord"` = Discord home, `"telegram"` = Telegram home, `"local"` = save to `~/.hermes/cron/output/` only. |
| `enabled_toolsets` | ❌ | list | Restrict the agent to specific toolsets. Omitting gives all default tools. Common: `["terminal", "file"]` for minimal jobs that just read/report, or omit for jobs that need gbrain MCP tools. |
| `model` | ❌ | dict | Override the model for this specific job. Format: `{provider: "openai", model: "gpt-4o"}`. Provider is pinned at creation time if omitted. |
| `repeat` | ❌ | int | Run the job N times then stop. Omit for recurring jobs (runs until removed). |
| `workdir` | ❌ | string | Absolute path to run the job from. Project context files (AGENTS.md, etc.) from that path are injected into the system prompt. Jobs with workdir run sequentially to keep directories isolated. |
| `script` | ❌ | string | Path to a Python script whose stdout is injected as context before the job runs. Relative paths resolve under `~/.hermes/scripts/`. Use for data collection and change detection. |
| `context_from` | ❌ | list | Job name(s) whose most recent output is injected as context before each run. Chain jobs: job A collects data, job B processes it. |

## Step-by-Step: Adding a New Cron Job

### 1. Decide: Skill vs Cron Job?

| Use a Skill when... | Use a Cron Job when... |
|--------------------|------------------------|
| User says "do X" interactively | Runs on a schedule without user interaction |
| User needs to influence the output | Output is always the same pattern |
| The workflow needs user decisions | The workflow is fully deterministic |
| It's a one-off or rare operation | It runs regularly (daily, weekly, etc.) |
| The user needs to see/discuss results | Results are logged/briefed asynchronously |

### 2. Write the Prompt

The prompt is the most important part. It MUST be:

- **Self-contained** — imagine a fresh agent session with zero context
- **Tool-explicit** — include specific tool calls like `mcp_gbrain_search(query="...")`
- **Step-by-step** — numbered steps the agent can follow linearly
- **Error-aware** — include what to do if something fails (e.g., "If Minions is down, report it")
- **Report-format** — tell the agent exactly how to format the output

**Good prompt pattern:**
```
## Workflow

1. **Step one:** Do X using {specific_tool_call}
2. **Step two:** Do Y using {specific_tool_call}
3. **Report:** Format output as {specific format}

## Quality Rules
- Rule 1
- Rule 2

## Error Handling
- If X fails, do Y
```

### 3. Add the Entry

Edit `/app/hermes_cron/config.yaml`:

```yaml
- name: my-new-job
  schedule: "0 9 * * 1"
  prompt: |
    Run the weekly widget check.

    Steps:
    1. Query for widgets: mcp_gbrain_search(query="widget")
    2. Report count and status.

    Format: simple list.
  skills:
    - second-brain
  deliver: discord
```

### 4. Sync

```bash
python3 /app/hermes_cron/sync.py --dry-run   # preview
python3 /app/hermes_cron/sync.py              # apply
```

### 5. Verify

```bash
python3 /app/hermes_cron/sync.py              # should show "no changes needed"
```

Or check with `cronjob(action='list')`.

## Converting a Skill to a Cron Job

When a skill should be a recurring scheduled task instead of an interactive skill:

1. **Extract the workflow** from the skill's SKILL.md
2. **Make the prompt self-contained** — remove references to loading skills (the cron config handles that), remove "When to Use" sections, make all instructions explicit for a fresh session
3. **Add entry to config.yaml** with appropriate schedule
4. **Repurpose the skill** — update it to be a reference document pointing at the cron job (or delete it if the cron fully replaces it)
5. **Run sync.py** to create the cron job
6. **Verify** — if the schedule allows, trigger a test run

## Common Pitfalls

- **Not self-contained prompts** — the most common failure. The cron session has NO memory of previous conversations. The prompt must be complete.
- **Missing skills** — if the job needs `second-brain` conventions, list it in `skills: [second-brain]`. The cron session won't load it automatically.
- **Not loading conventions** — for gbrain jobs, always include `skills: [second-brain]` so the agent knows how to properly write pages (citations, back-links, schema).
- **Changing job names** — `name` is the stable identity key. Changing it after creation creates a duplicate. Use `update_job` via the cronjob tool instead.
- **No error handling** — prompts should tell the agent what to do when things fail (Minions down, tool unavailable, empty results).
- **Overlapping schedules** — multiple jobs firing at the same time can conflict on gbrain writes. Space them out (e.g., `0 9 * * 1` vs `0 10 * * 1`).
- **Forgetting to sync** — editing config.yaml does NOT apply changes. You must run `sync.py`.
- **Using enabled_toolsets too restrictively** — if the job needs gbrain MCP tools, omit enabled_toolsets entirely (gives full tool access) or include the right ones.

## Existing Cron Jobs

| Job Name | Schedule | Description |
|----------|----------|-------------|
| `gbrain-contradictions` | Daily 9 AM | Scan for contradictory facts in gbrain |
| `gbrain-doctor` | Mon 9 AM | Full brain health dashboard |
| `gbrain-dream` | Nightly 2 AM | Autopilot maintenance (embed, backlinks, lint, purge) |
| `gbrain-orphans` | Sat 9 AM | List orphan pages for Coy's review |
| `gbrain-article-enrichment` | Sun 9 AM | Auto-enrich orphan articles by linking entities |

All defined in `/app/hermes_cron/config.yaml`. Managed via sync.py.
