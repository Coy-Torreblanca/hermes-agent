#!/usr/bin/env python3
"""
test_org_change_hook.py — Comprehensive test suite for org_change_hook.py.

Covers:
- HeadingSnapshot construction from raw dicts
- FileSnapshot creation and heading finding
- OrgChangeDiff computation (new, removed, metadata, state transitions)
- classify_change() — structural vs routine classification
- Audit logging (log_gbrain_update, get_recent_logs)
- OrgChangeHook full lifecycle (capture_pre → capture_post → finalize)
- All 4 classification routes: new entity, property change, state flip, inbox TODO

Usage:
  python3 scripts/tests/test_org_change_hook.py -v
  pytest scripts/tests/test_org_change_hook.py -v
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# ── Path Setup ───────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")
sys.path.insert(0, SCRIPTS_DIR)


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_HEADING_DICT = {
    "title": "Personal AI v1",
    "keyword": "EPIC",
    "level": 1,
    "properties": {"ID": "AAAA", "SPRINT": "4"},
    "line_start": 1,
    "line_end": 50,
    "parent_title": "",
    "body_text": "The personal AI project",
    "tags": ["ai", "personal"],
    "children": [
        {
            "title": "Second Brain CRUD",
            "keyword": "STORY",
            "level": 2,
            "properties": {"ID": "BBBB", "SPRINT": "4", "POINTS": "3", "VALUE": "Essential", "GOAL": "CRUD operations for gbrain"},
            "line_start": 10,
            "line_end": 20,
            "parent_title": "Personal AI v1",
            "body_text": "",
            "tags": [],
            "children": [],
        }
    ],
}

SAMPLE_STORY_DICT = {
    "title": "Auth Middleware",
    "keyword": "STORY-STARTED",
    "level": 2,
    "properties": {"ID": "CCCC", "SPRINT": "4", "POINTS": "5", "VALUE": "Important"},
    "line_start": 30,
    "line_end": 40,
    "parent_title": "Personal AI v1",
    "body_text": "JWT auth layer",
    "tags": [],
    "children": [],
}

SAMPLE_TODO_DICT = {
    "title": "Fix login bug",
    "keyword": "TODO",
    "level": 3,
    "properties": {"ID": "DDDD"},
    "line_start": 50,
    "line_end": 55,
    "parent_title": "Auth Middleware",
    "body_text": "",
    "tags": [],
    "children": [],
}


# ── Test Suite ───────────────────────────────────────────────────────────────

class TestHeadingSnapshot(unittest.TestCase):
    """HeadingSnapshot construction from raw dicts."""

    def setUp(self):
        from org_change_hook import HeadingSnapshot
        self.HeadingSnapshot = HeadingSnapshot

    def test_from_epic_dict(self):
        h = self.HeadingSnapshot(SAMPLE_HEADING_DICT)
        self.assertEqual(h.title, "Personal AI v1")
        self.assertEqual(h.keyword, "EPIC")
        self.assertEqual(h.level, 1)
        self.assertEqual(h.properties["ID"], "AAAA")
        self.assertEqual(h.properties["SPRINT"], "4")
        self.assertEqual(len(h.children), 1)
        self.assertEqual(h.children[0].title, "Second Brain CRUD")

    def test_from_story_dict(self):
        h = self.HeadingSnapshot(SAMPLE_STORY_DICT)
        self.assertEqual(h.title, "Auth Middleware")
        self.assertEqual(h.keyword, "STORY-STARTED")
        self.assertEqual(h.properties["POINTS"], "5")
        self.assertEqual(h.properties["VALUE"], "Important")

    def test_from_todo_dict(self):
        h = self.HeadingSnapshot(SAMPLE_TODO_DICT)
        self.assertEqual(h.title, "Fix login bug")
        self.assertEqual(h.keyword, "TODO")
        self.assertEqual(h.level, 3)

    def test_to_dict_serialization(self):
        h = self.HeadingSnapshot(SAMPLE_HEADING_DICT)
        d = h.to_dict()
        self.assertEqual(d["title"], "Personal AI v1")
        self.assertEqual(d["keyword"], "EPIC")
        self.assertEqual(d["children_count"], 1)
        self.assertEqual(d["properties"]["SPRINT"], "4")

    def test_empty_properties(self):
        d = {"title": "Empty", "keyword": "TODO", "level": 1, "properties": {},
             "line_start": 1, "line_end": 2, "parent_title": "", "body_text": "",
             "tags": [], "children": []}
        h = self.HeadingSnapshot(d)
        self.assertEqual(h.properties, {})
        self.assertEqual(len(h.children), 0)

    def test_nested_children(self):
        d = {
            "title": "Root", "keyword": "EPIC", "level": 1,
            "properties": {}, "line_start": 1, "line_end": 100,
            "parent_title": "", "body_text": "", "tags": [], "children": [
                {
                    "title": "Child", "keyword": "STORY", "level": 2,
                    "properties": {}, "line_start": 10, "line_end": 50,
                    "parent_title": "Root", "body_text": "", "tags": [], "children": [
                        {
                            "title": "Grandchild", "keyword": "TODO", "level": 3,
                            "properties": {}, "line_start": 20, "line_end": 30,
                            "parent_title": "Child", "body_text": "", "tags": [], "children": [],
                        }
                    ],
                }
            ],
        }
        h = self.HeadingSnapshot(d)
        self.assertEqual(len(h.children), 1)
        self.assertEqual(h.children[0].children[0].title, "Grandchild")


class TestFileSnapshot(unittest.TestCase):
    """FileSnapshot creation and heading finding."""

    def setUp(self):
        from org_change_hook import FileSnapshot, HeadingSnapshot
        self.FileSnapshot = FileSnapshot

    def test_from_empty_list(self):
        fs = self.FileSnapshot("/tmp/test.org", [])
        self.assertEqual(len(fs.headings), 0)
        self.assertTrue(fs.timestamp.endswith("Z") or "T" in fs.timestamp)

    def test_from_heading_list(self):
        fs = self.FileSnapshot("/tmp/test.org", [SAMPLE_HEADING_DICT, SAMPLE_STORY_DICT])
        self.assertEqual(len(fs.headings), 2)
        self.assertEqual(fs.headings[0].title, "Personal AI v1")
        self.assertEqual(fs.headings[1].title, "Auth Middleware")

    def test_find_heading_exact(self):
        fs = self.FileSnapshot("/tmp/test.org", [SAMPLE_HEADING_DICT])
        h = fs.find_heading("Personal AI v1", partial=False)
        self.assertIsNotNone(h)
        self.assertEqual(h.title, "Personal AI v1")

    def test_find_heading_partial(self):
        fs = self.FileSnapshot("/tmp/test.org", [SAMPLE_HEADING_DICT])
        h = fs.find_heading("Personal")
        self.assertIsNotNone(h)
        self.assertEqual(h.title, "Personal AI v1")

    def test_find_heading_nested(self):
        fs = self.FileSnapshot("/tmp/test.org", [SAMPLE_HEADING_DICT])
        h = fs.find_heading("Second Brain")
        self.assertIsNotNone(h)
        self.assertEqual(h.title, "Second Brain CRUD")

    def test_find_heading_missing(self):
        fs = self.FileSnapshot("/tmp/test.org", [SAMPLE_HEADING_DICT])
        h = fs.find_heading("Nonexistent")
        self.assertIsNone(h)

    def test_filepath_stored(self):
        fs = self.FileSnapshot("/data/test.org", [])
        self.assertEqual(fs.filepath, "/data/test.org")


class TestOrgChangeDiff(unittest.TestCase):
    """OrgChangeDiff computation."""

    def setUp(self):
        from org_change_hook import FileSnapshot, OrgChangeDiff
        self.FileSnapshot = FileSnapshot
        self.OrgChangeDiff = OrgChangeDiff

    def make_fs(self, headings):
        return self.FileSnapshot("/tmp/test.org", headings)

    def test_no_changes(self):
        pre = self.make_fs([SAMPLE_HEADING_DICT])
        post = self.make_fs([SAMPLE_HEADING_DICT])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.new_headings), 0)
        self.assertEqual(len(diff.removed_headings), 0)
        self.assertEqual(len(diff.metadata_changes), 0)
        self.assertEqual(len(diff.state_transitions), 0)

    def test_new_story_detected(self):
        pre = self.make_fs([SAMPLE_HEADING_DICT])
        post = self.make_fs([SAMPLE_HEADING_DICT, SAMPLE_STORY_DICT])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.new_headings), 1)
        self.assertEqual(diff.new_headings[0]["title"], "Auth Middleware")
        self.assertEqual(diff.new_headings[0]["keyword"], "STORY-STARTED")

    def test_removed_heading_detected(self):
        pre = self.make_fs([SAMPLE_HEADING_DICT, SAMPLE_STORY_DICT])
        post = self.make_fs([SAMPLE_HEADING_DICT])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.removed_headings), 1)
        self.assertEqual(diff.removed_headings[0]["title"], "Auth Middleware")

    def test_state_transition_detected(self):
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["keyword"] = "STORY-DONE"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.state_transitions), 1)
        self.assertEqual(diff.state_transitions[0]["from"], "STORY-STARTED")
        self.assertEqual(diff.state_transitions[0]["to"], "STORY-DONE")

    def test_metadata_change_detected(self):
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(SAMPLE_STORY_DICT["properties"])
        post_h["properties"]["POINTS"] = "8"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.metadata_changes), 1)
        self.assertEqual(diff.metadata_changes[0]["title"], "Auth Middleware")
        self.assertIn("POINTS", diff.metadata_changes[0]["properties"])
        self.assertEqual(diff.metadata_changes[0]["properties"]["POINTS"]["from"], "5")
        self.assertEqual(diff.metadata_changes[0]["properties"]["POINTS"]["to"], "8")

    def test_multiple_changes(self):
        pre = self.make_fs([SAMPLE_HEADING_DICT])
        post = self.make_fs([SAMPLE_HEADING_DICT, SAMPLE_STORY_DICT, SAMPLE_TODO_DICT])
        diff = self.OrgChangeDiff(pre, post)
        self.assertEqual(len(diff.new_headings), 2)  # STORY + TODO (nested under EPIC, but top-level additions)

    def test_diff_to_dict(self):
        pre = self.make_fs([SAMPLE_HEADING_DICT])
        post = self.make_fs([SAMPLE_HEADING_DICT, SAMPLE_STORY_DICT])
        diff = self.OrgChangeDiff(pre, post)
        d = diff.to_dict()
        self.assertIn("filepath", d)
        self.assertIn("pre_timestamp", d)
        self.assertIn("post_timestamp", d)
        self.assertEqual(len(d["new_headings"]), 1)


class TestClassifyChange(unittest.TestCase):
    """Change classification: structural vs routine."""

    def setUp(self):
        from org_change_hook import FileSnapshot, OrgChangeDiff, classify_change
        self.FileSnapshot = FileSnapshot
        self.OrgChangeDiff = OrgChangeDiff
        self.classify_change = classify_change

    def make_fs(self, headings):
        return self.FileSnapshot("/tmp/test.org", headings)

    def test_new_story_is_structural(self):
        """New STORY keyword → merits_gbrain=True"""
        pre = self.make_fs([])
        post = self.make_fs([SAMPLE_STORY_DICT])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "create_todo")
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["classification"], "structural")
        self.assertIn("Auth Middleware", result["relevant_entities"])

    def test_new_epic_is_structural(self):
        """New EPIC keyword → merits_gbrain=True"""
        pre = self.make_fs([])
        post = self.make_fs([SAMPLE_HEADING_DICT])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "create_epic")
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["classification"], "structural")

    def test_goal_change_is_structural(self):
        """GOAL property change → merits_gbrain=True"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(pre_h["properties"])
        post_h["properties"]["GOAL"] = "New goal description"
        # Remove GOAL from pre to make it actually new
        pre_h["properties"] = {k: v for k, v in pre_h["properties"].items() if k != "GOAL"}
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "metadata_update")
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["classification"], "structural")

    def test_points_change_is_structural(self):
        """POINTS property change → merits_gbrain=True"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(pre_h["properties"])
        post_h["properties"]["POINTS"] = "8"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "points_update")
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["classification"], "structural")

    def test_value_change_is_structural(self):
        """VALUE property change → merits_gbrain=True"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(pre_h["properties"])
        post_h["properties"]["VALUE"] = "Essential"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "value_update")
        self.assertTrue(result["merits_gbrain"])

    def test_type_change_is_structural(self):
        """TYPE property change → merits_gbrain=True"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(pre_h["properties"])
        post_h["properties"]["TYPE"] = "feature"
        pre_h["properties"] = {k: v for k, v in pre_h["properties"].items() if k != "TYPE"}
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "type_update")
        self.assertTrue(result["merits_gbrain"])

    def test_state_transition_is_routine(self):
        """TODO→DONE → merits_gbrain=False"""
        pre_h = {"title": "Task", "keyword": "TODO", "level": 3,
                 "properties": {"ID": "EEEE"}, "line_start": 1, "line_end": 5,
                 "parent_title": "", "body_text": "", "tags": [], "children": []}
        post_h = dict(pre_h)
        post_h["keyword"] = "DONE"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "state_change")
        self.assertFalse(result["merits_gbrain"])
        self.assertEqual(result["classification"], "routine")

    def test_new_todo_in_inbox_is_routine(self):
        """New TODO in inbox (no EPIC/STORY parent) → merits_gbrain=False"""
        pre = self.make_fs([])
        post = self.make_fs([SAMPLE_TODO_DICT])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "create_todo")
        self.assertFalse(result["merits_gbrain"])
        self.assertEqual(result["classification"], "routine")

    def test_story_started_to_story_done_is_routine(self):
        """STORY-STARTED→STORY-DONE → merits_gbrain=False"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["keyword"] = "STORY-DONE"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "state_change")
        self.assertFalse(result["merits_gbrain"])

    def test_removed_heading_is_structural(self):
        """Heading removed → merits_gbrain=True"""
        pre = self.make_fs([SAMPLE_STORY_DICT])
        post = self.make_fs([])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "delete")
        self.assertTrue(result["merits_gbrain"])

    def test_sprit_change_is_routine(self):
        """SPRINT number change → merits_gbrain=False"""
        pre_h = dict(SAMPLE_STORY_DICT)
        post_h = dict(SAMPLE_STORY_DICT)
        post_h["properties"] = dict(pre_h["properties"])
        post_h["properties"]["SPRINT"] = "5"
        pre = self.make_fs([pre_h])
        post = self.make_fs([post_h])
        diff = self.OrgChangeDiff(pre, post)
        result = self.classify_change(diff, "sprint_update")
        self.assertFalse(result["merits_gbrain"])


