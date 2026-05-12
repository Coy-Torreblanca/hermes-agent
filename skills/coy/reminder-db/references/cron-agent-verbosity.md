# Cron Agent Verbosity — Resolved May 4, 2026

## Problem
Cron agents always deliver their final response. Models (even DeepSeek v4) produce output when told to be silent. This caused empty-poll noise on the 5-minute reminder poller.

## Strategies tested (failed)

| # | Approach | Result |
|---|----------|--------|
| 1 | "Output nothing if no reminders" | 198-char explanation output |
| 2 | "Output [SILENT]" | `[SILENT]` delivered as message |
| 3 | "Output single 0" | `0` delivered as message |
| 4 | Script pre-processor + "don't respond" | `(empty)` or `[SILENT]` |
| 5 | `deliver: local` + separate delivery cron with `send_message` | System injects "do NOT use send_message" → blocked |

## Solution: System-level [SILENT] suppression

The cron system injects its own delivery instructions into EVERY cron agent's prompt:

> "SILENT: If there is genuinely nothing new to report, respond with exactly "[SILENT]" (nothing else) to suppress delivery. Never combine [SILENT] with content — either report your findings normally, or say [SILENT] and nothing more."

This means:
- `[SILENT]` response → system SUPPRESSES the Telegram delivery entirely
- Any other response → delivered as-is

## Validated architecture

Single cron job (`fec8ee1d67b6`, `Reminder DB — deliver alerts`):

```
schedule: */5 * * * *
deliver: origin  ← system suppresses [SILENT]
script: reminder_poll.py  ← pre-processor, outputs "NO_REMINDERS" or alerts
prompt: "If NO_REMINDERS → [SILENT]. If alerts → output them verbatim."
```

Verified with two manual runs:
- Alerts test (09:47): reminder fired → alert delivered to Telegram ✓
- Silence test (09:50): no reminders → agent responded [SILENT] → suppressed ✓

## Key insight

Do NOT fight the cron agent's verbosity. Use the system's built-in `[SILENT]` suppression mechanism. The framing is critical:
- ❌ "If nothing to say, respond with nothing" — model will still produce text
- ✅ "If no alerts, respond [SILENT]" — model complies, system suppresses it

The `[SILENT]` keyword is a CONTRACT with the cron delivery system, not just a model instruction. The system recognizes it and blocks the Telegram delivery.
