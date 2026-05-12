# Reminder DB — Runtime Reference

Quick-reference for session agents. The canonical source is `reminder-db` SKILL.md.

## Cron Job

| Field | Value |
|-------|-------|
| Job ID | `fec8ee1d67b6` |
| Name | `Reminder DB — deliver alerts` |
| Schedule | `*/5 * * * *` (every 5 minutes) |
| Script | `reminder_poll.py` |
| Deliver | `origin` (Telegram) |
| Enabled toolsets | `["terminal"]` |
| Prompt | "If context is NO_REMINDERS → [SILENT]. If context has alerts → output them verbatim." |

## Database

| Field | Value |
|-------|-------|
| Connection | `DATABASE_URL` env var |
| Host | Railway Postgres (`postgres.railway.internal`) |
| Schema | `hermes` |
| Table | `hermes.reminders` |

## Quick Actions

```bash
# Poll manually
python3 skills/coy/reminder-db/scripts/reminder_poll.py

# View overdue
python3 -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT id, content, status, due_at FROM hermes.reminders WHERE status != ''done'' AND due_at <= NOW();')
for row in cur.fetchall(): print(f'#{row[0]} [{row[2]}] {row[1][:70]}')
conn.close()
"

# Mark done
python3 -c "import os, psycopg2; c=psycopg2.connect(os.environ['DATABASE_URL']); c.cursor().execute(\"UPDATE hermes.reminders SET status='done' WHERE id=N\"); c.commit()"

# Recreate cron job if lost
# See reminder-db SKILL.md → Architecture section for full config
```

## Files

| File | Location |
|------|----------|
| Poller script | `skills/coy/reminder-db/scripts/reminder_poll.py` |
| Cron definitions | `~/.hermes/cron/jobs.json` |
| Skill | `skills/coy/reminder-db/SKILL.md` |
