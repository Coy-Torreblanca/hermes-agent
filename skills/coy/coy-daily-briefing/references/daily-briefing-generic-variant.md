# Daily Briefing — Generic Variant (absorbed from daily-briefing skill)

This is the original generic daily-briefing skill that preceded `coy-daily-briefing`. The Coy-specific version (`coy-daily-briefing`) is the authoritative skill. This reference preserves the generic variant's unique content that wasn't replicated in coy-daily-briefing.

## Edge Cases (from generic variant — supplement coy-daily-briefing)

### Coy messages after missing a briefing
If he messages at 10 AM and the 7 AM briefing already fired:
- Acknowledge the time
- Deliver the morning briefing NOW (same format)
- "You're up. Here's the morning briefing — it already went out but here it is again."

### No new inbox items
Skip the inbox section. "📥 INBOX — nothing new."

### Sprint is empty or stale
Note it: "⚡ Sprint looks thin — [X]/16 committed. Want to pull from backlog?"

### Google Calendar not set up
Skip calendar section. Note once per week: "📅 Google Calendar not connected — set up when ready."

## Integration Points (generic variant)

- **coy-sprint**: Sprint dashboard, inbox grooming, task state changes
- **coy-journal**: All briefings get journaled as timeline entries
- **google-workspace**: Calendar events (optional, requires OAuth setup)
- **gbrain**: Day's plan and outcomes go to `journal/YYYY-MM-DD`

## Rules (generic variant)

1. **Confirm before pushing** — never move inbox items or change sprint state without Coy's confirmation
2. **Brief, not verbose** — the briefing is a dashboard, not a conversation. Coy confirms, you act.
3. **Sabbath override always wins** — no briefing, no plan, no nudge on Sabbath
4. **Journal everything** — every briefing interaction gets a timeline entry
5. **Time-aware** — all times use system time. Adjust cron accordingly.

## Timeline (generic variant)

| Time | Event | Delivery |
|---|---|---|
| 07:00 | Morning briefing | Cron → Telegram |
| 14:00 | Afternoon check-in | Cron → Telegram |
| 21:00 | Evening wrap-up | Cron → Telegram |

**Note:** coy-daily-briefing uses different times (04:15, 14:00, 21:00) to match Coy's 4 AM wake schedule. The generic variant's 07:00 morning time was designed for a standard schedule.
