#!/usr/bin/env python3
"""
habit_query.py — Dedicated org-mode habit parser.

Reads, toggles, and tracks habits in habits.org and sprint_habits.org.
Completely separate from org_query.py — habits have their own syntax
(SCHEDULED repeaters, STYLE markers, LOGBOOK state history) that doesn't
fit the EPIC/STORY/TODO hierarchy parser.

Commands:
  --list             Show all habits with status
  --toggle <title>   Mark a habit DONE for today
  --overdue          Show habits past their SCHEDULED date
  --due-today        Show habits due today
  --streak <title>   Count consecutive DONE days from LOGBOOK
  --add <json>       Create a new habit
  --reschedule <title> <YYYY-MM-DD> [repeater]
                     Change a habit's SCHEDULED date (optionally repeater)
  --help             This message

Usage:
  habit_query.py [file] --list
  habit_query.py [file] --toggle "Bible study"
  habit_query.py [file] --add '{"title":"Morning Prayer","schedule":"+1d"}'
  habit_query.py [file] --reschedule "Bible study" 2026-06-01

If no file is given, reads /data/syncthing/Sync/org/personal/habits.org
"""

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from typing import Optional

HABITS_FILE = os.path.expanduser(
    "/data/syncthing/Sync/org/personal/habits.org"
)
SPRINT_HABITS_FILE = os.path.expanduser(
    "/data/syncthing/Sync/org/work/sprint_habits.org"
)

# ── Scheduled line parsing ─────────────────────────────────────────────
SCHEDULED_RE = re.compile(
    r'^\s*SCHEDULED:\s*<(?P<date>\d{4}-\d{2}-\d{2})\s+\w+\s*(?P<repeater>[^>]*)>'
)
STATE_RE = re.compile(
    r'-\s+State\s+"DONE"\s+from\s+"\w+"\s+\[(?P<ts>[^\]]+)\]'
)
HEADING_RE = re.compile(r'^(\*+)\s+(TODO|STORY|DONE)\s+(.*)$')
PROP_START_RE = re.compile(r'^\s*:PROPERTIES:\s*$')
PROP_END_RE = re.compile(r'^\s*:END:\s*$')
PROP_RE = re.compile(r'^\s*:(?P<key>[A-Z_]+):\s+(?P<val>.*)$')

REPEATER_PATTERNS = {
    '+1d': 'daily',
    '.+1d/2d': 'daily (weekdays)',
    '+1w': 'weekly',
    '+2w': 'biweekly',
    '++2w/21d': 'biweekly',
    '+1m': 'monthly',
}


def parse_habits(text: str) -> list[dict]:
    """Parse org-mode habits file into structured habit list.

    Each habit is a dict with keys: heading, keyword, priority, scheduled,
    repeater, style, last_repeat, title, body, logbook, line.
    """
    habits = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        m = HEADING_RE.match(line)
        if not m:
            i += 1
            continue

        stars = m.group(1)
        keyword = m.group(2)
        remainder = m.group(3).strip()

        # Extract priority cookie
        priority = None
        prio_m = re.match(r'\[#(A|B|C)\]\s*(.*)', remainder)
        if prio_m:
            priority = prio_m.group(1)
            title = prio_m.group(2).strip()
        else:
            title = remainder

        # Strip tags from title
        title = re.sub(r'\s+:[\w:-]+:\s*$', '', title).strip()
        title = re.sub(r'^:[\w:-]+:\s+', '', title).strip()

        heading_line = i

        # Collect lines until next heading at same or lower level
        scheduled = None
        repeater = None
        style = None
        last_repeat = None
        habit_id = None
        props = {}
        in_props = False
        body_lines = []
        logbook = []
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            # Stop at next heading with same or fewer stars
            next_m = HEADING_RE.match(next_line)
            if next_m and len(next_m.group(1)) <= len(stars):
                break

            # SCHEDULED line (appears before properties)
            sched_m = SCHEDULED_RE.match(next_line)
            if sched_m:
                scheduled = sched_m.group('date')
                rep_raw = sched_m.group('repeater').strip()
                repeater = REPEATER_PATTERNS.get(rep_raw, rep_raw)
                j += 1
                continue

            # Properties drawer
            if PROP_START_RE.match(next_line):
                in_props = True
                j += 1
                continue
            if PROP_END_RE.match(next_line):
                in_props = False
                j += 1
                continue
            if in_props:
                prop_m = PROP_RE.match(next_line)
                if prop_m:
                    k = prop_m.group('key')
                    v = prop_m.group('val').strip()
                    props[k] = v
                    if k == 'STYLE':
                        style = v
                    elif k == 'LAST_REPEAT':
                        last_repeat = v
                    elif k == 'ID':
                        habit_id = v
                j += 1
                continue

            # State transitions (LOGBOOK entries, inline)
            state_m = STATE_RE.search(next_line)
            if state_m:
                logbook.append(state_m.group('ts'))
                j += 1
                continue

            # Empty lines between blocks
            if next_line.strip() == '' and not body_lines:
                j += 1
                continue

            # Body text
            body_lines.append(next_line)
            j += 1

        if style == 'habit' or style is None:
            # Accept heading-level habits even without :STYLE:
            # (some sprint habits may be nested differently)
            habits.append({
                'heading_line': heading_line,
                'keyword': keyword,
                'priority': priority,
                'title': title,
                'scheduled': scheduled,
                'repeater': repeater,
                'style': style,
                'last_repeat': last_repeat,
                'id': habit_id,
                'logbook': logbook,
                'body': '\n'.join(body_lines).strip(),
                'line': heading_line + 1,  # 1-indexed line
            })
        i = j
    return habits


