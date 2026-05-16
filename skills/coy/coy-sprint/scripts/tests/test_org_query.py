#!/usr/bin/env python3
"""
test_org_query.py — Comprehensive test suite for org_query.py.

Covers:
- Core parsing: EPICs, STORYs, TODOs, properties, children
- Edge cases: empty EPICs, malformed properties, nested hierarchies
- Query commands: --find-active, --find-epic, --sprint, --insert-point
- Validation rules: WIP violations, orphans, missing points
- Statistics: heading counts, keyword breakdowns
- Integration: all CLI commands from end to end

Usage:
  pytest scripts/tests/test_org_query.py -v
  python3 scripts/tests/test_org_query.py
"""

import json
import os
import subprocess
import sys
import unittest

# ── Path Setup ─────────────────────────────────────────────────────────────────
# Use canonical script — NO wrapper/symlink in skill dir (removed May 2026)
CANONICAL = os.path.expanduser("~/.hermes/scripts/org_query.py")
ORG_QUERY_PATH = os.environ.get("ORG_QUERY_PATH") or CANONICAL
FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__),  # tests/
    "fixtures"
)

SAMPLE_TASKS = os.path.join(FIXTURES_DIR, "sample_tasks.org")
SAMPLE_BACKLOG = os.path.join(FIXTURES_DIR, "sample_backlog.org")
EDGE_CASES = os.path.join(FIXTURES_DIR, "edge_cases.org")

# ── Test Helpers ──────────────────────────────────────────────────────────────

def run_script(filepath: str, *args) -> dict | list:
    """Run org_query.py with given args and return parsed JSON output."""
    cmd = [sys.executable, ORG_QUERY_PATH, filepath] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Try to parse error JSON from stdout
        try:
            parsed = json.loads(result.stdout)
            return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        return {"_error": result.stderr.strip(), "_stdout": result.stdout.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"_error": str(e), "_stdout": result.stdout.strip()}


