#!/bin/bash
# Cron Setup — Run after fresh Railway deploy to recreate all cron jobs.
# Usage: bash skills/coy/setup-crons.sh
# Requires: Hermes CLI available as 'hermes' in PATH.

set -e

echo "=== Setting up Coy's cron jobs ==="

# --- Active Daily Crons ---

# 1. 6AM Work Triage (Mon-Fri)
hermes cron add \
  --name "6AM Work Triage — Mon-Fri" \
  --skill coy-sprint \
  --schedule "0 6 * * 1-5" \
  --deliver "discord:#daily-briefing" \
  --prompt "It's 6 AM CDT on a workday. Deliver Coy's morning work triage.

STEPS:
1. Pull today's Google Calendar events and active Google Tasks using the probe script at skills/coy/reminder-db/scripts/check_google_tasks_and_calendar.py.
2. Read the current sprint dashboard from /data/syncthing/Sync/org/work/tasks.org using org_query.py.
3. Check for any DEADLINE items due today in both work and personal org files.
4. Check infrastructure: run cronjob list to verify all crons are healthy. Flag any paused or failed crons.
5. Present a concise morning briefing: today's schedule, active sprint task, deadlines, and any infrastructure alerts.
6. Deliver to #daily-briefing."

echo "✓ 6AM Work Triage"

# 2. Org refile: inbox → tasks/personal (Mon-Fri, 8 PM)
hermes cron add \
  --name "Org refile: inbox → tasks/personal" \
  --skill coy-sprint \
  --schedule "0 20 * * 1-5" \
  --model deepseek-v4-flash \
  --deliver "discord:#daily-briefing" \
  --prompt "You are Coy's org-mode triage agent. Your job: check inbox.org for uncategorized items, then present refile proposals.

STEPS:
1. Read /data/syncthing/Sync/org/inbox.org to see current uncategorized items.
2. For each item, read the workflow reference files at /data/syncthing/Sync/org/ (task_workflow.md, sprint_workflow.md, agenda_workflow.md, inbox.md).
3. Present each item as a refile proposal with the exact org-mode text that would be written to the destination file, including proposed POINTS, VALUE, SPRINT, and GOAL.
4. Present as proposals only — do NOT modify any org files. Wait for Coy's approval.
5. Deliver to #daily-briefing."

echo "✓ Org refile"

# 3. Nightly Journal Recap (1 AM UTC = 8 PM CDT)
hermes cron add \
  --name "Nightly Journal Recap" \
  --skill coy-journal \
  --schedule "0 1 * * *" \
  --model deepseek-v4-pro \
  --deliver "discord:#coach" \
  --prompt "It's 8 PM CDT. Post Coy's end-of-day journal recap to #coach.

STEPS:
1. Get today's date in CDT (America/Chicago timezone).
2. Read today's journal entry from /data/syncthing/Sync/org/ if it exists.
3. Check gbrain for any timeline entries or pages created/updated today.
4. Compile a brief end-of-day recap: what Coy worked on, key decisions, mood, health notes, and any patterns worth flagging.
5. If no journal entry exists for today, ask Coy if he wants to do a quick recap.
6. Deliver to #coach."

echo "✓ Nightly Journal Recap"

# 4. RSS daily scan (4 AM)
hermes cron add \
  --name "RSS daily scan" \
  --skill blogwatcher \
  --schedule "0 4 * * *" \
  --deliver "discord:#rss" \
  --toolsets terminal \
  --prompt "Run RSS scan on all 11 feeds and report new articles to Coy.

1. Run: BLOGWATCHER_DB=/data/.blogwatcher-cli/blogwatcher-cli.db blogwatcher scan
2. Check for new articles since last scan.
3. Summarize new articles with title, source, and why Coy might want to read them.
4. Deliver to #rss."

echo "✓ RSS daily scan"

# 5. Changelog RSS regeneration (every 6 hours)
hermes cron add \
  --name "Changelog RSS regeneration" \
  --schedule "0 */6 * * *" \
  --deliver local \
  --toolsets terminal,file \
  --prompt "Regenerate the Hermes changelog RSS feed.

Run: python3 ~/.hermes/scripts/changelog_rss.py

Output goes to ~/.hermes/www/changelog.xml. Verify the file was written and contains valid XML."

echo "✓ Changelog RSS"

# 6. Daily Bible verse for Dad (8 AM)
hermes cron add \
  --name "Daily Bible verse for Dad" \
  --schedule "0 8 * * *" \
  --deliver origin \
  --prompt "Remind Coy to send his father Javier a Bible verse today. Javier specifically asked Coy to send him daily Bible verses and prayers, and Coy made a personal commitment to do this.

Check gbrain for the evangelism-tracking page to see what verses have been sent recently and what Javier has responded to. Suggest a verse that would be meaningful based on what Javier has engaged with. Remind Coy that Javier prefers accessible, encouraging verses (like Proverbs) over dense prophetic passages."

echo "✓ Daily Bible verse for Dad"

# 7. Plan for Max's July 9 visit (monthly, June 1 onward)
hermes cron add \
  --name "Plan for Max's July 9 visit" \
  --schedule "0 9 1 6 *" \
  --deliver origin \
  --prompt "Remind Coy to plan for Max Trussell's arrival. Max flies in on Thursday, July 9, 2026: OAK → DAL (11:25 AM - 5:15 PM). He stays through Sunday July 12.

Check if Coy has made any preparations: accommodations, activities, meals, transport. If nothing is planned yet, suggest starting with lodging and a loose itinerary."

echo "✓ Plan for Max's visit"

# --- Paused Crons (created but disabled) ---

# 8. Nightly gbrain sync (paused — needs Minions worker)
hermes cron add \
  --name "Nightly git diff → gbrain sync" \
  --skill gbrain \
  --schedule "0 7 * * *" \
  --model deepseek-v4-flash \
  --deliver "discord:#gbrain" \
  --paused \
  --prompt "You are a nightly sync agent. Your job: detect changed files in /data/syncthing/Sync/ and ingest them into gbrain.

STEPS:
1. Run gbrain sync_brain with --repo /data/syncthing/Sync --no-embed.
2. Report which files changed and were ingested.
3. If sync fails, log friction and report the error.
4. Deliver to #gbrain."

echo "✓ Nightly gbrain sync (paused)"

# 9. FULL gbrain sync baseline (paused — one-shot, run manually)
hermes cron add \
  --name "FULL gbrain sync (baseline)" \
  --skill gbrain \
  --schedule "once at 2026-05-07 06:00" \
  --model deepseek-v4-flash \
  --deliver local \
  --paused \
  --prompt "You are running the initial full gbrain sync for /data/syncthing/Sync/.

STEPS:
1. cd /data/syncthing/Sync
2. Run gbrain import with --no-embed flag.
3. Report pages created, updated, and any errors.
4. Verify pages contain real content (not header-only stubs)."

echo "✓ FULL gbrain sync (paused)"

echo ""
echo "=== All 9 cron jobs created ==="
echo "Active: 7 (6AM Triage, Org Refile, Journal Recap, RSS, Changelog, Bible Verse, Max Visit)"
echo "Paused: 2 (gbrain sync, FULL gbrain sync)"
echo ""
echo "Run 'hermes cron list' to verify."
