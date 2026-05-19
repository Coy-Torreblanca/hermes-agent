#!/usr/bin/env python3
"""
test_habit_query.py — Test suite for habit_query.py.

Tests parsing, status detection, streak calculation, and CLI commands.
Pure unit tests — no file mutation (toggle/add are not tested here).

Usage:
  python3 scripts/tests/test_habit_query.py -v
"""

import json
import os
import subprocess
import sys
import unittest
import calendar
import atexit
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import patch

# Add parent dir to path so we can import the script modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# We import the module directly for unit testing the functions
import importlib.util
spec = importlib.util.spec_from_file_location(
    "habit_query",
    os.path.expanduser("~/.hermes/scripts/habit_query.py")
)
hq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hq)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
STREAK_HABITS = os.path.join(FIXTURES_DIR, "streak_habits.org")

HABIT_SCRIPT = os.path.expanduser("~/.hermes/scripts/habit_query.py")


def _make_sample_fixture():
    """Generate sample_habits content with dates always 30+ days out."""
    today = date.today()
    # Saturday ~4 weeks from now
    days_to_sat = (5 - today.weekday()) % 7
    if days_to_sat == 0:
        days_to_sat = 7
    sat = today + timedelta(days=days_to_sat + 28)
    sat_str = sat.strftime('%Y-%m-%d')
    sat_dow = sat.strftime('%a')
    # Friday before that Saturday
    fri = sat - timedelta(days=1)
    fri_str = fri.strftime('%Y-%m-%d')
    fri_dow = fri.strftime('%a')
    # Rent: 2nd of month, 2 months ahead
    rm = today.month + 2
    ry = today.year
    if rm > 12:
        rm -= 12
        ry += 1
    rd = min(2, calendar.monthrange(ry, rm)[1])
    rent_str = f"{ry:04d}-{rm:02d}-{rd:02d}"
    rent_dt = datetime.strptime(rent_str, '%Y-%m-%d').date()
    rent_dow = rent_dt.strftime('%a')
    # Investment: 1st of same month
    inv_str = f"{ry:04d}-{rm:02d}-01"
    inv_dt = datetime.strptime(inv_str, '%Y-%m-%d').date()
    inv_dow = inv_dt.strftime('%a')

    content = (
        '* TODO 📖 Study Anglican liturgy before Sundays\n'
        f'  SCHEDULED: <{sat_str} {sat_dow} +1w>\n'
        '  :PROPERTIES:\n'
        '  :STYLE:    habit\n'
        '  :END:\n'
        '\n'
        '  Look up lectionary cycle. Read passages before Sunday service (9:15 AM\n'
        '  Christ the King) to make it more impactful. Saturday prep for Sunday liturgy.\n'
        '\n'
        '* TODO 🙏 Prepare for Bible study — read chapters + Bible Project videos\n'
        f'  SCHEDULED: <{fri_str} {fri_dow} +1w>\n'
        '  :PROPERTIES:\n'
        '  :STYLE:    habit\n'
        '  :END:\n'
        '\n'
        '  Read assigned chapters and watch Bible Project videos before each study\n'
        '  session.\n'
        '\n'
        '* TODO 💸 Pay rent — due 1st, reminder 2nd at 4 PM\n'
        f'  SCHEDULED: <{rent_str} {rent_dow} +1m>\n'
        '  :PROPERTIES:\n'
        '  :STYLE:    habit\n'
        '  :ID:       E463F6634B924F9EB9A95DA5749B767A\n'
        '  :END:\n'
        '\n'
        '  Rent is due on the 1st of each month.\n'
        '\n'
        '* STORY Execute Monthly Investment Strategy\n'
        f'  SCHEDULED: <{inv_str} {inv_dow} +1m>\n'
        '  :PROPERTIES:\n'
        '  :STYLE: habit\n'
        '  :LAST_REPEAT: [2026-04-18 Sat 04:45]\n'
        '  :END:\n'
        '\n'
        '  - State "DONE"       from "TODO"       [2026-04-18 Sat 04:45]\n'
        '  Deploy $4,166 from savings into the market via dollar-cost averaging.\n'
        '\n'
        '  ** Allocation Checklist:\n'
        '  - [ ] Transfer $4,166 from Savings to Brokerage\n'
        '  - [ ] Buy ~$1,388 of VGLT (33%)\n'
        '  - [ ] Buy ~$1,388 of VTEB (33%)\n'
        '  - [ ] Buy ~$1,388 of DIA (33%)\n'
    )

    fd, path = tempfile.mkstemp(suffix='.org', prefix='test_sample_habits_')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    atexit.register(lambda p=path: os.unlink(p) if os.path.exists(p) else None)

    return path, {
        'anglican': sat_str,
        'bible_study': fri_str,
        'rent': rent_str,
    }