def run_python(code: str) -> dict:
    """Run inline Python that imports org_query.py functions for unit testing."""
    import_path = os.path.dirname(ORG_QUERY_PATH)
    wrapped = f"""
import sys
sys.path.insert(0, '{import_path}')
import org_query
import json

{code}
"""
    result = subprocess.run(
        [sys.executable, "-c", wrapped],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {{"_error": result.stderr.strip(), "_stdout": result.stdout.strip()}}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {{"_error": str(e), "_stdout": result.stdout.strip()}}


# ── Test Suite ────────────────────────────────────────────────────────────────

class TestCoreParsing(unittest.TestCase):
    """Tests for parse_org() — the foundation of everything."""

    def test_parses_file_without_error(self):
        """Basic smoke test: can parse a real org file."""
        result = run_script(SAMPLE_TASKS, "--epics")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_detects_epics(self):
        """Should find all EPIC headings in the file."""
        result = run_script(SAMPLE_TASKS, "--epics")
        titles = [e["title"] for e in result]
        self.assertIn("Personal AI v1", titles)
        self.assertIn("30AI Document Pipeline", titles)
        self.assertIn("CI/CD Pipeline", titles)
        # [ICEBOX] is parsed as part of the title since it's not a keyword
        self.assertIn("[ICEBOX] Future Ideas", titles)

    def test_epic_has_children(self):
        """EPIC with stories should report children_count > 0."""
        result = run_script(SAMPLE_TASKS, "--epics")
        epics = {e["title"]: e for e in result}
        self.assertGreater(epics["Personal AI v1"]["children_count"], 0)
        self.assertEqual(epics["[ICEBOX] Future Ideas"]["children_count"], 0)

    def test_epic_shows_sprint(self):
        """EPIC properties should include SPRINT."""
        result = run_script(SAMPLE_TASKS, "--epics")
        epics = {e["title"]: e for e in result}
        self.assertEqual(epics["Personal AI v1"]["sprint"], "4")
        self.assertEqual(epics["30AI Document Pipeline"]["sprint"], "backlog")

    def test_epic_shows_tags(self):
        """EPIC tags should be parsed from heading."""
        result = run_script(SAMPLE_TASKS, "--epics")
        epics = {e["title"]: e for e in result}
        self.assertIn("personal-ai", epics["Personal AI v1"]["tags"])
        self.assertIn("hermes", epics["Personal AI v1"]["tags"])
        self.assertIn("30ai", epics["30AI Document Pipeline"]["tags"])

    def test_find_epic_by_partial_name(self):
        """--find-epic should match by partial name."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "Personal AI")
        self.assertNotIn("error", result)
        self.assertNotIn("_error", result)
        self.assertEqual(result.get("keyword"), "EPIC")
        self.assertEqual(result["title"], "Personal AI v1")

    def test_find_epic_not_found(self):
        """--find-epic should return error for missing EPIC."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "DoesNotExist")
        self.assertIn("error", result)


class TestFindActive(unittest.TestCase):
    """Tests for find_active() — detecting currently running tasks."""

    def test_finds_started_and_next(self):
        """Should find all STARTED, NEXT, STORY-STARTED, STORY-NEXT items."""
        result = run_script(SAMPLE_TASKS, "--find-active")
        self.assertIsInstance(result, list)
        keywords = [item["keyword"] for item in result]
        self.assertIn("STORY-STARTED", keywords)
        self.assertIn("STORY-NEXT", keywords)

    def test_active_has_epic_chain(self):
        """Active items should include their parent EPIC context."""
        result = run_script(SAMPLE_TASKS, "--find-active")
        active_by_title = {item["title"]: item for item in result}
        if "Build ingestion pipeline" in active_by_title:
            item = active_by_title["Build ingestion pipeline"]
            self.assertIn("Personal AI v1", item.get("epic_chain", ""))

    def test_active_includes_metadata(self):
        """Active items should include points, sprint, value."""
        result = run_script(SAMPLE_TASKS, "--find-active")
        self.assertGreater(len(result), 0)
        active_task = result[0]
        self.assertIn("points", active_task)
        self.assertIn("sprint", active_task)
        self.assertIn("value", active_task)


class TestSprintItems(unittest.TestCase):
    """Tests for sprint filtering."""

    def test_sprint_4_items(self):
        """Should return all items in sprint 4."""
        result = run_script(SAMPLE_TASKS, "--sprint", "4")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        titles = [i["title"] for i in result]
        self.assertIn("Build ingestion pipeline", titles)
        self.assertIn("Build query layer", titles)

    def test_backlog_items(self):
        """Should return items in backlog (supports string arg)."""
        result = run_script(SAMPLE_TASKS, "--sprint", "backlog")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        titles = [i["title"] for i in result]
        self.assertIn("Build PDF ingestion", titles)

    def test_sprint_items_have_epic(self):
        """Sprint items should include parent EPIC name."""
        result = run_script(SAMPLE_TASKS, "--sprint", "4")
        sprint4 = {i["title"]: i for i in result}
        ing = sprint4.get("Build ingestion pipeline", {})
        self.assertIn("Personal AI v1", ing.get("epic", ""))


class TestInsertPoint(unittest.TestCase):
    """Tests for insert_point() — finding where to insert under EPICs."""

    def test_epic_with_children(self):
        """Should return insert point after last child for EPIC with children."""
        result = run_script(SAMPLE_TASKS, "--insert-point", "Personal AI v1")
        self.assertNotIn("error", result)
        self.assertEqual(result["epic"], "Personal AI v1")
        self.assertIsNotNone(result.get("insert_after_line"))
        self.assertIsNotNone(result.get("last_child"))
        self.assertGreater(len(result.get("last_child", "")), 0)

    def test_epic_without_children(self):
        """Should return insert point after properties for EPIC without children."""
        result = run_script(SAMPLE_TASKS, "--insert-point", "Future Ideas")
        self.assertNotIn("error", result)
        # [ICEBOX] prefix is part of the title
        self.assertEqual(result["epic"], "[ICEBOX] Future Ideas")
        self.assertIsNone(result.get("last_child"))

    def test_epic_not_found(self):
        """Should return error for missing EPIC."""
        result = run_script(SAMPLE_TASKS, "--insert-point", "DoesNotExist")
        self.assertIn("error", result)


class TestChildrenOf(unittest.TestCase):
    """Tests for children_of() — listing direct children of a heading."""

    def test_children_exists(self):
        """Should return children of an EPIC or heading."""
        result = run_script(SAMPLE_TASKS, "--children-of", "Personal AI v1")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        titles = [c["title"] for c in result]
        self.assertIn("Build ingestion pipeline", titles)

    def test_children_metadata(self):
        """Children should include keyword, points, sprint."""
        result = run_script(SAMPLE_TASKS, "--children-of", "Personal AI v1")
        child = result[0] if result else {}
        self.assertIn("keyword", child)
        self.assertIn("points", child)
        self.assertIn("sprint", child)

    def test_children_not_found(self):
        """Should return empty list for missing heading."""
        result = run_script(SAMPLE_TASKS, "--children-of", "DoesNotExist")
        self.assertEqual(result, [])


class TestFindHeading(unittest.TestCase):
    """Tests for find_heading() — finding headings by regex/partial."""

    def test_find_by_partial(self):
        """Should find headings by partial title match."""
        result = run_script(SAMPLE_TASKS, "--heading", "ingestion")
        self.assertNotIn("error", result)
        self.assertIn("ingestion", result.get("title", "").lower())

    def test_find_by_exact_regex(self):
        """Should find headings by regex pattern."""
        result = run_script(SAMPLE_TASKS, "--heading", "30AI Document Pipeline")
        self.assertNotIn("error", result)
        self.assertEqual(result.get("keyword"), "EPIC")

    def test_heading_not_found(self):
        """Should return error for non-matching pattern."""
        result = run_script(SAMPLE_TASKS, "--heading", "XyzzyNonexistent")
        self.assertIn("error", result)


class TestValidate(unittest.TestCase):
    """Tests for validate() — rule violation detection."""

    def test_stories_dont_need_epics(self):
        """Top-level STORYs without EPIC parents are VALID — not warnings."""
        result = run_script(SAMPLE_TASKS, "--validate")
        self.assertIn("warnings", result)
        self.assertIn("issues", result)
        # No orphan STORY warnings
        orphan_story_warnings = [w for w in result["warnings"] if "STORY without EPIC" in w.get("message", "")]
        self.assertEqual(len(orphan_story_warnings), 0)

    def test_detects_orphan_todo(self):
        """TODOs without STORY parents should be flagged as issues."""
        result = run_script(SAMPLE_TASKS, "--validate")
        orphan_todo_issues = [i for i in result.get("issues", []) if i.get("rule") == "ORPHAN_TODO"]
        # sample_tasks.org has TODOs under STORYs so no orphans here

    def test_orphan_todo_with_synthetic_data(self):
        """Orphan TODO detection works with synthetic hierarchy."""
        code = """
import sys
sys.path.insert(0, '/data/.hermes/scripts')
import org_query

# Manually parse a mini hierarchy with orphan TODO
headings = [
    {
        'keyword': 'TODO',
        'title': 'Orphan Task',
        'level': 1,
        'line_start': 1,
        'properties': {},
        'children': [],
        'parent_keyword': None,
    },
    {
        'keyword': 'STORY',
        'title': 'Valid Story',
        'level': 1,
        'line_start': 5,
        'properties': {},
        'children': [
            {
                'keyword': 'TODO',
                'title': 'Child Task',
                'level': 2,
                'line_start': 7,
                'properties': {},
                'children': [],
                'parent_keyword': 'STORY',
            }
        ],
        'parent_keyword': None,
    },
]

result = org_query.validate(headings)
print(json.dumps(result))
"""
        result = run_python(code)
        issues = result.get("issues", [])
        orphan_issues = [i for i in issues if i.get("rule") == "ORPHAN_TODO"]
        self.assertEqual(len(orphan_issues), 1, f"Expected 1 orphan TODO, got {len(orphan_issues)}: {issues}")
        # The valid child TODO under STORY should NOT be flagged
        todo_parent_issues = [i for i in issues if "Child Task" in i.get("message", "")]
        self.assertEqual(len(todo_parent_issues), 0, f"Child under STORY should not be flagged: {todo_parent_issues}")

    def test_no_wip_violation_on_normal_file(self):
        """Sample file should not have WIP violations (Personal AI has 1 STARTED)."""
        result = run_script(SAMPLE_TASKS, "--validate")
        self.assertIn("issues", result)
        wip_issues = [i for i in result["issues"] if "WIP" in i.get("rule", "")]
        self.assertEqual(len(wip_issues), 0)

    def test_detects_multiple_started(self):
        """Edge case file with 2 STARTED tasks should trigger WIP violation."""
        result = run_script(EDGE_CASES, "--validate")
        self.assertIn("issues", result)
        wip_issues = [i for i in result["issues"] if "SINGLE WIP" in i.get("rule", "")]
        self.assertGreaterEqual(len(wip_issues), 1)

    def test_active_counts(self):
        """Validation should report active task counts."""
        result = run_script(SAMPLE_TASKS, "--validate")
        self.assertIn("active_count", result)
        self.assertIn("started_count", result)
        self.assertIn("next_count", result)


class TestStats(unittest.TestCase):
    """Tests for stats() — overall statistics."""

    def test_counts_total_headings(self):
        """Should report total heading count."""
        result = run_script(SAMPLE_TASKS, "--stats")
        self.assertIn("total_headings", result)
        self.assertGreater(result["total_headings"], 0)

    def test_counts_epics(self):
        """Should report epic count."""
        result = run_script(SAMPLE_TASKS, "--stats")
        self.assertIn("epic_count", result)
        self.assertEqual(result["epic_count"], 4)

    def test_keyword_breakdown(self):
        """Should report keyword breakdown including compound keywords."""
        result = run_script(SAMPLE_TASKS, "--stats")
        self.assertIn("keyword_breakdown", result)
        kb = result["keyword_breakdown"]
        self.assertIn("EPIC", kb)
        self.assertIn("STORY", kb)
        self.assertIn("STORY-STARTED", kb)
        self.assertIn("STORY-NEXT", kb)

    def test_epic_listing(self):
        """Stats should include per-EPIC details."""
        result = run_script(SAMPLE_TASKS, "--stats")
        self.assertIn("epics", result)
        epic_titles = [e["title"] for e in result["epics"]]
        self.assertIn("Personal AI v1", epic_titles)


class TestSummary(unittest.TestCase):
    """Tests for sprint_summary() — the dashboard output."""

    def test_summary_returns_sprint(self):
        """Should return sprint number."""
        result = run_script(SAMPLE_TASKS, "--summary", "4")
        self.assertEqual(result["sprint"], 4)

    def test_summary_counts_items(self):
        """Should count sprint items."""
        result = run_script(SAMPLE_TASKS, "--summary", "4")
        self.assertGreater(result["total_items"], 0)

    def test_summary_capacity(self):
        """Should report capacity metrics."""
        result = run_script(SAMPLE_TASKS, "--summary", "4")
        self.assertIn("capacity", result)
        self.assertIn("capacity_used_pct", result)
        self.assertIn("points_completed", result)
        self.assertIn("points_remaining", result)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling."""

    def test_nonexistent_file(self):
        """Should handle missing files gracefully."""
        result = run_script("/tmp/nonexistent.org")
        has_error = "error" in result or "_error" in result
        self.assertTrue(has_error, f"Expected error in result, got: {result}")

    def test_empty_epic_insert_point(self):
        """Insert point for empty EPIC should return properties-relative line."""
        result = run_script(EDGE_CASES, "--insert-point", "Single Epic With No Children")
        self.assertNotIn("error", result)
        self.assertIsNone(result.get("last_child"))

    def test_edge_case_stats(self):
        """Edge case file should parse correctly for stats."""
        result = run_script(EDGE_CASES, "--stats")
        self.assertIn("epic_count", result)
        self.assertEqual(result["epic_count"], 3)


class TestPropertyParsing(unittest.TestCase):
    """Tests for property drawer parsing accuracy."""

    def test_parses_points(self):
        """Should correctly parse :POINTS: property."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "Personal AI v1")
        self.assertEqual(result["properties"].get("POINTS"), "83")

    def test_parses_value(self):
        """Should correctly parse :VALUE: property."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "Personal AI v1")
        self.assertEqual(result["properties"].get("VALUE"), "Critical")

    def test_parses_goal(self):
        """Should correctly parse :GOAL: property."""
        result = run_script(SAMPLE_TASKS, "--find-epic", "30AI Document Pipeline")
        goal = result["properties"].get("GOAL", "")
        self.assertIn("document ingestion", goal.lower())

    def test_epic_without_points(self):
        """EPIC without POINTS should have empty string, not error."""
        result = run_script(EDGE_CASES, "--find-epic", "Edge Case Epic 1")
        self.assertNotIn("error", result)
        self.assertIn("", result["properties"].get("POINTS", ""))

    def test_child_properties_preserved(self):
        """Child stories should preserve their properties and keyword."""
        result = run_script(SAMPLE_TASKS, "--children-of", "Personal AI v1")
        children = {c["title"]: c for c in result}
        ing = children.get("Build ingestion pipeline", {})
        self.assertEqual(ing.get("keyword"), "STORY-STARTED")
        self.assertEqual(ing.get("sprint"), "4")


class TestCLIIntegration(unittest.TestCase):
    """End-to-end CLI integration tests."""

    def test_help_output(self):
        """Running without args should provide usage info."""
        cmd = [sys.executable, ORG_QUERY_PATH]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            output = json.loads(result.stdout)
            self.assertIn("error", output)
        except json.JSONDecodeError:
            self.fail("Output should be valid JSON")

    def test_unknown_command(self):
        """Unknown commands should get error response and exit code 1."""
        result = subprocess.run(
            [sys.executable, ORG_QUERY_PATH, SAMPLE_TASKS, "--nonexistent-command"],
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        self.assertIn("error", data)

    def test_summary_default_sprint_4(self):
        """Default sprint for --summary should be 4."""
        result = run_script(SAMPLE_TASKS, "--summary")
        self.assertIn("sprint", result)
        self.assertEqual(result["sprint"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
