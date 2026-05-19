#!/usr/bin/env python3
"""
org_change_hook.py — Post-change hook architecture for org-mode file operations.

Captures pre/post state around org writes, computes structured diffs,
classifies changes (structural vs routine), and routes to gbrain.

Designed to be called from org_query.py after write operations, or
wrapped around habit_query.py mutations.

Usage:
    # As an import:
    from org_change_hook import OrgChangeHook

    hook = OrgChangeHook()
    result = hook.process_write(
        script_name="org_query.py",
        operation="create_todo",
        params={"title": "New Story", "destination": "Personal AI v1"},
        filepath="/data/syncthing/Sync/org/work/tasks.org",
        pre_state=pre_parse,
        post_state=post_parse,
    )
    if result["merits_gbrain"]:
        report = hook.prepare_change_report(result)
        # route to gbrain adapter

    # As a CLI wrapper:
    # org_change_hook.py --capture-pre tasks.org --capture-post tasks.org \\
    #   --script "org_query.py --create-todo '...'"
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Constants ──────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(os.path.expanduser("~/.hermes/scripts"))
GBRAIN_AUDIT_LOG = SCRIPTS_DIR / "gbrain_update_log.jsonl"

# ─── Change Classification Thresholds ───────────────────────────────────────

# These property keys signal structural changes when added/removed/modified
STRUCTURAL_PROPERTIES = {"GOAL", "VALUE", "POINTS", "TYPE"}

# These keywords indicate a new top-level container was created
STRUCTURAL_KEYWORDS = {"EPIC", "STORY", "STORY-STARTED", "STORY-NEXT"}

# State transitions that are routine (no gbrain update needed)
ROUTINE_KEYWORDS = {"TODO", "STARTED", "NEXT", "DONE", "CANCELLED", "WAITING",
                    "STORY-DONE", "STORY-WAITING"}


# ─── Data Classes ───────────────────────────────────────────────────────────

class HeadingSnapshot:
    """Snapshot of a single org heading at a point in time."""
    
    def __init__(self, heading_dict: dict):
        self.title = heading_dict.get("title", "")
        self.keyword = heading_dict.get("keyword", "")
        self.level = heading_dict.get("level", 0)
        self.properties = dict(heading_dict.get("properties", {}))
        self.line_start = heading_dict.get("line_start", 0)
        self.line_end = heading_dict.get("line_end", 0)
        self.parent_title = heading_dict.get("parent_title", "")
        self.body_text = heading_dict.get("body_text", "")
        self.tags = list(heading_dict.get("tags", []))
        self.children = [
            HeadingSnapshot(c) for c in heading_dict.get("children", [])
        ]
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "keyword": self.keyword,
            "level": self.level,
            "properties": self.properties,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "parent_title": self.parent_title,
            "tags": self.tags,
            "children_count": len(self.children),
        }


class FileSnapshot:
    """Snapshot of an org file's headings at a point in time."""
    
    def __init__(self, filepath: str, headings: list):
        self.filepath = filepath
        self.headings = [HeadingSnapshot(h) for h in headings]
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def find_heading(self, title: str, partial: bool = True) -> Optional[HeadingSnapshot]:
        """Find a heading by title (recursive)."""
        for h in self.headings:
            if partial and title.lower() in h.title.lower():
                return h
            if title.lower() == h.title.lower():
                return h
            result = self._find_in_children(h.children, title, partial)
            if result:
                return result
        return None
    
    def _find_in_children(self, children: list, title: str, partial: bool) -> Optional[HeadingSnapshot]:
        for h in children:
            if partial and title.lower() in h.title.lower():
                return h
            if title.lower() == h.title.lower():
                return h
            result = self._find_in_children(h.children, title, partial)
            if result:
                return result
        return None
    
    @classmethod
    def from_file(cls, filepath: str) -> "FileSnapshot":
        """Create a snapshot by parsing the org file."""
        try:
            sys.path.insert(0, str(SCRIPTS_DIR))
            from org_query import parse_org
            headings = parse_org(filepath)
            return cls(filepath, headings)
        except Exception as e:
            return cls(filepath, [])  # Empty snapshot on error


# ─── Diff Computation ───────────────────────────────────────────────────────