def parse_date(d: str) -> Optional[date]:
    """Parse YYYY-MM-DD string to date."""
    try:
        return datetime.strptime(d, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_logbook_timestamp(ts: str) -> Optional[date]:
    """Parse org-mode timestamp like '2026-04-18 Sat 04:45' to date."""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', ts)
    if m:
        return parse_date(m.group(1))
    return None


def compute_streak(logbook: list[str]) -> int:
    """Count consecutive DONE days from newest to oldest.

    Given timestamps ['2026-05-15 Thu 10:00', '2026-05-14 Wed 09:00'],
    returns 2 if they're consecutive calendar days.
    """
    dates = sorted(
        [d for d in (parse_logbook_timestamp(t) for t in logbook) if d],
        reverse=True
    )
    if not dates:
        return 0

    streak = 1
    for i in range(len(dates) - 1):
        if (dates[i] - dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def habit_status(h: dict, today: date) -> str:
    """Determine habit status: overdue, due-today, done-today, upcoming, no-schedule."""
    if not h['scheduled']:
        return 'no-schedule'

    sched = parse_date(h['scheduled'])
    if not sched:
        return 'no-schedule'

    # Check if DONE today
    done_dates = [
        d for d in
        (parse_logbook_timestamp(t) for t in h['logbook'])
        if d == today
    ]
    if done_dates:
        return 'done-today'

    if today > sched:
        return 'overdue'
    if today == sched:
        return 'due-today'
    return 'upcoming'


def list_habits(filepath: str) -> list[dict]:
    """Parse and annotate all habits with status and streak."""
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        text = f.read()
    habits = parse_habits(text)
    today = date.today()
    for h in habits:
        h['status'] = habit_status(h, today)
        h['streak'] = compute_streak(h['logbook'])
    return habits


def format_habit(h: dict) -> str:
    """Format habit for display."""
    status_icons = {
        'overdue': '🔴',
        'due-today': '🟡',
        'done-today': '✅',
        'upcoming': '⏳',
        'no-schedule': '⚪',
    }
    icon = status_icons.get(h['status'], '⚪')
    prio_tag = f"[#{h['priority']}] " if h['priority'] else ""
    sched = f"  SCHEDULED: <{h['scheduled']}>" if h['scheduled'] else ""
    rep = f" ({h['repeater']})" if h['repeater'] else ""
    streak = f" 🔥{h['streak']}d" if h['streak'] > 1 else ""
    return f"{icon} {prio_tag}{h['title']}{sched}{rep}{streak}"


def find_habit(habits: list[dict], title_query: str) -> Optional[dict]:
    """Find habit by partial title match."""
    query = title_query.lower()
    for h in habits:
        if query in h['title'].lower():
            return h
    return None


# ── Mutating operations ────────────────────────────────────────────────

def reschedule_habit(filepath: str, title_query: str,
                     new_date: str,
                     new_repeater: Optional[str] = None) -> dict:
    """Change the SCHEDULED date (and optionally repeater) of a habit.

    Args:
        filepath: Path to the habits.org/sprint_habits.org file.
        title_query: Partial title to match the habit.
        new_date: New SCHEDULED date in YYYY-MM-DD format.
        new_repeater: Optional new repeater (e.g. '+1w', '++2w/21d').
            If omitted, the existing repeater is preserved.

    Returns:
        dict with rescheduled status, title, old/new scheduled, repeater.
    """
    habits = list_habits(filepath)
    habit = find_habit(habits, title_query)
    if not habit:
        return {'error': f'Habit matching "{title_query}" not found'}

    parsed_date = parse_date(new_date)
    if not parsed_date:
        return {'error': f'Invalid date: "{new_date}". Use YYYY-MM-DD format.'}

    day_name = parsed_date.strftime('%A')

    with open(filepath) as f:
        lines = f.readlines()

    # Walk through habits to find the target
    in_habit = False
    habit_stars = None
    updated = False
    old_scheduled = None
    old_repeater = None

    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            if not in_habit and habit['title'].lower() in m.group(3).lower():
                in_habit = True
                habit_stars = len(m.group(1))
                continue
            elif in_habit and len(m.group(1)) <= habit_stars:
                break

        if in_habit:
            sched_m = SCHEDULED_RE.match(line)
            if sched_m:
                old_scheduled = sched_m.group('date')
                old_repeater = sched_m.group('repeater').strip()
                repeater = new_repeater if new_repeater else old_repeater
                lines[i] = f'   SCHEDULED: <{new_date} {day_name} {repeater}>\n'
                updated = True
                break

    if not updated:
        return {'error': 'Could not find SCHEDULED line for habit'}

    with open(filepath, 'w') as f:
        f.writelines(lines)

    return {
        'rescheduled': True,
        'title': habit['title'],
        'old_scheduled': old_scheduled,
        'new_scheduled': new_date,
        'repeater': REPEATER_PATTERNS.get(new_repeater, new_repeater)
            if new_repeater else habit['repeater'],
    }


def toggle_habit(filepath: str, title_query: str) -> dict:
    """Mark a habit DONE for today by adding a LOGBOOK entry
    AND advancing the SCHEDULED date per the repeater pattern."""
    habits = list_habits(filepath)
    habit = find_habit(habits, title_query)
    if not habit:
        return {'error': f'Habit matching "{title_query}" not found'}

    today_str = datetime.now().strftime('%Y-%m-%d %a %H:%M')
    # Use 3-space indent to match existing org-mode LOGBOOK convention
    state_line = f'   - State "DONE"       from "{habit["keyword"]}"       [{today_str}]\n'

    today_date = date.today()

    with open(filepath) as f:
        lines = f.readlines()

    # Find the end of properties drawer for this habit
    # Insert right after :END: line
    in_habit = False
    habit_stars = None
    insert_at = None
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            if habit['title'].lower() in m.group(3).lower():
                in_habit = True
                habit_stars = len(m.group(1))
                continue
            elif in_habit and len(m.group(1)) <= habit_stars:
                # Next sibling heading — stop
                break
        if in_habit and PROP_END_RE.match(line):
            insert_at = i + 1  # Insert after :END:
            break

    if insert_at is None:
        return {'error': 'Could not find properties drawer end for habit'}

    # Insert the state line right after :END:
    lines.insert(insert_at, state_line)

    # Now advance the SCHEDULED date according to the repeater pattern
    advance_date = None
    for i, line in enumerate(lines):
        sched_m = SCHEDULED_RE.match(line)
        if sched_m:
            raw_repeater = sched_m.group('repeater').strip()
            if raw_repeater == '+1d':
                advance_date = today_date + timedelta(days=1)
            elif raw_repeater == '.+1d/2d':
                # Advance to next weekday (skip Sat/Sun)
                next_day = today_date + timedelta(days=1)
                while next_day.weekday() >= 5:  # 5=Sat, 6=Sun
                    next_day += timedelta(days=1)
                advance_date = next_day
            elif raw_repeater in ('+1w', '++2w/21d'):
                advance_date = today_date + timedelta(days=7)
            elif raw_repeater == '+2w':
                advance_date = today_date + timedelta(days=14)
            elif raw_repeater == '+1m':
                # Advance to next month, same day (or last day of next month)
                month = today_date.month + 1
                year = today_date.year
                if month > 12:
                    month = 1
                    year += 1
                try:
                    advance_date = today_date.replace(year=year, month=month)
                except ValueError:
                    # Day overflow — use last day of next month
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    advance_date = today_date.replace(year=year, month=month, day=last_day)
            else:
                # Unknown repeater — skip advancement
                pass

            if advance_date:
                day_name = advance_date.strftime('%A')
                lines[i] = f'   SCHEDULED: <{advance_date.strftime("%Y-%m-%d")} {day_name} {raw_repeater}>\n'
            break

    with open(filepath, 'w') as f:
        f.writelines(lines)

    return {'toggled': True, 'title': habit['title'], 'time': today_str}


def add_habit(filepath: str, params: dict) -> dict:
    """Add a new habit to the file.

    Required: title
    Optional: schedule (e.g. '+1w'), body, priority
    """
    title = params.get('title', '').strip()
    if not title:
        return {'error': 'title is required'}

    schedule = params.get('schedule', '+1w')
    body = params.get('body', '').strip()
    priority = params.get('priority', '')

    # Determine next SCHEDULED date
    today = date.today()
    # Default to next week on same day
    if schedule == '+1d':
        sched_date = today + timedelta(days=1)
    elif schedule in ('+1w', '.+1d/2d'):
        sched_date = today + timedelta(days=7)
    elif schedule == '+1m':
        # Next month, same day
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year += 1
        try:
            sched_date = today.replace(year=year, month=month)
        except ValueError:
            sched_date = today + timedelta(days=30)  # fallback
    else:
        sched_date = today

    day_name = sched_date.strftime('%A')
    sched_str = sched_date.strftime(f'%Y-%m-%d {day_name}')

    prio_tag = f' [#{priority}]' if priority else ''
    emoji = params.get('emoji', '')

    block = (
        f'* TODO{prio_tag} {emoji} {title}\n'
        f'  SCHEDULED: <{sched_str} {schedule}>\n'
        f'  :PROPERTIES:\n'
        f'  :STYLE:    habit\n'
        f'  :END:\n'
    )
    if body:
        block += '\n' + '\n'.join(f'  {line}' for line in body.split('\n')) + '\n'
    block += '\n'

    with open(filepath, 'a') as f:
        f.write(block)

    return {
        'added': True,
        'title': title,
        'scheduled': sched_str,
        'schedule': schedule,
        'file': filepath,
    }


# ── CLI ────────────────────────────────────────────────────────────────

def usage():
    print(__doc__.strip())
    sys.exit(0)


def main():
    # Determine file path
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a != sys.argv[0]]
    commands = [a for a in sys.argv[1:] if a.startswith('--')]

    filepath = HABITS_FILE
    non_flag_args = []
    for a in sys.argv[1:]:
        if a.startswith('--') or a.startswith('-'):
            continue
        if not non_flag_args and (a.endswith('.org') or '/' in a):
            filepath = a
        else:
            non_flag_args.append(a)

    if not commands or '--help' in commands:
        usage()

    cmd = commands[0]

    if cmd == '--list':
        habits = list_habits(filepath)
        output = []
        for h in habits:
            output.append(format_habit(h))
            if h['body']:
                output.append(f"    {h['body'][:100]}")
        print(json.dumps({
            'habits': [
                {
                    'title': h['title'],
                    'status': h['status'],
                    'streak': h['streak'],
                    'scheduled': h['scheduled'],
                    'repeater': h['repeater'],
                    'body': h['body'][:200],
                }
                for h in habits
            ],
            'display': '\n'.join(output),
        }, indent=2))
        return

    if cmd == '--overdue':
        habits = [h for h in list_habits(filepath) if h['status'] == 'overdue']
        if habits:
            for h in habits:
                print(format_habit(h))
        else:
            print(json.dumps({'status': 'ok', 'message': 'No overdue habits'}))
        return

    if cmd == '--due-today':
        habits = [h for h in list_habits(filepath) if h['status'] == 'due-today']
        if habits:
            for h in habits:
                print(format_habit(h))
        else:
            print(json.dumps({'status': 'ok', 'message': 'No habits due today'}))
        return

    if cmd == '--streak':
        query = ' '.join(non_flag_args)
        if not query:
            print(json.dumps({'error': '--streak requires a title query'}))
            sys.exit(1)
        habits = list_habits(filepath)
        habit = find_habit(habits, query)
        if not habit:
            print(json.dumps({'error': f'Habit matching "{query}" not found'}))
            sys.exit(1)
        print(json.dumps({
            'title': habit['title'],
            'streak': habit['streak'],
            'logbook_count': len(habit['logbook']),
            'status': habit['status'],
        }, indent=2))
        return

    if cmd == '--toggle':
        query = ' '.join(non_flag_args)
        if not query:
            print(json.dumps({'error': '--toggle requires a title query'}))
            sys.exit(1)
        result = toggle_habit(filepath, query)
        print(json.dumps(result, indent=2))
        if 'error' in result:
            sys.exit(1)
        return

    if cmd == '--add':
        json_str = ' '.join(non_flag_args)
        try:
            params = json.loads(json_str)
        except json.JSONDecodeError:
            print(json.dumps({'error': '--add requires valid JSON'}))
            sys.exit(1)
        result = add_habit(filepath, params)
        print(json.dumps(result, indent=2))
        if 'error' in result:
            sys.exit(1)
        return

    if cmd == '--reschedule':
        if len(non_flag_args) < 2:
            print(json.dumps({
                'error': '--reschedule requires a title and date. '
                         'Usage: --reschedule "Title" YYYY-MM-DD [repeater]'
            }))
            sys.exit(1)
        query = non_flag_args[0]
        new_date = non_flag_args[1]
        new_repeater = non_flag_args[2] if len(non_flag_args) >= 3 else None
        result = reschedule_habit(filepath, query, new_date, new_repeater)
        print(json.dumps(result, indent=2))
        if 'error' in result:
            sys.exit(1)
        return

    print(json.dumps({'error': f'Unknown command: {cmd}'}))
    sys.exit(1)


if __name__ == '__main__':
    main()
