#!/usr/bin/env python3
"""
One-shot probe: lists today's Google Calendar events + all needsAction Google Tasks.

Outputs lines prefixed with CAL| and TASK| for easy parsing by cron agents.
Usage:
    python3 skills/coy/reminder-db/scripts/check_google_tasks_and_calendar.py

Requires: ~/.hermes/google_token.json (Google OAuth with Calendar + Tasks scopes)
Task list ID: MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow

Output format:
    CAL|<start_datetime>|<end_datetime>|<summary>|<location>
    TASK|<id>|<title>|<due_datetime>|<notes>
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from datetime import datetime, timezone, timedelta

creds = Credentials.from_authorized_user_file(os.path.expanduser("~/.hermes/google_token.json"))

# Calendar - today's events in CDT
svc = build("calendar", "v3", credentials=creds)
now_cdt = datetime.now(timezone(timedelta(hours=-5)))
start_of_day = now_cdt.replace(hour=0, minute=0, second=0, microsecond=0)
end_of_day = start_of_day + timedelta(hours=24)

events = svc.events().list(
    calendarId='primary',
    timeMin=start_of_day.isoformat(),
    timeMax=end_of_day.isoformat(),
    singleEvents=True,
    orderBy='startTime',
    timeZone='America/Chicago'
).execute()

for e in events.get('items', []):
    start = e['start'].get('dateTime', e['start'].get('date'))
    end = e['end'].get('dateTime', e['end'].get('date'))
    print(f"CAL|{start}|{end}|{e.get('summary','')}|{e.get('location','')}")

# Google Tasks - all active (needsAction) tasks
task_svc = build("tasks", "v1", credentials=creds)
LIST_ID = "MDY0OTg0ODYyMDU0MzgzMjQyMjU6MDow"
tasks = task_svc.tasks().list(tasklist=LIST_ID, showCompleted=False).execute()
for t in tasks.get("items", []):
    due = t.get('due', 'none')
    notes = t.get('notes', '')
    title = t.get('title', '').strip()
    if title:  # skip empty placeholder tasks
        print(f"TASK|{t['id']}|{title}|{due}|{notes}")