class OrgChangeDiff:
    """Structured diff between pre and post file snapshots."""
    
    def __init__(self, pre: FileSnapshot, post: FileSnapshot):
        self.pre = pre
        self.post = post
        self.new_headings: list[dict] = []
        self.removed_headings: list[dict] = []
        self.metadata_changes: list[dict] = []
        self.state_transitions: list[dict] = []
        self._compute()
    
    def _compute(self):
        """Compute the diff between pre and post state."""
        pre_titles = set()
        post_titles = set()
        
        # Collect titles recursively
        def collect_titles(headings: list, titles: set, parent: str = ""):
            for h in headings:
                key = f"{h.title}::{h.line_start}"
                titles.add(key)
                collect_titles(h.children, titles, h.title)
        
        collect_titles(self.pre.headings, pre_titles)
        collect_titles(self.post.headings, post_titles)
        
        # New headings
        new_keys = post_titles - pre_titles
        for key in new_keys:
            title, line = key.split("::", 1)
            h = self.post.find_heading(title)
            if h:
                self.new_headings.append({
                    "title": h.title,
                    "keyword": h.keyword,
                    "level": h.level,
                    "properties": h.properties,
                    "line_start": int(line),
                    "parent_title": h.parent_title,
                    "tags": h.tags,
                })
        
        # Removed headings
        removed_keys = pre_titles - post_titles
        for key in removed_keys:
            title, line = key.split("::", 1)
            h = self.pre.find_heading(title)
            if h:
                self.removed_headings.append({
                    "title": h.title,
                    "keyword": h.keyword,
                    "level": h.level,
                    "properties": h.properties,
                })
        
        # Metadata & state changes on existing headings
        common_keys = pre_titles & post_titles
        for key in common_keys:
            title, line = key.split("::", 1)
            pre_h = self.pre.find_heading(title)
            post_h = self.post.find_heading(title)
            if not pre_h or not post_h:
                continue
            
            # State transition
            if pre_h.keyword != post_h.keyword:
                self.state_transitions.append({
                    "title": post_h.title,
                    "from": pre_h.keyword,
                    "to": post_h.keyword,
                    "level": post_h.level,
                    "parent_title": post_h.parent_title,
                })
            
            # Metadata/property changes
            changed_props = {}
            all_props = set(list(pre_h.properties.keys()) + list(post_h.properties.keys()))
            for prop in all_props:
                old_val = pre_h.properties.get(prop)
                new_val = post_h.properties.get(prop)
                if old_val != new_val:
                    changed_props[prop] = {"from": old_val, "to": new_val}
            
            if changed_props:
                self.metadata_changes.append({
                    "title": post_h.title,
                    "keyword": post_h.keyword,
                    "properties": changed_props,
                    "level": post_h.level,
                })
    
    def to_dict(self) -> dict:
        return {
            "filepath": self.pre.filepath,
            "pre_timestamp": self.pre.timestamp,
            "post_timestamp": self.post.timestamp,
            "new_headings": self.new_headings,
            "removed_headings": self.removed_headings,
            "metadata_changes": self.metadata_changes,
            "state_transitions": self.state_transitions,
        }


# ─── Change Classification ──────────────────────────────────────────────────

