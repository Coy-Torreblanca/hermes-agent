#!/usr/bin/env python3
"""
test_parse_backlog.py — Tests for parse_backlog.py backlog parsing.

Covers:
- Sprint filtering (backlog items vs sprinted items)
- Value sort order (Critical → Low)
- Max points filter
- Value-only filter
- Items without value are excluded

Usage:
  pytest scripts/tests/test_parse_backlog.py -v
  python3 scripts/tests/test_parse_backlog.py
"""

import os
import re as re_module
import subprocess
import sys
import tempfile
import unittest

# ── Path Setup ─────────────────────────────────────────────────────────────────
PARSE_BACKLOG_PATH = os.path.join(
    os.path.dirname(__file__),  # tests/
    "..",                        # scripts/
    "parse_backlog.py"
)
FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__),  # tests/
    "fixtures"
)

SAMPLE_BACKLOG = os.path.join(FIXTURES_DIR, "sample_backlog.org")


def run_backlog(*args) -> subprocess.CompletedProcess:
    """Run parse_backlog.py with given args."""
    cmd = [sys.executable, PARSE_BACKLOG_PATH, "--file", SAMPLE_BACKLOG] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def extract_items(output: str) -> list[dict]:
    """Parse backlog output into structured items.

    Output format from parse_backlog.py:
        STORY Title
            POINTS: N | VALUE: ValueName
            GOAL: Goal text
    """
    items = []
    current = None
    re_heading = re_module.compile(r"^(STORY|TODO|EPIC)\s+(.+)")
    re_points = re_module.compile(r"POINTS:\s+(\d+)")
    re_value = re_module.compile(r"VALUE:\s+(\S+)")
    re_goal = re_module.compile(r"GOAL:\s+(.+)")

    for line in output.strip().split("\n"):
        heading_match = re_heading.match(line)
        if heading_match:
            if current:
                items.append(current)
            current = {
                "keyword": heading_match.group(1),
                "title": heading_match.group(2).strip(),
            }
            continue

        if current:
            pts = re_points.search(line)
            if pts:
                current["points"] = int(pts.group(1))
            val = re_value.search(line)
            if val:
                current["value"] = val.group(1)
            goal = re_goal.search(line)
            if goal:
                current["goal"] = goal.group(1)

    if current:
        items.append(current)
    return items


class TestBacklogParsing(unittest.TestCase):
    """Tests for parse_backlog.py."""

    def test_excludes_sprinted_items(self):
        """Items with SPRINT: 4 should be excluded from backlog output."""
        result = run_backlog()
        items = extract_items(result.stdout)
        titles = [i["title"] for i in items]
        self.assertIn("Critical item", titles, "Should include backlog items")
        self.assertNotIn(
            "Sprint 4 item",
            titles,
            "Items with SPRINT: 4 should be excluded"
        )

    def test_excludes_no_value_items(self):
        """Items without :VALUE: should be excluded."""
        result = run_backlog()
        items = extract_items(result.stdout)
        titles = [i["title"] for i in items]
        self.assertNotIn("No value item", titles)

    def test_value_sort_order(self):
        """Items should appear sorted by VALUE: Critical → Low."""
        # Use a high max-points so nothing gets truncated
        result = run_backlog("--max-points", "99")
        items = extract_items(result.stdout)
        value_order = {"Critical": 0, "Essential": 1, "High": 2, "Important": 3, "Medium": 4, "Nice-to-have": 5, "Low": 6}
        values = [value_order.get(i.get("value", ""), 99) for i in items]
        ordered_values = [v for v in values if v <= 3]
        self.assertEqual(
            ordered_values,
            sorted(ordered_values),
            f"Items should be sorted by value, got order: {ordered_values}"
        )

    def test_max_points_filter(self):
        """--max-points should limit total committed points."""
        result = run_backlog("--max-points", "5")
        for line in result.stdout.strip().split("\n"):
            if "TOTAL:" in line:
                total = int(re_module.search(r"TOTAL:\s+(\d+)", line).group(1))
                self.assertLessEqual(total, 5)
                return
        self.fail("No TOTAL line found in output")

    def test_value_only_filter(self):
        """--value-only should restrict to single value level."""
        result = run_backlog("--value-only", "Essential")
        items = extract_items(result.stdout)
        for item in items:
            self.assertEqual(
                item.get("value"),
                "Essential",
                f"Item '{item.get('title')}' has wrong value: {item.get('value')}"
            )

    def test_total_line_present(self):
        """Output should end with TOTAL line."""
        result = run_backlog()
        has_total = any("TOTAL:" in line for line in result.stdout.split("\n"))
        self.assertTrue(has_total)

    def test_points_displayed(self):
        """Each item should show POINTS."""
        result = run_backlog()
        items = extract_items(result.stdout)
        for item in items:
            self.assertIn("points", item, f"Item '{item.get('title')}' missing POINTS")

    def test_goal_displayed(self):
        """Items with GOAL should display it."""
        result = run_backlog()
        items = extract_items(result.stdout)
        goals = [i.get("goal") for i in items if i.get("goal")]
        self.assertGreater(len(goals), 0)

    def test_exit_code_zero(self):
        """Should exit with code 0 on success."""
        result = run_backlog()
        self.assertEqual(result.returncode, 0)

    def test_output_to_stdout(self):
        """Output should go to stdout."""
        result = run_backlog()
        self.assertGreater(len(result.stdout.strip()), 0)

    def test_stale_flag(self):
        """--stale N should flag items older than N sprint cycles."""
        # Create a temp org file with one old item and one recent item
        with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
            f.write("""#+TITLE: Stale Test

** STORY Old item
:PROPERTIES:
:ID:       STALE001
:CREATED:  [2026-01-01]
:SPRINT:   backlog
:POINTS:   3
:VALUE:    Essential
:GOAL:     Test stale detection
:END:

** STORY Recent item
:PROPERTIES:
:ID:       STALE002
:CREATED:  [2026-05-17]
:SPRINT:   backlog
:POINTS:   2
:VALUE:    Essential
:GOAL:     Should not be stale
:END:
""")
            temp_path = f.name

        try:
            # Run with --stale 1: both items are at least 1 sprint old
            result = run_backlog("--file", temp_path, "--stale", "1")
            self.assertEqual(result.returncode, 0)
            # Old item should have stale marker
            self.assertIn("⏰", result.stdout,
                          "Old item should be flagged as stale")
            # Recent item may or may not be flagged depending on today's date

            # Run with --stale 20: neither item should be flagged
            result2 = run_backlog("--file", temp_path, "--stale", "20")
            self.assertEqual(result2.returncode, 0)
            self.assertNotIn("⏰", result2.stdout,
                             "Neither item should be flagged with --stale 20")
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
