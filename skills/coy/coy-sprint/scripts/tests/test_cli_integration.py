#!/usr/bin/env python3
"""
test_cli_integration.py — End-to-end integration tests for org_query.py.

These tests run every CLI command against real fixture files and check:
- Exit codes are non-zero (0 for success, 1 for error)
- Output is valid JSON
- Key structural properties exist in the output
- Error cases produce appropriate error messages

This is the "safety net" — run before any deployment that changes org_query.py.
"""

import json
import os
import subprocess
import sys
import unittest

# Use canonical script — NO wrapper/symlink in skill dir (removed May 2026)
CANONICAL = os.path.expanduser("~/.hermes/scripts/org_query.py")
ORG_QUERY_PATH = os.environ.get("ORG_QUERY_PATH") or CANONICAL
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_TASKS = os.path.join(FIXTURES_DIR, "sample_tasks.org")
EDGE_CASES = os.path.join(FIXTURES_DIR, "edge_cases.org")


def run_script(filepath: str, *args) -> subprocess.CompletedProcess:
    cmd = [sys.executable, ORG_QUERY_PATH, filepath] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def assert_valid_json(test_case, result):
    """Assert that result is valid JSON and return parsed dict/list."""
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        test_case.fail(
            f"Invalid JSON output for {result.args}\n"
            f"stderr: {result.stderr[:200]}\n"
            f"stdout: {result.stdout[:200]}\n"
            f"JSON error: {e}"
        )


class TestAllCommands(unittest.TestCase):
    """Run every CLI command and check basic validity."""

    def __run_and_check(self, filepath: str, *args):
        """Run a command and expect success (exit code 0 + valid JSON)."""
        result = run_script(filepath, *args)
        msg = f"Non-zero exit for: {result.args}\nstderr: {result.stderr[:300]}"
        self.assertEqual(result.returncode, 0, msg=msg)
        return assert_valid_json(self, result)

    def test_default_parse(self):
        """Default invocation (no command) should return parsed headings."""
        data = self.__run_and_check(SAMPLE_TASKS)
        self.assertIn("headings", data)
        self.assertIsInstance(data["headings"], list)
        self.assertGreater(len(data["headings"]), 0)

    def test_summary(self):
        """--summary should return dashboard with sprint metrics."""
        data = self.__run_and_check(SAMPLE_TASKS, "--summary", "4")
        self.assertIn("sprint", data)
        self.assertIn("active_tasks", data)
        self.assertIn("sprint_items", data)
        self.assertIn("capacity", data)

    def test_summary_no_arg(self):
        """--summary without sprint number should default to 4."""
        data = self.__run_and_check(SAMPLE_TASKS, "--summary")
        self.assertIn("sprint", data)

    def test_find_active(self):
        """--find-active should return list of active tasks."""
        data = self.__run_and_check(SAMPLE_TASKS, "--find-active")
        self.assertIsInstance(data, list)

    def test_find_epic(self):
        """--find-epic should return EPIC subtree."""
        data = self.__run_and_check(SAMPLE_TASKS, "--find-epic", "Personal AI")
        self.assertEqual(data.get("keyword"), "EPIC")
        self.assertIn("children", data)
        self.assertIn("properties", data)

    def test_find_epic_error(self):
        """--find-epic with non-existent name should return error JSON."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "NONEXISTENT")
        data = assert_valid_json(self, result)
        self.assertIn("error", data)

    def test_sprint_4(self):
        """--sprint 4 should return sprint 4 items."""
        data = self.__run_and_check(SAMPLE_TASKS, "--sprint", "4")
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_sprint_backlog(self):
        """--sprint backlog should return backlog items (string arg)."""
        data = self.__run_and_check(SAMPLE_TASKS, "--sprint", "backlog")
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_insert_point(self):
        """--insert-point should return insertion location."""
        data = self.__run_and_check(SAMPLE_TASKS, "--insert-point", "Personal AI v1")
        self.assertIn("insert_after_line", data)
        self.assertIn("level", data)
        self.assertIn("epic", data)

    def test_insert_point_empty_epic(self):
        """--insert-point on EPIC without children should work."""
        data = self.__run_and_check(SAMPLE_TASKS, "--insert-point", "Future Ideas")
        self.assertIn("insert_after_line", data)
        self.assertIsNone(data.get("last_child"))

    def test_children_of(self):
        """--children-of should return direct children."""
        data = self.__run_and_check(SAMPLE_TASKS, "--children-of", "Personal AI v1")
        self.assertIsInstance(data, list)

    def test_children_of_missing(self):
        """--children-of for missing heading should return empty list."""
        data = self.__run_and_check(SAMPLE_TASKS, "--children-of", "DoesNotExist")
        self.assertEqual(data, [])

    def test_heading(self):
        """--heading should find by pattern with correct keyword."""
        data = self.__run_and_check(SAMPLE_TASKS, "--heading", "Build ingestion")
        self.assertIn("title", data)
        self.assertEqual(data.get("keyword"), "STORY-STARTED")

    def test_heading_not_found(self):
        """--heading with non-matching pattern should return error JSON."""
        result = run_script(SAMPLE_TASKS, "--heading", "ZzZzZzZ")
        data = assert_valid_json(self, result)
        self.assertIn("error", data)

    def test_stats(self):
        """--stats should return heading statistics."""
        data = self.__run_and_check(SAMPLE_TASKS, "--stats")
        self.assertIn("total_headings", data)
        self.assertIn("epic_count", data)
        self.assertIn("keyword_breakdown", data)

    def test_validate(self):
        """--validate should return validation results."""
        data = self.__run_and_check(SAMPLE_TASKS, "--validate")
        self.assertIn("issues", data)
        self.assertIn("warnings", data)

    def test_validate_detects_wip_on_edge(self):
        """--validate on edge_cases.org should find WIP violations."""
        data = self.__run_and_check(EDGE_CASES, "--validate")
        self.assertGreaterEqual(len(data.get("issues", [])), 1)

    def test_epics(self):
        """--epics should return all EPICs."""
        data = self.__run_and_check(SAMPLE_TASKS, "--epics")
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 4)

    def test_unknown_command(self):
        """Unknown command should return error and exit code 1."""
        result = run_script(SAMPLE_TASKS, "--bogus")
        self.assertEqual(result.returncode, 1)
        data = assert_valid_json(self, result)
        self.assertIn("error", data)

    def test_no_args(self):
        """No args should return usage error."""
        result = subprocess.run([sys.executable, ORG_QUERY_PATH], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
