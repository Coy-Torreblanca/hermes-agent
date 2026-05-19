#!/usr/bin/env python3
"""
test_org_gbrain_adapter.py — Comprehensive test suite for org_gbrain_adapter.py.

Covers:
- resolve_gbrain_slug() — known EPIC mappings, concept patterns, generic fallback
- estimate_page_type() — EPIC→project, STORY→concept
- build_subagent_prompt() — structure and content validation
- GbrainUpdateAdapter.evaluate() — structural changes, routine skips
- CLI interface --dry-run and --print-prompt

Usage:
  python3 scripts/tests/test_org_gbrain_adapter.py -v
  pytest scripts/tests/test_org_gbrain_adapter.py -v
"""

import json
import os
import subprocess
import sys
import unittest

# ── Path Setup ───────────────────────────────────────────────────────────────
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")
sys.path.insert(0, SCRIPTS_DIR)

# ── Fixtures ─────────────────────────────────────────────────────────────────

STRUCTURAL_CHANGE_REPORT = {
    "script_name": "org_query.py",
    "operation": "create_todo",
    "filepath": "/data/syncthing/Sync/org/work/tasks.org",
    "merits_gbrain": True,
    "classification": "structural",
    "reason": "New STORY created",
    "relevant_entities": ["LLM gbrain Sync Design"],
    "new_headings": [
        {
            "title": "LLM gbrain Sync Design",
            "keyword": "STORY",
            "level": 2,
            "properties": {
                "ID": "F9E73A4B",
                "SPRINT": "4",
                "POINTS": "2",
                "VALUE": "Essential",
                "GOAL": "Design parallel gbrain sync agent",
            },
            "line_start": 450,
            "parent_title": "Personal AI v1",
            "tags": ["gbrain", "sync", "automation"],
        }
    ],
    "metadata_changes": [],
    "state_transitions": [],
    "removed_headings": [],
}

ROUTINE_CHANGE_REPORT = {
    "script_name": "org_query.py",
    "operation": "state_change",
    "filepath": "/data/syncthing/Sync/org/work/tasks.org",
    "merits_gbrain": False,
    "classification": "routine",
    "reason": "Routine state transitions: 1 item(s) changed state",
    "relevant_entities": ["Auth Middleware"],
    "new_headings": [],
    "metadata_changes": [],
    "state_transitions": [{"title": "Auth MW", "from": "TODO", "to": "NEXT"}],
    "removed_headings": [],
}

METADATA_CHANGE_REPORT = {
    "script_name": "org_query.py",
    "operation": "property_update",
    "filepath": "/data/syncthing/Sync/org/work/tasks.org",
    "merits_gbrain": True,
    "classification": "structural",
    "reason": "Structural property changes: 1 field(s) modified",
    "relevant_entities": ["Second Brain CRUD"],
    "new_headings": [],
    "metadata_changes": [
        {
            "title": "Second Brain CRUD",
            "keyword": "STORY-STARTED",
            "properties": {"POINTS": {"from": "3", "to": "5"}},
        }
    ],
    "state_transitions": [],
    "removed_headings": [],
}

NEW_EPIC_REPORT = {
    "script_name": "org_query.py",
    "operation": "create_epic",
    "filepath": "/data/syncthing/Sync/org/work/tasks.org",
    "merits_gbrain": True,
    "classification": "structural",
    "reason": "New EPIC created",
    "relevant_entities": ["Big New Project"],
    "new_headings": [
        {
            "title": "Big New Project",
            "keyword": "EPIC",
            "level": 1,
            "properties": {"ID": "ABCD", "SPRINT": "5"},
            "line_start": 500,
            "parent_title": "",
            "tags": [],
        }
    ],
    "metadata_changes": [],
    "state_transitions": [],
    "removed_headings": [],
}


# ── Test Suite ───────────────────────────────────────────────────────────────