class TestAuditLogging(unittest.TestCase):
    """log_gbrain_update and get_recent_logs."""

    def setUp(self):
        from org_change_hook import log_gbrain_update, get_recent_logs, GBRAIN_AUDIT_LOG
        self.log_gbrain_update = log_gbrain_update
        self.get_recent_logs = get_recent_logs
        self.log_path = Path(GBRAIN_AUDIT_LOG)
        # Remember pre-test log length
        self.pre_log_count = len(self.get_recent_logs(999))

    def test_log_entry_written(self):
        report = {
            "script_name": "test_script",
            "operation": "test_operation",
            "filepath": "/tmp/test.org",
            "merits_gbrain": True,
            "classification": "structural",
            "reason": "Test reason",
            "relevant_entities": ["Test Entity"],
            "new_headings_count": 1,
            "state_transitions_count": 0,
            "metadata_changes_count": 0,
        }
        result = self.log_gbrain_update(report)
        self.assertTrue(result["logged"])
        self.assertIn("entry", result)
        self.assertEqual(result["entry"]["script"], "test_script")
        self.assertEqual(result["entry"]["merits_gbrain"], True)

    def test_get_recent_logs(self):
        # Write a unique entry we can find
        report = {
            "script_name": "findable_test",
            "operation": "test",
            "filepath": "/tmp/test.org",
            "merits_gbrain": False,
            "classification": "routine",
            "reason": "Findable entry",
            "relevant_entities": [],
            "new_headings": [],
            "state_transitions": [],
            "new_headings_count": 0,
            "state_transitions_count": 0,
            "metadata_changes_count": 0,
        }
        self.log_gbrain_update(report)
        logs = self.get_recent_logs(10)
        self.assertGreater(len(logs), 0)
        # The latest entry should be our findable_test
        found = any(e["script"] == "findable_test" for e in logs)
        self.assertTrue(found)

    def test_log_entry_structure(self):
        report = {
            "script_name": "struct_test",
            "operation": "create",
            "filepath": "/tmp/struct.org",
            "merits_gbrain": True,
            "classification": "structural",
            "reason": "New STORY",
            "relevant_entities": ["Struct Entity"],
            "new_headings": [{"title": "New Story", "keyword": "STORY"}],
            "new_headings_count": 1,
            "state_transitions": [{"title": "Old Task", "from": "TODO", "to": "DONE"}],
            "state_transitions_count": 1,
            "metadata_changes_count": 0,
        }
        result = self.log_gbrain_update(report)
        entry = result["entry"]
        self.assertIn("timestamp", entry)
        self.assertIn("gbrain_action_taken", entry)
        self.assertFalse(entry["gbrain_action_taken"])
        self.assertEqual(entry["new_headings_count"], 1)
        self.assertEqual(entry["state_transitions_count"], 1)

    def test_get_recent_logs_returns_list(self):
        logs = self.get_recent_logs(5)
        self.assertIsInstance(logs, list)

    def test_get_recent_logs_empty_file(self):
        from org_change_hook import GBRAIN_AUDIT_LOG
        path = Path(GBRAIN_AUDIT_LOG)
        if path.exists():
            # Can't temporarily delete, but can test limit=0
            logs = self.get_recent_logs(999)
            self.assertIsInstance(logs, list)