SAMPLE_HABITS, SAMPLE_FIXTURE_DATES = _make_sample_fixture()


def run_script(filepath: str, *args) -> subprocess.CompletedProcess:
    cmd = [sys.executable, HABIT_SCRIPT, filepath] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


class TestParsing(unittest.TestCase):
    """Core parsing: heading, SCHEDULED, properties, body."""

    def test_parses_all_habits(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertEqual(len(habits), 4)

    def test_parses_heading_keyword(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        todo_habits = [h for h in habits if h['keyword'] == 'TODO']
        story_habits = [h for h in habits if h['keyword'] == 'STORY']
        self.assertEqual(len(todo_habits), 3)
        self.assertEqual(len(story_habits), 1)

    def test_parses_title(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertIn('Study Anglican liturgy', habits[0]['title'])
        self.assertIn('Prepare for Bible study', habits[1]['title'])

    def test_parses_scheduled(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertEqual(habits[0]['scheduled'], SAMPLE_FIXTURE_DATES['anglican'])
        self.assertEqual(habits[1]['scheduled'], SAMPLE_FIXTURE_DATES['bible_study'])
        self.assertEqual(habits[2]['scheduled'], SAMPLE_FIXTURE_DATES['rent'])

    def test_parses_repeater(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertEqual(habits[0]['repeater'], 'weekly')
        self.assertEqual(habits[1]['repeater'], 'weekly')
        self.assertEqual(habits[2]['repeater'], 'monthly')

    def test_parses_style(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        for h in habits:
            self.assertEqual(h['style'], 'habit')

    def test_parses_id(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        # Only rent habit has ID
        self.assertIsNone(habits[0]['id'])
        self.assertEqual(habits[2]['id'], 'E463F6634B924F9EB9A95DA5749B767A')

    def test_parses_last_repeat(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        # Only investment strategy has LAST_REPEAT
        self.assertIsNotNone(habits[3]['last_repeat'])
        self.assertIsNone(habits[0]['last_repeat'])

    def test_parses_body(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertIn('Look up lectionary cycle', habits[0]['body'])
        self.assertIn('Deploy $4,166', habits[3]['body'])

    def test_parses_logbook(self):
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        # Only investment strategy has a logbook entry
        self.assertEqual(len(habits[0]['logbook']), 0)
        self.assertEqual(len(habits[3]['logbook']), 1)

    def test_body_excludes_scheduled(self):
        """SCHEDULED line should NOT appear in body."""
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertNotIn('SCHEDULED:', habits[0]['body'])

    def test_body_excludes_properties(self):
        """PROPERTIES and :END: should NOT appear in body."""
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertNotIn(':PROPERTIES:', habits[0]['body'])
        self.assertNotIn(':END:', habits[0]['body'])

    def test_body_excludes_logbook(self):
        """State DONE entries should NOT appear in body."""
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertNotIn('State "DONE"', habits[3]['body'])

    def test_parses_emoji_title(self):
        """Emoji in title should be preserved."""
        with open(SAMPLE_HABITS) as f:
            habits = hq.parse_habits(f.read())
        self.assertIn('📖', habits[0]['title'])
        self.assertIn('🙏', habits[1]['title'])
        self.assertIn('💸', habits[2]['title'])


class TestStreakCalculation(unittest.TestCase):
    """Streak counting from LOGBOOK timestamps."""

    def setUp(self):
        with open(STREAK_HABITS) as f:
            self.habits = hq.parse_habits(f.read())

    def test_bible_study_streak_4_days(self):
        """Bible study: May 12-15 = 4 consecutive days, gap at May 10-11."""
        habit = next(h for h in self.habits if 'Bible study' in h['title'])
        streak = hq.compute_streak(habit['logbook'])
        # Latest entries: 15, 14, 13, 12 = 4 consecutive, then 10 (gap)
        self.assertEqual(streak, 4)

    def test_rent_streak_1_monthly(self):
        """Rent: monthly entries are not consecutive days, so streak = 1."""
        habit = next(h for h in self.habits if 'rent' in h['title'].lower())
        streak = hq.compute_streak(habit['logbook'])
        # Each entry is a month apart — only first counts
        self.assertEqual(streak, 1)

    def test_daily_exercise_streak_8_days(self):
        """Daily exercise: May 8-15 = 8 consecutive days."""
        habit = next(h for h in self.habits if 'exercise' in h['title'])
        streak = hq.compute_streak(habit['logbook'])
        self.assertEqual(streak, 8)

    def test_empty_logbook_streak_0(self):
        """No logbook entries = streak 0."""
        streak = hq.compute_streak([])
        self.assertEqual(streak, 0)

    def test_single_entry_streak_1(self):
        """Single logbook entry = streak 1."""
        streak = hq.compute_streak(['2026-05-15 Fri 08:00'])
        self.assertEqual(streak, 1)


class TestStatusDetection(unittest.TestCase):
    """Habit status: overdue, due-today, done-today, upcoming."""

    def setUp(self):
        with open(STREAK_HABITS) as f:
            self.habits = hq.parse_habits(f.read())

    def test_bible_study_done_today(self):
        """Bible study DONE 2026-05-15 — done-today."""
        habit = next(h for h in self.habits if 'Bible study' in h['title'])
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'done-today')

    def test_rent_upcoming_jun2(self):
        """Rent SCHEDULED June 2 — upcoming on May 15."""
        habit = next(h for h in self.habits if 'rent' in h['title'].lower())
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'upcoming')

    def test_exercise_done_today(self):
        """Exercise DONE May 15 — done-today."""
        habit = next(h for h in self.habits if 'exercise' in h['title'])
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'done-today')

    def test_exercise_was_overdue_day_before(self):
        """Exercise on May 14 without logging — would be overdue."""
        habit = next(h for h in self.habits if 'exercise' in h['title'])
        status = hq.habit_status(habit, date(2026, 5, 14))
        # The SCHEDULED is May 15, so on May 14 it's upcoming
        self.assertEqual(status, 'done-today')

    def test_overdue_detection(self):
        """A habit SCHEDULED before today with no DONE today is overdue."""
        # Create a minimal habit that's overdue
        habit = {
            'scheduled': '2026-05-10',
            'logbook': ['2026-05-09 Thu 08:00'],
        }
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'overdue')

    def test_due_today_no_done(self):
        """SCHEDULED today but not yet DONE = due-today."""
        # Modify Bible study to NOT have today's DONE
        habit = {
            'scheduled': '2026-05-15',
            'logbook': ['2026-05-14 Thu 08:00'],  # Yesterday only
        }
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'due-today')

    def test_no_schedule(self):
        """No SCHEDULED date = no-schedule status."""
        habit = {'scheduled': None, 'logbook': []}
        status = hq.habit_status(habit, date(2026, 5, 15))
        self.assertEqual(status, 'no-schedule')


class TestFindHabit(unittest.TestCase):
    """Partial title matching."""

    def setUp(self):
        with open(SAMPLE_HABITS) as f:
            self.habits = hq.parse_habits(f.read())

    def test_find_by_partial(self):
        habit = hq.find_habit(self.habits, 'Anglican')
        self.assertIsNotNone(habit)
        self.assertIn('Anglican liturgy', habit['title'])

    def test_find_by_emoji(self):
        habit = hq.find_habit(self.habits, 'rent')
        self.assertIsNotNone(habit)
        self.assertIn('rent', habit['title'].lower())

    def test_find_not_found(self):
        habit = hq.find_habit(self.habits, 'nonexistent')
        self.assertIsNone(habit)

    def test_find_case_insensitive(self):
        habit = hq.find_habit(self.habits, 'anglican')
        self.assertIsNotNone(habit)


class TestCLIIntegration(unittest.TestCase):
    """End-to-end CLI tests using subprocess."""

    def test_list_returns_json(self):
        result = run_script(SAMPLE_HABITS, '--list')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn('habits', data)
        self.assertEqual(len(data['habits']), 4)

    def test_list_contains_titles(self):
        result = run_script(SAMPLE_HABITS, '--list')
        data = json.loads(result.stdout)
        titles = [h['title'] for h in data['habits']]
        self.assertIn('Study Anglican liturgy before Sundays', titles[0])

    def test_list_includes_status(self):
        result = run_script(SAMPLE_HABITS, '--list')
        data = json.loads(result.stdout)
        for h in data['habits']:
            self.assertIn('status', h)

    def test_list_includes_streak(self):
        result = run_script(SAMPLE_HABITS, '--list')
        data = json.loads(result.stdout)
        for h in data['habits']:
            self.assertIn('streak', h)

    def test_streak_command(self):
        result = run_script(STREAK_HABITS, '--streak', 'Bible study')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data['streak'], 4)

    def test_streak_not_found(self):
        result = run_script(SAMPLE_HABITS, '--streak', 'nonexistent')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)

    def test_overdue_empty(self):
        """No overdue habits in sample file."""
        result = run_script(SAMPLE_HABITS, '--overdue')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data['status'], 'ok')

    def test_unknown_command(self):
        result = run_script(SAMPLE_HABITS, '--bogus')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)

    def test_help_output(self):
        result = run_script(SAMPLE_HABITS, '--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('habit_query.py', result.stdout)
        self.assertIn('--list', result.stdout)
        self.assertIn('--reschedule', result.stdout)


class TestReschedule(unittest.TestCase):
    """Reschedule a habit: change SCHEDULED date via --reschedule."""

    TEMP_FILE = '/tmp/test_reschedule_habits.org'

    def setUp(self):
        import shutil
        shutil.copy(SAMPLE_HABITS, self.TEMP_FILE)

    def tearDown(self):
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)

    def _read_scheduled(self, title_substr: str) -> str:
        """Helper: read the SCHEDULED line for a habit by title substring."""
        with open(self.TEMP_FILE) as f:
            text = f.read()
        return self._find_scheduled(text, title_substr)

    def _find_scheduled(self, text: str, title_substr: str) -> str:
        """Find SCHEDULED line under a habit heading matching title_substr."""
        lines = text.split('\n')
        in_habit = False
        for line in lines:
            m = hq.HEADING_RE.match(line)
            if m and title_substr.lower() in m.group(3).lower():
                in_habit = True
                continue
            if in_habit:
                sched_m = hq.SCHEDULED_RE.match(line)
                if sched_m:
                    return sched_m.group(0).strip()
                if hq.HEADING_RE.match(line):
                    break
        return ''

    def test_cli_reschedule_date_only(self):
        """CLI: --reschedule changes the SCHEDULED date."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Anglican', '2026-06-07')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data['rescheduled'])
        self.assertEqual(data['old_scheduled'], SAMPLE_FIXTURE_DATES['anglican'])
        self.assertEqual(data['new_scheduled'], '2026-06-07')
        # Verify file content
        sched = self._read_scheduled('Anglican')
        self.assertIn('2026-06-07', sched)

    def test_cli_reschedule_with_repeater(self):
        """CLI: --reschedule changes date AND repeater."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Bible study',
                             '2026-05-23', '++2w/21d')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data['rescheduled'])
        self.assertEqual(data['new_scheduled'], '2026-05-23')
        self.assertEqual(data['repeater'], 'biweekly')
        # Verify file content has new repeater
        sched = self._read_scheduled('Bible study')
        self.assertIn('++2w/21d', sched)

    def test_cli_reschedule_preserves_repeater(self):
        """Default: existing repeater is preserved when no new one given."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Pay rent', '2026-07-02')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data['rescheduled'])
        # Original repeater was '+1m' → 'monthly'
        self.assertEqual(data['repeater'], 'monthly')
        sched = self._read_scheduled('Pay rent')
        self.assertIn('+1m', sched)

    def test_cli_reschedule_not_found(self):
        """--reschedule with non-matching title returns error."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'nonexistent', '2026-07-02')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)

    def test_cli_reschedule_bad_date(self):
        """--reschedule with invalid date returns error."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Anglican', 'not-a-date')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)

    def test_cli_reschedule_missing_args(self):
        """--reschedule without enough args returns error."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Anglican')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)

    def test_reschedule_last_repeat_preserved(self):
        """Rescheduling should not touch :LAST_REPEAT: or other properties."""
        result = run_script(self.TEMP_FILE, '--reschedule', 'Investment', '2026-07-01')
        self.assertEqual(result.returncode, 0)
        # The investment strategy habit has LAST_REPEAT — verify it's still there
        with open(self.TEMP_FILE) as f:
            text = f.read()
        # LAST_REPEAT should survive
        self.assertIn('LAST_REPEAT', text)
        # LOGBOOK entries should survive
        self.assertIn('State "DONE"', text)
        # Body content should survive
        self.assertIn('Deploy $4,166', text)


