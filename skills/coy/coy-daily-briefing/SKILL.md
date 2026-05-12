---
name: coy-daily-briefing
description: "Daily briefing system for Coy — morning plan, afternoon check-in, evening wrap-up. Grooms inbox, checks sprint, integrates calendar, requires confirmation before action."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [daily, briefing, routine, planning, productivity]
    related_skills: [adjust-daily-schedule]
---

# Coy's Daily Briefing System

A three-part daily rhythm delivered via Telegram. Hermes proactively manages Coy's day — grooming his inbox, checking his sprint, integrating his calendar, and confirming plans before acting.

> **Consolidated May 2026:** The generic `daily-briefing` skill (briefing at 07:00/14:00/21:00) has been archived. Its unique content (edge cases, generic timeline) is preserved in `references/daily-briefing-generic-variant.md`. This Coy-specific skill is now the single authoritative daily briefing skill.

## Schedule

| Briefing | Time | Purpose |
|----------|------|---------|
| Morning | 4:15 AM | Groom inbox, propose plan, confirm |
| Afternoon | 2:00 PM | Check progress, course correct |
| Evening | 9:00 PM | Wrap up, what got done |


Coy wakes at 4:00 AM daily. The morning briefing fires at 4:15 AM to give him a few minutes to get oriented before the plan arrives.

## Morning Briefing

### What to check

1. **Inbox** (`/data/syncthing/Sync/org/inbox.org`) — any new items since yesterday?
2. **Sprint** (`/data/syncthing/Sync/org/work/tasks.org`) — current WIP, NEXT queue, sprint capacity
3. **Personal board** (`/data/syncthing/Sync/org/personal/personal.org`) — blocked items, deadlines, overdue
4. **Calendar** (Google Calendar via `google-workspace` skill) — today's events, time-bound commitments
5. **Yesterday's journal** (`journal/YYYY-MM-DD` in gbrain) — what was planned, what got done, what carried over
6. **Pending reminders** — check Google Tasks (task list `MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow`) for tasks due today or overdue. Use the probe script at `skills/coy/reminder-db/scripts/check_google_tasks_and_calendar.py`. Reminders migrated to Google Tasks on May 6, 2026 — Postgres `hermes.reminders` is no longer authoritative.

### Output format

```
☀️ Good morning, Coy. It's [time] on [day].

📥 INBOX — [N] new items:
  • [item 1]
  • [item 2]

🔥 CURRENTLY WORKING: [WIP task]

⏭️ NEXT UP: [next task]

📅 TODAY'S CALENDAR:
  • [time] — [event]
  • [time] — [event]

🔄 CARRIED OVER from yesterday: [items]

📋 PROPOSED PLAN:
  1. [task] — start with this
  2. [task] — next
  3. [task] — if time permits

Confirm this plan and I'll move inbox items to sprint/backlog.
```

### Confirmation flow

After sending the briefing, use **clarify** to get Coy's approval. He may:
- Confirm → move items, set first task to STARTED
- Adjust → modify the plan and re-confirm
- Defer → leave items in inbox for later

## Afternoon Check-In

### What to check

1. Current WIP — still in progress? Blocked?
2. What got done since morning?
3. **Calendar** — has Coy adjusted his schedule mid-day? Load `adjust-daily-schedule` skill and check Google Calendar for today's actual blocks. Don't assume the default template — Coy may have shifted breaks, lunch, or work blocks. The `adjust-daily-schedule` skill may have been used to delete and recreate blocks.
4. Any new items or shifts?

### Output format

```
☀️ Afternoon check-in, Coy. It's [time].

📅 TODAY'S SCHEDULE (as it currently stands):
  • [time] — [block]
  • [time] — [block]

✅ DONE TODAY:
  • [item]
  • [item]

🔥 STILL IN PROGRESS: [WIP]

📋 STILL PLANNED:
  • [item]
  • [item]

Need to course correct on anything?
```

## Evening Wrap-Up

### What to check

1. What got done today vs what was planned?
2. What carried over to tomorrow?
3. Any significant moments to journal?
4. **Calendar** — check actual bedtime block (🛌 Sleep). Coy may have adjusted it mid-day ("I'm going to bed at 10 tonight"). Compare to the 9 PM target.

