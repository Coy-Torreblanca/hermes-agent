#!/usr/bin/env python3
"""
Reminder DB Poller — lifecycle-aware, runs every 5 min via cron script pre-processor.
Queries hermes.reminders for items needing alert (pending or delivered, next_remind_at due).
Sets status=delivered on first alert, bumps next_remind_at for re-alerts.
Outputs "NO_REMINDERS" when nothing is due (agent responds [SILENT]).
Outputs alerts text when reminders are due (agent relays verbatim).

Located at skills/coy/reminder-db/scripts/reminder_poll.py in the repo. Deployed to ~/.hermes/scripts/reminder_poll.py for the cron job.
"""
import os, sys, psycopg2

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    print("ERROR: DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Find reminders that need alerting RIGHT NOW:
    # - pending (never alerted) with next_remind_at <= now
    # - delivered (alerted but not done) with next_remind_at <= now (re-alert)
    cur.execute("""
        SELECT id, content, due_at, context, source, status, next_remind_at
        FROM hermes.reminders
        WHERE status IN ('pending', 'delivered')
          AND next_remind_at <= NOW()
        ORDER BY next_remind_at;
    """)
    rows = cur.fetchall()

    if not rows:
        print("NO_REMINDERS")
        conn.close()
        sys.exit(0)

    alerts = []
    for row in rows:
        rid, content, due_at_utc, context, source, status, next_at = row

        if status == 'pending':
            # First alert — mark delivered, set follow-up in 30 min
            tag = "🔔"
            cur.execute("""
                UPDATE hermes.reminders
                SET status = 'delivered',
                    delivered = TRUE,
                    delivered_at = NOW(),
                    next_remind_at = NOW() + INTERVAL '30 minutes'
                WHERE id = %s;
            """, (rid,))
        else:
            # Re-alert (was delivered but not done) — bump follow-up another 30 min
            tag = "🔁"
            cur.execute("""
                UPDATE hermes.reminders
                SET next_remind_at = NOW() + INTERVAL '30 minutes'
                WHERE id = %s;
            """, (rid,))

        line = f"{tag} {content}"
        if context:
            line += f"  ({context})"
        alerts.append(line)

    conn.commit()
    conn.close()

    if alerts:
        print("\n".join(alerts))

except Exception as e:
    print(f"POLL_ERROR: {e}", file=sys.stderr)
    sys.exit(1)
