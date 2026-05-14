# Cron Job Manifest

> Generated 2026-05-14. Snapshot of all Hermes cron jobs for Personal AI.
> Source of truth: `config.yaml` (for config-present jobs) + `cronjob(action='list')` (for runtime state).

## Current Jobs (6 total)

| # | Job Name | Schedule | Delivery | Config Present | Last Run | Status |
|---|----------|----------|----------|----------------|----------|--------|
| 1 | `gbrain-contradictions` | Daily `0 9 * * *` | `discord:home` | ✅ | 2026-05-14 | ❌ Error (delivery) |
| 2 | `gbrain-doctor` | Mon `0 9 * * 1` | `discord` | ✅ | Never | ⏳ First run 2026-05-18 |
| 3 | `gbrain-dream` | Nightly `0 2 * * *` | `discord:home` | ✅ | 2026-05-14 | ✅ Ran but delivery broken |
| 4 | `gbrain-orphans` | Sat `0 9 * * 6` | `discord` | ✅ | Never | ⏳ First run 2026-05-16 |
| 5 | `gbrain-article-enrichment` | Sun `0 9 * * 0` | `discord` | ❌ Created via cronjob tool | Never | ⏳ First run 2026-05-17 |
| 6 | `personalai-healthcheck` | Daily `0 6 * * *` | `discord:home` | ✅ | Never | ⏳ First run 2026-05-15 |

## Delivery Channel Key

| Destination Format | Meaning |
|-------------------|---------|
| `discord` | Home Discord channel (default) |
| `discord:home` | Discord channel ID `1501428244833108018` |
| `discord:#channel-name` | Named Discord channel (⚠️ fragile — channel must exist) |

## Known Issues

1. **gbrain-contradictions** and **gbrain-dream** both had delivery to `discord:#daily-briefing`
   which returned 404 (channel doesn't exist). Fixed 2026-05-14 to `discord:home`.
   Verify next run succeeded.
2. **gbrain-article-enrichment** was created via `cronjob(action='create')` but never
   added to `config.yaml`. Sync.py is one-directional (config → state), so this job
   runs from Hermes cron state but is invisible to the config. To fix, copy its
   definition into config.yaml and run sync.py.
3. **gbrain-dream** ran at 2 AM on 2026-05-14 with status "ok" but its actual
   operations (embed, backlinks, lint, purge) require the Minions worker which
   isn't running (`/app/gbrain_minions.sh` missing from disk). The cron job's
   prompt should detect this and report it.

## Health Check

The `personalai-healthcheck` job runs `/app/healthcheck.sh` (when deployed) which
probes 6 categories: supervisor processes, cron jobs, gbrain health, database,
volume/disk, and gateway/API. It reports to Discord daily at 6 AM.

For the full health check system design, see `projects/second-brain` in gbrain.