### Output format

```
🌙 Evening wrap-up, Coy.

📅 TODAY'S ACTUAL BEDTIME: [time from calendar]

✅ COMPLETED: [N] tasks
🔄 CARRIED TO TOMORROW: [items]

💤 BEDTIME: What time did you get to bed? (9 PM target)

💡 Significant today: [key moments if any]

Rest well. I'll be here tomorrow at 4:15 AM.
```
## Cron Job Setup

Three cron jobs drive this system. Create them with `cronjob action='create'`.

**Delivery targets**: Jobs deliver to Discord channels (preferred) or Telegram. See `coy-sprint` skill's `references/discord-delivery.md` for the current channel mapping.

### Morning Briefing Job
- **Name**: `Daily Briefing — Morning`
- **Schedule**: `15 9 * * *`
- **Prompt**: "Deliver Coy's morning briefing. Load coy-daily-briefing and coy-sprint skills. Follow the Morning Briefing format. Check inbox, sprint, personal board, calendar, and yesterday's journal. Propose a plan. End by asking for confirmation using clarify."
- **Skills**: `coy-daily-briefing`, `coy-sprint`, `google-workspace`
- **Target**: `discord:#daily-briefing`

### Afternoon Check-In Job
- **Name**: `Daily Briefing — Afternoon`
- **Schedule**: `0 19 * * *`
- **Prompt**: "Deliver Coy's afternoon check-in. Load coy-daily-briefing, coy-sprint, adjust-daily-schedule, and google-workspace skills. Follow the Afternoon Check-In format. Pull today's calendar to show actual schedule blocks — Coy may have adjusted mid-day."
- **Skills**: `coy-daily-briefing`, `coy-sprint`, `adjust-daily-schedule`, `google-workspace`
- **Target**: `discord:#daily-briefing`

### Evening Wrap-Up Job
- **Name**: `Daily Briefing — Evening`
- **Schedule**: `0 2 * * *`
- **Prompt**: "Deliver Coy's evening wrap-up. Load coy-daily-briefing, coy-sprint, and google-workspace skills. Follow the Evening Wrap-Up format. Check today's calendar for the actual 🛌 Sleep block time — Coy may have adjusted bedtime mid-day."
- **Skills**: `coy-daily-briefing`, `coy-sprint`, `google-workspace`
- **Target**: `discord:#journal` (when created) or `discord:#daily-briefing`

## Rules

1. **Never move items without confirmation.** The briefing proposes — Coy decides.
2. **Always check both inboxes** — WorkInbox AND PersonalInbox.
3. **Respect single WIP.** Never propose starting a new task if one is already STARTED.
4. **Calendar-aware.** If Coy has a 10 AM meeting, don't propose a 3-point task for the morning.
5. **Sabbath mode.** If it's Friday evening through Saturday evening, skip briefings or switch to quiet mode.
6. **Personal items get priority too.** Don't only focus on work sprint — personal board matters equally.
7. **Mid-day schedule adjustments.** Coy may have used `adjust-daily-schedule` to shift his calendar blocks during the day. Always pull today's actual calendar before proposing capacity or time estimates. Don't assume the default template is still accurate after 9 AM.

## Deployment Status (May 6, 2026)

**Google Calendar auth is WORKING.** The `google-workspace` skill can pull Coy's calendar.

Currently running:
- **6AM Work Triage** (`cd0827974b9b`, Mon-Fri): Now loads `coy-sprint` + `google-workspace`. Pulls calendar, checks inbox, checks sprint, then asks Coy about email/Teams. This is still a stopgap — it does inbox grooming but does NOT do full sprint planning, personal board review, or yesterday's journal.

**Full morning briefing NOT yet deployed.** When deployed, it should:
- Load: `coy-daily-briefing`, `coy-sprint`, `google-workspace`
- Check: inbox, sprint, personal board, calendar, yesterday's journal, pending reminders
- Propose a full plan and ask for confirmation via clarify
- The 6AM Work Triage would then be folded into it (or paused).
