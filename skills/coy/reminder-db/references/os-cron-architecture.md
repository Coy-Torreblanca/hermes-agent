# OS-Level Cron Architecture (Cost Elimination)

**Decision:** Move reminder polling from Hermes cron agent to OS-level cron.

## Current (expensive)
```
Hermes cron (*/5 min) → spins up agent → runs reminder_poll.py as pre-processor
                                           ↓
                                     agent reads output
                                           ↓
                                     NO_REMINDERS → agent outputs [SILENT] → suppressed
                                     alerts found → agent delivers to Telegram
```
288 sessions/day. ~95% are [SILENT] — but EVERY one burns tokens (system prompt + context).

## Target (zero silent cost)
```
OS cron (*/5 or */15 min) → runs reminder_poll.py directly
                                      ↓
                                no alerts → exit (zero tokens, no agent)
                                alerts found → wake Hermes → deliver
```
Only spins up Hermes when there's something to deliver. ~2-4 sessions/day.

## Root cause confirmation
May 5, 2026: Carlton deployed a fresh container → zero overnight token usage. Confirms cost is from Coy's post-deploy additions (cron jobs), not the base deployment.

## Implementation notes
- Script already works standalone: `python3 reminder_poll.py` with DATABASE_URL set
- Need a mechanism to "wake Hermes" when alerts exist: Hermes CLI send, API call, or file-based trigger
- OS crontab entry: `*/15 * * * * cd /path && python3 reminder_poll.py`
- Keep existing Hermes cron job running until OS cron validated