class TestOrgChangeHookLifecycle(unittest.TestCase):
    """OrgChangeHook full lifecycle test."""

    def setUp(self):
        from org_change_hook import OrgChangeHook
        self.OrgChangeHook = OrgChangeHook
        self.temp_dir = tempfile.mkdtemp()

    def make_org_file(self, content: str) -> str:
        path = os.path.join(self.temp_dir, "test.org")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_process_write_returns_context(self):
        hook = self.OrgChangeHook()
        path = self.make_org_file("* TODO First task\n")
        result = hook.process_write(
            script_name="test",
            operation="create_todo",
            filepath=path,
            params={"title": "Test"},
        )
        self.assertIn("filepath", result)
        self.assertEqual(result["filepath"], path)
        self.assertTrue(result["pre_captured"])

    def test_finalize_empty_cycle(self):
        hook = self.OrgChangeHook()
        path = self.make_org_file("* TODO First task\n")
        hook.capture_pre(path)
        hook.capture_post(path)
        report = hook.analyze(
            filepath=path,
            script_name="test",
            operation="read",
        )
        self.assertFalse(report["merits_gbrain"])
        self.assertEqual(report["classification"], "unknown")

    def test_finalize_with_change(self):
        """Capture pre, modify file, capture post, analyze change."""
        hook = self.OrgChangeHook()
        path = self.make_org_file("* EPIC Project\n:PROPERTIES:\n:ID:       XXXX\n:END:\n")
        hook.capture_pre(path)

        # Simulate writing a new STORY
        with open(path, "a") as f:
            f.write("** STORY New Feature\n:PROPERTIES:\n:ID:       YYYY\n:SPRINT:   4\n:POINTS:   3\n:END:\n")

        hook.capture_post(path)
        report = hook.analyze(
            filepath=path,
            script_name="test",
            operation="create_todo",
        )
        self.assertTrue(report["merits_gbrain"])
        self.assertEqual(report["classification"], "structural")
        self.assertTrue(len(report["new_headings"]) > 0)

    def test_process_write_to_finalize_cycle(self):
        """Full process_write → modify → finalize cycle."""
        hook = self.OrgChangeHook()
        path = self.make_org_file("* EPIC Test\n:PROPERTIES:\n:ID:       ZZZZ\n:END:\n")

        ctx = hook.process_write(
            script_name="test",
            operation="create_todo",
            filepath=path,
            params={"title": "New Task"},
        )

        # Modify the file
        with open(path, "a") as f:
            f.write("** TODO New Task\n:PROPERTIES:\n:ID:       WWWW\n:END:\n")

        report = hook.finalize(ctx)
        self.assertFalse(report["merits_gbrain"])  # TODO is routine
        self.assertEqual(len(report["new_headings"]), 1)

    def test_prepare_gbrain_payload(self):
        """prepare_gbrain_payload returns expected structure."""
        hook = self.OrgChangeHook()
        path = self.make_org_file("* EPIC Test\n")
        hook.capture_pre(path)
        hook.capture_post(path)
        report = hook.analyze(path, "test", "test")
        payload = hook.prepare_gbrain_payload(report)
        self.assertEqual(payload["source"], "org_change_hook")
        self.assertIn("operation", payload)
        self.assertIn("new_headings", payload)
        self.assertIn("metadata_changes", payload)
        self.assertIn("state_transitions", payload)
        self.assertIn("hook_timestamp", payload)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestCLI(unittest.TestCase):
    """CLI interface tests for org_change_hook.py."""

    def setUp(self):
        self.script = os.path.join(SCRIPTS_DIR, "org_change_hook.py")

    def run_cli(self, *args) -> dict:
        result = __import__("subprocess").run(
            [sys.executable, self.script] + list(args),
            capture_output=True, text=True
        )
        try:
            return json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return {"_error": result.stderr.strip(), "_stdout": result.stdout.strip()}

    def test_cli_log_shows_entries(self):
        result = self.run_cli("--log", "--log-limit", "5")
        self.assertIn("entries", result)
        self.assertIsInstance(result["entries"], list)

    def test_cli_capture_pre_and_post(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False, dir="/tmp") as f:
            f.write("* TODO Test\n")
            pre_path = f.name
        post_path = pre_path  # Same file for pre and post
        result = self.run_cli("--capture-pre", pre_path, "--capture-post", post_path,
                              "--script", "cli_test", "--operation", "test")
        self.assertIn("merits_gbrain", result)
        self.assertIn("classification", result)
        self.assertIn("audit", result)
        self.assertTrue(result["audit"]["logged"])
        os.unlink(pre_path)

    def test_cli_capture_pre_only(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".org", delete=False, dir="/tmp") as f:
            f.write("* TODO Pre Only\n")
            path = f.name
        result = self.run_cli("--capture-pre", path, "--script", "cli_test")
        self.assertEqual(result["status"], "pre_captured")
        self.assertIn("headings_count", result)
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