class TestResolveSlug(unittest.TestCase):
    """resolve_gbrain_slug() — title to gbrain slug mapping."""

    def setUp(self):
        from org_gbrain_adapter import resolve_gbrain_slug
        self.resolve = resolve_gbrain_slug

    def test_known_epic_personal_ai(self):
        slug = self.resolve("Personal AI v1", {"keyword": "EPIC"})
        self.assertEqual(slug, "projects/personalai")

    def test_known_epic_30ai(self):
        slug = self.resolve("30ai", {"keyword": "EPIC"})
        self.assertEqual(slug, "projects/30ai")

    def test_known_epic_second_brain(self):
        slug = self.resolve("Second Brain", {"keyword": "EPIC"})
        self.assertEqual(slug, "projects/personalai/second-brain")

    def test_concept_pattern_compliance(self):
        slug = self.resolve("Org Mode Compliance", {"keyword": "STORY"})
        self.assertEqual(slug, "concepts/org-mode-compliance")

    def test_concept_pattern_architecture(self):
        slug = self.resolve("System Architecture Design", {"keyword": "STORY"})
        self.assertEqual(slug, "concepts/system-architecture-design")

    def test_concept_pattern_pipeline(self):
        slug = self.resolve("Data Pipeline", {"keyword": "STORY"})
        self.assertEqual(slug, "concepts/data-pipeline")

    def test_generic_epic_fallback(self):
        slug = self.resolve("Custom EPIC Name", {"keyword": "EPIC"})
        self.assertEqual(slug, "projects/custom-epic-name")

    def test_icebox_suffix_stripped(self):
        slug = self.resolve("My EPIC [ICEBOX]", {"keyword": "EPIC"})
        # Brackets are stripped but ICEBOX remains in slug
        self.assertIn("my-epic", slug)

    def test_generic_story_fallback_projects(self):
        slug = self.resolve("Fix login bug", {"keyword": "STORY"})
        self.assertTrue(slug.startswith("projects/"))

    def test_case_insensitive_match(self):
        slug = self.resolve("PERSONAL AI V1", {"keyword": "EPIC"})
        self.assertEqual(slug, "projects/personalai")

    def test_no_keyword_provided(self):
        slug = self.resolve("Some Item", {})
        self.assertTrue(slug.startswith("projects/"))


class TestEstimatePageType(unittest.TestCase):
    """estimate_page_type() — keyword to type mapping."""

    def setUp(self):
        from org_gbrain_adapter import estimate_page_type
        self.estimate = estimate_page_type

    def test_epic_is_project(self):
        self.assertEqual(self.estimate("Personal AI v1", "EPIC"), "project")

    def test_story_is_concept(self):
        self.assertEqual(self.estimate("Auth Middleware", "STORY"), "concept")

    def test_story_started_is_concept(self):
        self.assertEqual(self.estimate("Active Work", "STORY-STARTED"), "concept")

    def test_todo_is_concept(self):
        self.assertEqual(self.estimate("Fix Bug", "TODO"), "concept")

    def test_unknown_keyword_is_concept(self):
        self.assertEqual(self.estimate("Something", ""), "concept")

    def test_story_with_compliance_in_title(self):
        self.assertEqual(self.estimate("Compliance Standards", "STORY"), "concept")

    def test_story_with_pipeline_in_title(self):
        self.assertEqual(self.estimate("CI/CD Pipeline", "STORY"), "concept")