def classify_change(diff: OrgChangeDiff, operation: str = "") -> dict:
    """
    Classify whether the change merits a gbrain update.
    
    Returns:
        {
            "merits_gbrain": bool,
            "reason": str,
            "classification": "structural" | "routine" | "unknown",
            "relevant_entities": [list of story/epic titles that changed],
        }
    """
    relevant_entities = []
    
    # Check for new EPICs or STORYs (always structural)
    for h in diff.new_headings:
        if h["keyword"] in STRUCTURAL_KEYWORDS:
            relevant_entities.append(h["title"])
    
    if relevant_entities:
        return {
            "merits_gbrain": True,
            "reason": f"New {', '.join(h['keyword'] for h in diff.new_headings if h['keyword'] in STRUCTURAL_KEYWORDS)} created",
            "classification": "structural",
            "relevant_entities": [h["title"] for h in diff.new_headings],
        }
    
    # Check for structural property changes on existing items
    struct_changes = []
    for mc in diff.metadata_changes:
        for prop, change in mc["properties"].items():
            if prop in STRUCTURAL_PROPERTIES:
                struct_changes.append({
                    "title": mc["title"],
                    "property": prop,
                    "from": change["from"],
                    "to": change["to"],
                })
                relevant_entities.append(mc["title"])
    
    if struct_changes:
        return {
            "merits_gbrain": True,
            "reason": f"Structural property changes: {len(struct_changes)} field(s) modified",
            "classification": "structural",
            "relevant_entities": list(set(relevant_entities)),
            "changes": struct_changes,
        }
    
    # Check for new non-inbox headings (TODO under a STORY could be notable)
    new_todos = [h for h in diff.new_headings if h["keyword"] not in ROUTINE_KEYWORDS
                 and h["keyword"] not in STRUCTURAL_KEYWORDS
                 and h["keyword"] != "TODO"]
    if new_todos:
        relevant_entities.extend(h["title"] for h in new_todos)
        return {
            "merits_gbrain": True,
            "reason": f"New non-routine heading(s): {', '.join(h['title'] for h in new_todos)}",
            "classification": "structural",
            "relevant_entities": list(set(relevant_entities)),
        }
    
    # Routine state transitions — skip
    if diff.state_transitions:
        return {
            "merits_gbrain": False,
            "reason": f"Routine state transitions: {len(diff.state_transitions)} item(s) changed state",
            "classification": "routine",
            "relevant_entities": list(set(
                t["title"] for t in diff.state_transitions
            )),
        }

    # New TODOs in inbox or under STORYs — routine (inbox capture, no gbrain value)
    new_todos = [h for h in diff.new_headings if h["keyword"] == "TODO"]
    if new_todos:
        return {
            "merits_gbrain": False,
            "reason": f"New TODO(s) created: {', '.join(h['title'] for h in new_todos)}",
            "classification": "routine",
            "relevant_entities": [h["title"] for h in new_todos],
        }
    
    # Removed headings — debatable, but for now flag as potentially structural
    if diff.removed_headings:
        return {
            "merits_gbrain": True,
            "reason": f"Headings removed: {len(diff.removed_headings)} item(s)",
            "classification": "structural",
            "relevant_entities": [h["title"] for h in diff.removed_headings],
        }
    
    # Default: no significant change
    known_entities = list(set(
        [mc["title"] for mc in diff.metadata_changes] +
        [t["title"] for t in diff.state_transitions]
    ))
    return {
        "merits_gbrain": False,
        "reason": "No structural changes detected",
        "classification": "unknown",
        "relevant_entities": known_entities,
    }


# ─── Audit Logging ──────────────────────────────────────────────────────────

