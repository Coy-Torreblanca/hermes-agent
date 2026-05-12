# Sleep & Consequence Tracking Workflow

How to map Coy's actual sleep patterns using session logs and gbrain.

## When to Use

- Coy reports oversleeping or missing a morning commitment
- Coy expresses frustration about wake time
- You're doing a morning briefing and notice he's late
- He asks you to "track consequences"

## Data Sources

| Source | What it tells you | How to query |
|--------|-------------------|--------------|
| `session_search` | Actual last activity time each night | `session_search(query="May 03 OR May 04")` |
| `memory` | Stated bedtimes, wake times, commitments | Search for `sleep` or `wake` |
| `gbrain` sleep-patterns page | Cumulative log of all oversleep events | `mcp_gbrain_query(query="sleep patterns oversleep")` |

## Procedure

### 1. Map Actual Bedtimes

Use `session_search` to find the LAST user-initiated session each night (ignore cron jobs). The timestamp of the last Telegram or TUI session is the *earliest possible* bedtime — actual bedtime is later.

**Key insight:** Coy's claimed bedtime often doesn't match his actual last activity. Always compare:
- Claimed bedtime (what he says)
- Actual last activity (session timestamp)
- Wake time (when he first messages)

### 2. Calculate Sleep Debt

For each night, compute:
- **Max possible sleep** = wake time − last activity time
- **Actual sleep** = unknown (we can't measure), but max possible is an upper bound

Accumulate across 3+ nights. If max possible sleep is consistently below 6 hours, his body will eventually force a correction (crash sleep).

### 3. Log to gbrain

Update `/gbrain/sleep-patterns` with:
- Date
- Claimed bedtime vs actual last activity
- Wake time
- Max possible sleep
- Consequences (missed Bible study, late to work, etc.)
- Root cause assessment

### 4. Set Defensive Reminders

If no bedtime reminder exists, create one via `reminder-db`:
- **Time:** 8:30 PM (wind-down starts, lights out by 8:45)
- **Recurrence:** daily
- **Content:** "Wind down for bed — lights out by 8:45 PM for 4 AM wake"
- **Context:** Link to gbrain sleep-patterns page

## Example from May 5, 2026

| Night | Last Activity | Wake | Max Sleep | Notes |
|-------|---------------|------|-----------|-------|
| May 2→3 (Sat) | 10:53 PM (TUI, 30ai work) | unknown | ~5h max | Weekend, working late |
| May 3→4 (Sun) | 4:33 PM (MTG summary) | unknown | unknown | Blank — no late activity logged |
| May 4→5 (Mon) | 8:06 PM (TUI, Seph) → bed 9:30 PM | 6:00 AM | ~8.5h actual | Body collected weekend debt |

Cumulative debt from Saturday's 5-hour night + unknown Sunday, collected on Monday despite reasonable bedtime. Crashed through 4 AM alarm to 6 AM.

Consequences: Missed Bible study, late to work.

## Pitfalls

- **Don't trust claimed bedtimes** — compare claimed bedtime against last session activity
- **Ignore cron sessions** — only user-initiated sessions (telegram, tui) matter for bedtime
- **Don't reassure** — when Coy says "I reap what I sow," agree and show the data. See coy-sprint skill's "Accountability — Consequence Tracking" section.