class TestBuildSubagentPrompt(unittest.TestCase):
    """build_subagent_prompt() — prompt generation."""

    def setUp(self):
        from org_gbrain_adapter import build_subagent_prompt
        self.build = build_subagent_prompt

    def test_structural_change_prompt_contains_key_elements(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertIn("LLM-Driven GBrain Update", prompt)
        self.assertIn("## New Headings Created", prompt)
        self.assertIn("LLM gbrain Sync Design", prompt)
        self.assertIn("projects/llm-gbrain-sync-design", prompt)
        self.assertIn("## Instructions", prompt)
        self.assertIn("search gbrain first", prompt.lower())

    def test_routine_change_prompt_has_skip_section(self):
        prompt = self.build(ROUTINE_CHANGE_REPORT)
        self.assertIn("State Transitions (Routine", prompt)
        self.assertIn("Auth MW", prompt)

    def test_metadata_change_prompt(self):
        prompt = self.build(METADATA_CHANGE_REPORT)
        self.assertIn("## Metadata Changes", prompt)
        self.assertIn("Second Brain CRUD", prompt)
        self.assertIn("POINTS", prompt)
        self.assertIn("3", prompt)
        self.assertIn("5", prompt)

    def test_new_epic_prompt(self):
        prompt = self.build(NEW_EPIC_REPORT)
        self.assertIn("## New Headings Created", prompt)
        self.assertIn("Big New Project", prompt)
        self.assertIn("projects/big-new-project", prompt)

    def test_prompt_includes_citation_instructions(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertIn("Citation format", prompt)

    def test_prompt_includes_timestamp(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertIn("Change timestamp", prompt)

    def test_prompt_includes_full_property_details(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertIn("F9E73A4B", prompt)
        self.assertIn("Essential", prompt)
        self.assertIn("Design parallel", prompt)

    def test_prompt_source_section_contains_metadata(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertIn("## Source Information", prompt)
        self.assertIn("org_query.py", prompt)
        self.assertIn("create_todo", prompt)

    def test_prompt_max_length_reasonable(self):
        prompt = self.build(STRUCTURAL_CHANGE_REPORT)
        self.assertLess(len(prompt), 5000)  # Should be concise


class TestGbrainUpdateAdapter(unittest.TestCase):
    """GbrainUpdateAdapter.evaluate() — full evaluation pipeline."""

    def setUp(self):
        from org_gbrain_adapter import GbrainUpdateAdapter
        self.adapter = GbrainUpdateAdapter()

    def test_structural_change_returns_decisions(self):
        result = self.adapter.evaluate(STRUCTURAL_CHANGE_REPORT)
        self.assertTrue(result["merits_gbrain"])
        self.assertGreater(result["decision_count"], 0)
        self.assertIsNotNone(result["subagent_prompt"])
        first = result["decisions"][0]
        self.assertEqual(first["action"], "search_first")
        self.assertEqual(first["entity"], "LLM gbrain Sync Design")

    def test_routine_change_skips(self):
        result = self.adapter.evaluate(ROUTINE_CHANGE_REPORT)
        self.assertFalse(result["merits_gbrain"])
        self.assertIsNone(result["subagent_prompt"])
        self.assertEqual(result["decision_count"], 0)

    def test_metadata_change_detects_correctly(self):
        result = self.adapter.evaluate(METADATA_CHANGE_REPORT)
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 1)
        self.assertEqual(result["decisions"][0]["action"], "update_page")

    def test_new_epic_routes_to_search_first(self):
        result = self.adapter.evaluate(NEW_EPIC_REPORT)
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 1)
        self.assertEqual(result["decisions"][0]["action"], "search_first")
        self.assertEqual(result["decisions"][0]["suggested_slug"], "projects/big-new-project")

    def test_search_first_has_reason(self):
        result = self.adapter.evaluate(NEW_EPIC_REPORT)
        self.assertIn("reason", result["decisions"][0])
        self.assertIn("New", result["decisions"][0]["reason"])

    def test_decision_has_suggested_slug(self):
        result = self.adapter.evaluate(STRUCTURAL_CHANGE_REPORT)
        d = result["decisions"][0]
        self.assertIn("suggested_slug", d)
        self.assertTrue(d["suggested_slug"].startswith("projects/") or d["suggested_slug"].startswith("concepts/"))

    def test_evaluate_on_empty_report(self):
        empty = {
            "merits_gbrain": False, "classification": "unknown",
            "reason": "No changes", "new_headings": [],
            "metadata_changes": [], "state_transitions": [],
            "removed_headings": [],
        }
        result = self.adapter.evaluate(empty)
        self.assertFalse(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 0)

    def test_evaluate_with_removed_heading(self):
        report = {
            "merits_gbrain": True, "classification": "structural",
            "reason": "Heading removed", "new_headings": [],
            "metadata_changes": [], "state_transitions": [],
            "removed_headings": [{"title": "Old Thing", "keyword": "STORY"}],
        }
        result = self.adapter.evaluate(report)
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 1)
        self.assertEqual(result["decisions"][0]["entity"], "Old Thing")
        self.assertEqual(result["decisions"][0]["action"], "update_page")


class TestCLI(unittest.TestCase):
    """CLI interface tests for org_gbrain_adapter.py."""

    def setUp(self):
        self.script = os.path.join(SCRIPTS_DIR, "org_gbrain_adapter.py")

    def run_cli(self, *args) -> dict | str:
        import tempfile
        # Build args properly
        cmd = [sys.executable, self.script]
        cmd.extend(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "--print-prompt" in args:
            return result.stdout  # Raw text
        try:
            return json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return {"_error": result.stderr.strip(), "_stdout": result.stdout.strip()}

    def save_payload(self, payload: dict) -> str:
        import tempfile
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp")
        json.dump(payload, f)
        f.close()
        return f.name

    def test_cli_dry_run_structural(self):
        path = self.save_payload(STRUCTURAL_CHANGE_REPORT)
        result = self.run_cli("--payload", path, "--dry-run")
        self.assertIn("merits_gbrain", result)
        self.assertTrue(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 1)
        os.unlink(path)

    def test_cli_dry_run_routine(self):
        path = self.save_payload(ROUTINE_CHANGE_REPORT)
        result = self.run_cli("--payload", path, "--dry-run")
        self.assertFalse(result["merits_gbrain"])
        self.assertEqual(result["decision_count"], 0)
        os.unlink(path)

    def test_cli_print_prompt(self):
        path = self.save_payload(STRUCTURAL_CHANGE_REPORT)
        output = self.run_cli("--payload", path, "--print-prompt")
        self.assertIsInstance(output, str)
        self.assertIn("LLM-Driven GBrain Update", output)
        self.assertIn("Instructions", output)
        os.unlink(path)

    def test_cli_default_output_has_decision_count(self):
        path = self.save_payload(STRUCTURAL_CHANGE_REPORT)
        result = self.run_cli("--payload", path)
        self.assertIn("decision_count", result)
        os.unlink(path)

    def test_cli_dry_run_shows_decisions_detail(self):
        path = self.save_payload(NEW_EPIC_REPORT)
        result = self.run_cli("--payload", path, "--dry-run")
        self.assertIn("decisions", result)
        d = result["decisions"][0]
        self.assertIn("entity", d)
        self.assertIn("action", d)
        self.assertIn("suggested_slug", d)
        os.unlink(path)

    def test_cli_from_hook_accepts_report(self):
        path = self.save_payload(STRUCTURAL_CHANGE_REPORT)
        result = self.run_cli("--from-hook", path, "--dry-run")
        self.assertTrue(result["merits_gbrain"])
        os.unlink(path)

    def test_cli_missing_payload_error(self):
        result = self.run_cli()
        self.assertIn("error", result)

    def test_cli_from_hook_matches_payload(self):
        path = self.save_payload(STRUCTURAL_CHANGE_REPORT)
        payload_result = self.run_cli("--payload", path, "--dry-run")
        hook_result = self.run_cli("--from-hook", path, "--dry-run")
        self.assertEqual(payload_result["merits_gbrain"], hook_result["merits_gbrain"])
        self.assertEqual(payload_result["decision_count"], hook_result["decision_count"])
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