def log_gbrain_update(change_report: dict) -> dict:
    """
    Write an audit entry to the gbrain update log.
    
    Returns {"logged": True, "entry": {...}, "log_file": "..."}
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "script": change_report.get("script_name", "unknown"),
        "operation": change_report.get("operation", "unknown"),
        "filepath": change_report.get("filepath", ""),
        "merits_gbrain": change_report.get("merits_gbrain", False),
        "classification": change_report.get("classification", "unknown"),
        "reason": change_report.get("reason", ""),
        "relevant_entities": change_report.get("relevant_entities", []),
        "new_headings_count": len(change_report.get("new_headings", [])),
        "state_transitions_count": len(change_report.get("state_transitions", [])),
        "metadata_changes_count": len(change_report.get("metadata_changes", [])),
        "gbrain_action_taken": False,  # Set to True after adapter runs
    }
    
    # Append to JSONL log
    GBRAIN_AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(GBRAIN_AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return {"logged": True, "entry": entry, "log_file": str(GBRAIN_AUDIT_LOG)}


def get_recent_logs(limit: int = 20) -> list[dict]:
    """Get the most recent audit log entries."""
    if not GBRAIN_AUDIT_LOG.exists():
        return []
    
    entries = []
    with open(GBRAIN_AUDIT_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return entries[-limit:]


# ─── Main Hook Processor ────────────────────────────────────────────────────

class OrgChangeHook:
    """
    Post-change hook that captures org diffs and classifies them.
    
    Usage:
        hook = OrgChangeHook()
        hook.capture_pre(filepath)
        # ... perform org write ...
        hook.capture_post(filepath)
        report = hook.analyze(script_name="org_query.py", operation="create_todo")
    """
    
    def __init__(self):
        self.pre_snapshots: dict[str, FileSnapshot] = {}
        self.post_snapshots: dict[str, FileSnapshot] = {}
    
    def capture_pre(self, filepath: str) -> FileSnapshot:
        """Capture the state of a file before a write operation."""
        snapshot = FileSnapshot.from_file(filepath)
        self.pre_snapshots[filepath] = snapshot
        return snapshot
    
    def capture_post(self, filepath: str) -> FileSnapshot:
        """Capture the state of a file after a write operation."""
        snapshot = FileSnapshot.from_file(filepath)
        self.post_snapshots[filepath] = snapshot
        return snapshot
    
    def analyze(self, filepath: str, script_name: str = "",
                operation: str = "") -> dict:
        """
        Analyze the diff between pre and post state.
        
        Returns a structured change report:
        {
            "script_name": str,
            "operation": str,
            "filepath": str,
            "merits_gbrain": bool,
            "classification": str,
            "reason": str,
            "relevant_entities": [str],
            "diff": {...},
            "audit": {...},
        }
        """
        pre = self.pre_snapshots.get(filepath)
        post = self.post_snapshots.get(filepath)
        
        if pre is None or post is None:
            return {
                "script_name": script_name,
                "operation": operation,
                "filepath": filepath,
                "merits_gbrain": False,
                "classification": "unknown",
                "reason": "Missing pre or post snapshot",
                "relevant_entities": [],
                "diff": None,
            }
        
        diff = OrgChangeDiff(pre, post)
        classification = classify_change(diff, operation)
        
        report = {
            "script_name": script_name,
            "operation": operation,
            "filepath": filepath,
            **classification,
            "diff": diff.to_dict(),
            "new_headings": diff.new_headings,
            "state_transitions": diff.state_transitions,
            "metadata_changes": diff.metadata_changes,
            "removed_headings": diff.removed_headings,
        }
        
        # Log the change
        audit = log_gbrain_update(report)
        report["audit"] = audit
        
        return report
    
    def process_write(self, script_name: str, operation: str,
                      filepath: str, params: dict = None) -> dict:
        """
        Convenience: capture, execute, analyze.
        
        NOTE: This method captures pre, then returns a partial report.
        The caller must execute the write and call finalize() separately.
        """
        self.capture_pre(filepath)
        return {
            "hook_ready": True,
            "filepath": filepath,
            "pre_captured": True,
            "script_name": script_name,
            "operation": operation,
            "params": params or {},
        }
    
    def finalize(self, context: dict) -> dict:
        """
        Complete the hook cycle: capture post, analyze, return report.
        """
        filepath = context["filepath"]
        self.capture_post(filepath)
        return self.analyze(
            filepath=filepath,
            script_name=context.get("script_name", ""),
            operation=context.get("operation", ""),
        )
    
    def prepare_gbrain_payload(self, report: dict) -> dict:
        """
        Prepare a structured payload for the gbrain update adapter.
        
        This is what gets sent to the Hermes subagent for LLM-driven gbrain updates.
        """
        return {
            "source": "org_change_hook",
            "script": report.get("script_name", ""),
            "operation": report.get("operation", ""),
            "filepath": report.get("filepath", ""),
            "classification": report.get("classification", ""),
            "reason": report.get("reason", ""),
            "new_headings": report.get("new_headings", []),
            "metadata_changes": report.get("metadata_changes", []),
            "state_transitions": report.get("state_transitions", []),
            "removed_headings": report.get("removed_headings", []),
            "relevant_entities": report.get("relevant_entities", []),
            "hook_timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ─── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    """CLI entry point for standalone use."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Post-change hook for org-mode file analysis"
    )
    parser.add_argument("--capture-pre", help="Capture pre-state of file")
    parser.add_argument("--capture-post", help="Capture post-state of file")
    parser.add_argument("--script", help="Script name that triggered the change")
    parser.add_argument("--operation", help="Operation name (create_todo, toggle, etc.)")
    parser.add_argument("--log", action="store_true", help="Show recent audit logs")
    parser.add_argument("--log-limit", type=int, default=20, help="Log entry count")
    
    args = parser.parse_args()
    
    if args.log:
        entries = get_recent_logs(args.log_limit)
        print(json.dumps({"entries": entries, "count": len(entries)}, indent=2))
        return
    
    if args.capture_pre and args.capture_post:
        hook = OrgChangeHook()
        hook.capture_pre(args.capture_pre)
        hook.capture_post(args.capture_post)
        report = hook.analyze(
            filepath=args.capture_post,
            script_name=args.script or "unknown",
            operation=args.operation or "unknown",
        )
        print(json.dumps(report, indent=2, default=str))
        return
    
    if args.capture_pre:
        hook = OrgChangeHook()
        snapshot = hook.capture_pre(args.capture_pre)
        print(json.dumps({
            "status": "pre_captured",
            "filepath": args.capture_pre,
            "headings_count": len(snapshot.headings),
        }, indent=2))
        return
    
    print(json.dumps({"error": "Use --capture-pre and/or --capture-post"}, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()