class TestUtility(unittest.TestCase):
    """Utility functions."""

    def test_parse_date_valid(self):
        d = hq.parse_date('2026-05-15')
        self.assertEqual(d, date(2026, 5, 15))

    def test_parse_date_invalid(self):
        d = hq.parse_date('not-a-date')
        self.assertIsNone(d)

    def test_parse_date_none(self):
        d = hq.parse_date(None)
        self.assertIsNone(d)

    def test_parse_logbook_timestamp(self):
        d = hq.parse_logbook_timestamp('2026-05-15 Fri 08:00')
        self.assertEqual(d, date(2026, 5, 15))

    def test_parse_logbook_timestamp_no_match(self):
        d = hq.parse_logbook_timestamp('')
        self.assertIsNone(d)

    def test_repeater_patterns(self):
        """All known repeater patterns should be recognized."""
        patterns = ['+1d', '.+1d/2d', '+1w', '+2w', '++2w/21d', '+1m']
        for p in patterns:
            self.assertIn(p, hq.REPEATER_PATTERNS, f"Missing pattern: {p}")


class TestToggle(unittest.TestCase):
    """Toggle habit: state line indent, SCHEDULED advancement."""

    TEMP_FILE = '/tmp/test_toggle_habits.org'

    WEEKDAY_HABIT = '* TODO Daily Org Triage\n' \
                    '   SCHEDULED: <2026-05-18 Mon .+1d/2d>\n' \
                    '   :PROPERTIES:\n' \
                    '   :STYLE:    habit\n' \
                    '   :ID:       habit-org-triage\n' \
                    '   :END:\n' \
                    '   - State "DONE"       from "TODO"       [2026-05-16 Sat 06:52]\n' \
                    '\n'

    DAILY_HABIT = '* TODO Daily exercise\n' \
                  '   SCHEDULED: <2026-05-18 Mon +1d>\n' \
                  '   :PROPERTIES:\n' \
                  '   :STYLE:    habit\n' \
                  '   :END:\n' \
                  '   - State "DONE"       from "TODO"       [2026-05-17 Sun 07:00]\n' \
                  '\n'

    WEEKLY_HABIT = '* TODO 📖 Study Anglican liturgy\n' \
                   '   SCHEDULED: <2026-05-23 Sat +1w>\n' \
                   '   :PROPERTIES:\n' \
                   '   :STYLE:    habit\n' \
                   '   :END:\n' \
                   '\n' \
                   '  Body content here.\n' \
                   '\n'

    MONTHLY_HABIT = '* TODO 💸 Pay rent\n' \
                    '   SCHEDULED: <2026-06-02 Tue +1m>\n' \
                    '   :PROPERTIES:\n' \
                    '   :STYLE:    habit\n' \
                    '   :ID:       E463F6634B924F9EB9A95DA5749B767A\n' \
                    '   :END:\n' \
                    '\n' \
                    '  Rent is due on the 1st.\n' \
                    '\n'

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)

    def _write_fixture(self, content: str):
        """Write test fixture to temp file."""
        with open(self.TEMP_FILE, 'w') as f:
            f.write(content)

    def _read_state_lines(self) -> list[str]:
        """Read all State DONE lines from the temp file."""
        with open(self.TEMP_FILE) as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines if 'State "DONE"' in l]

    def _read_scheduled(self) -> str:
        """Read the SCHEDULED line from the temp file."""
        with open(self.TEMP_FILE) as f:
            lines = f.readlines()
        for line in lines:
            m = hq.SCHEDULED_RE.match(line)
            if m:
                return m.group(0).strip()
        return ''

    @patch.object(hq, 'date')
    def test_state_line_uses_3space_indent(self, mock_date):
        """State line after toggle should use 3-space indent."""
        mock_date.today.return_value = date(2026, 5, 18)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKDAY_HABIT)
        result = hq.toggle_habit(self.TEMP_FILE, 'Daily Org Triage')
        self.assertNotIn('error', result)
        state_lines = self._read_state_lines()
        for line in state_lines:
            # Every state line should start with 3 spaces
            if '2026-05-18' in line:
                self.assertTrue(line.startswith('   - State'),
                                f'State line indent wrong: {repr(line[:20])}')

    @patch.object(hq, 'date')
    def test_weekday_repeater_advances_to_next_weekday(self, mock_date):
        """.+1d/2d on Monday advances to Tuesday (skips weekend properly)."""
        mock_date.today.return_value = date(2026, 5, 18)  # Monday
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKDAY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Daily Org Triage')
        sched = self._read_scheduled()
        self.assertIn('2026-05-19', sched)  # Tuesday
        self.assertIn('Tue', sched)
        self.assertIn('.+1d/2d', sched)

    @patch.object(hq, 'date')
    def test_weekday_skips_weekends(self, mock_date):
        """Friday toggle advances to Monday (skips Sat/Sun)."""
        mock_date.today.return_value = date(2026, 5, 22)  # Friday
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        friday_habit = '* TODO Weekday Task\n' \
                       '   SCHEDULED: <2026-05-22 Fri .+1d/2d>\n' \
                       '   :PROPERTIES:\n' \
                       '   :STYLE:    habit\n' \
                       '   :END:\n' \
                       '\n'
        self._write_fixture(friday_habit)
        hq.toggle_habit(self.TEMP_FILE, 'Weekday Task')
        sched = self._read_scheduled()
        # Friday toggle → Saturday→Sunday skip → Monday
        self.assertIn('2026-05-25', sched)  # Monday
        self.assertIn('Mon', sched)

    @patch.object(hq, 'date')
    def test_daily_repeater_advances_one_day(self, mock_date):
        """+1d advances by exactly 1 day."""
        mock_date.today.return_value = date(2026, 5, 18)  # Monday
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.DAILY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Daily exercise')
        sched = self._read_scheduled()
        self.assertIn('2026-05-19', sched)
        self.assertIn('+1d', sched)

    @patch.object(hq, 'date')
    def test_weekly_repeater_advances_seven_days(self, mock_date):
        """+1w advances by exactly 7 days."""
        mock_date.today.return_value = date(2026, 5, 18)  # Monday
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKLY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Study Anglican liturgy')
        sched = self._read_scheduled()
        self.assertIn('2026-05-25', sched)
        self.assertIn('+1w', sched)

    @patch.object(hq, 'date', wraps=date)
    def test_monthly_repeater_advances_one_month(self, mock_date):
        """+1m advances to next month from today."""
        mock_date.today.return_value = date(2026, 5, 18)  # Monday
        self._write_fixture(self.MONTHLY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Pay rent')
        sched = self._read_scheduled()
        # May 18 + 1 month → June 18 (keeps today's day, not original SCHEDULED day)
        self.assertIn('2026-06-18', sched)
        self.assertIn('+1m', sched)

    @patch.object(hq, 'date')
    def test_body_preserved_after_toggle(self, mock_date):
        """Body text should survive toggle."""
        mock_date.today.return_value = date(2026, 5, 18)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKLY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Study Anglican liturgy')
        with open(self.TEMP_FILE) as f:
            text = f.read()
        self.assertIn('Body content here', text)

    @patch.object(hq, 'date')
    def test_properties_preserved_after_toggle(self, mock_date):
        """Properties drawer should survive toggle."""
        mock_date.today.return_value = date(2026, 5, 18)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.MONTHLY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Pay rent')
        with open(self.TEMP_FILE) as f:
            text = f.read()
        self.assertIn(':PROPERTIES:', text)
        self.assertIn('E463F6634B924F9EB9A95DA5749B767A', text)
        self.assertIn(':STYLE:    habit', text)

    @patch.object(hq, 'date')
    def test_existing_state_entries_preserved(self, mock_date):
        """Old logbook entries should survive toggle."""
        mock_date.today.return_value = date(2026, 5, 18)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKDAY_HABIT)
        hq.toggle_habit(self.TEMP_FILE, 'Daily Org Triage')
        with open(self.TEMP_FILE) as f:
            text = f.read()
        self.assertIn('[2026-05-16 Sat 06:52]', text)

    @patch.object(hq, 'date')
    def test_cli_toggle_returns_success(self, mock_date):
        """CLI --toggle returns toggled=True."""
        mock_date.today.return_value = date(2026, 5, 18)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        self._write_fixture(self.WEEKDAY_HABIT)
        result = run_script(self.TEMP_FILE, '--toggle', 'Daily Org Triage')
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertTrue(data['toggled'])
        self.assertEqual(data['title'], 'Daily Org Triage')
    def test_toggle_not_found(self):
        """--toggle with non-matching title returns error."""
        self._write_fixture(self.WEEKDAY_HABIT)
        result = run_script(self.TEMP_FILE, '--toggle', 'nonexistent')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
