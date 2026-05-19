#!/usr/bin/env python3
"""
org_gbrain_adapter.py — Routes org change diffs to gbrain page updates.

Takes a structured change report from org_change_hook.py and determines
which gbrain pages need creating or updating via the gbrain page-writer workflow.

Usage:
    # Generate-only mode: produce the structured prompt for dispatch
    python3 org_gbrain_adapter.py --payload <change_payload.json>
    python3 org_gbrain_adapter.py --from-hook <report.json>

    # Audit mode: review what would happen
    python3 org_gbrain_adapter.py --payload report.json --dry-run

    # Embedded from code:
    from org_gbrain_adapter import GbrainUpdateAdapter
    adapter = GbrainUpdateAdapter()
    decisions = adapter.evaluate(change_report)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(os.path.expanduser("~/.hermes/scripts"))
TASKS_PATH = "/data/syncthing/Sync/org/work/tasks.org"
GBRAIN_AUDIT_LOG = SCRIPTS_DIR / "gbrain_update_log.jsonl"

# ─── Entity-to-GBrain Mapping ───────────────────────────────────────────────

# Maps org EPIC titles to gbrain page slugs
# New EPICs/stories that match these patterns get routed to existing pages
DEFAULT_EPIC_MAP = {
    "personal ai": "projects/personalai",
    "personal ai v1": "projects/personalai",
    "personal ai v2": "projects/personalai",
    "30ai": "projects/30ai",
    "second brain": "projects/personalai/second-brain",
    "sprint intelligence": "concepts/sprint-intelligence",
}

# Types of org entities that route to concepts/ pages
CONCEPT_PATTERNS = [
    "compliance", "architecture", "pipeline", "standard",
    "workflow", "protocol", "system", "infrastructure",
]


def resolve_gbrain_slug(title: str, properties: dict) -> str:
    """
    Resolve an org heading to a gbrain page slug.
    
    Returns the best-guess slug based on:
    1. Known EPIC-to-slug mappings
    2. Pattern matching (concept patterns → concepts/, story patterns → projects/)
    3. Generic fallback
    """
    title_lower = title.lower().strip()
    keyword = properties.get("keyword", "").upper() if isinstance(properties, dict) else ""
    
    # Check known EPIC mappings first
    for key, slug in DEFAULT_EPIC_MAP.items():
        if key in title_lower:
            return slug
    
    # EPIC → projects/
    if keyword == "EPIC":
        slug = title_lower.replace(" ", "-").replace("[", "").replace("]", "")
        return f"projects/{slug}"
    
    # Concept patterns → concepts/
    for pattern in CONCEPT_PATTERNS:
        if pattern in title_lower:
            slug = title_lower.replace(" ", "-")
            return f"concepts/{slug}"
    
    # Default: try projects/ namespace for stories
    slug = title_lower.replace(" ", "-").replace("[", "").replace("]", "")
    return f"projects/{slug}"


def estimate_page_type(title: str, keyword: str) -> str:
    """Estimate the type field for a new gbrain page."""
    if keyword.upper() == "EPIC":
        return "project"
    if keyword.upper().startswith("STORY"):
        return "concept" if any(p in title.lower() for p in CONCEPT_PATTERNS) else "concept"
    return "concept"


def build_subagent_prompt(change_payload: dict) -> str:
    """
    Build a structured prompt ready for a Hermes subagent equipped with
    gbrain page-writer context.
    
    The subagent should:
    1. Look up existing gbrain pages for each affected entity
    2. Create or update pages based on the change
    3. Add timeline entries
    4. Create back-links
    """
    operation = change_payload.get("operation", "unknown")
    script = change_payload.get("script") or change_payload.get("script_name", "unknown")
    filepath = change_payload.get("filepath", "")
    classification = change_payload.get("classification", "unknown")
    reason = change_payload.get("reason", "")
    
    prompt_parts = [
        "# LLM-Driven GBrain Update",
        "",
        f"A {classification} change was detected in the org file and needs gbrain attention.",
        "",
        "## Source Information",
        f"- **Script:** {script}",
        f"- **Operation:** {operation}",
        f"- **File:** {filepath}",
        f"- **Classification:** {classification}",
        f"- **Reason:** {reason}",
        "",
    ]
    
    # New headings
    new_headings = change_payload.get("new_headings", [])
    if new_headings:
        prompt_parts.extend([
            "## New Headings Created",
            "",
            "Each of these may need a new gbrain page or an update to the parent's page:",
        ])
        for h in new_headings:
            props = h.get("properties", {})
            slug = resolve_gbrain_slug(h["title"], h)
            page_type = estimate_page_type(h["title"], h.get("keyword", ""))
            prompt_parts.append(f"")
            prompt_parts.append(f"### {h['title']}")
            prompt_parts.append(f"- **Keyword:** {h.get('keyword', '')}")
            prompt_parts.append(f"- **Level:** {h.get('level', '')}")
            prompt_parts.append(f"- **Parent:** {h.get('parent_title', '(top-level)')}")
            prompt_parts.append(f"- **ID:** `{props.get('ID', '(auto)')}`")
            prompt_parts.append(f"- **GOAL:** {props.get('GOAL', '(not set)')}")
            prompt_parts.append(f"- **VALUE:** {props.get('VALUE', '(not set)')}")
            prompt_parts.append(f"- **POINTS:** {props.get('POINTS', '(not set)')}")
            prompt_parts.append(f"- **SPRINT:** {props.get('SPRINT', 'backlog')}")
            prompt_parts.append(f"- **Suggested slug:** `{slug}`")
            prompt_parts.append(f"- **Suggested type:** `{page_type}`")
    
    # Metadata changes
    metadata_changes = change_payload.get("metadata_changes", [])
    if metadata_changes:
        prompt_parts.extend([
            "",
            "## Metadata Changes",
            "",
            "These items had their properties modified and may need gbrain updates:",
        ])
        for mc in metadata_changes:
            props = mc.get("properties", {})
            prompt_parts.append(f"")
            prompt_parts.append(f"### {mc['title']}")
            for prop, change in props.items():
                prompt_parts.append(f"- **{prop}:** `{change.get('from', '(none)')}` → `{change.get('to', '(none)')}`")
    
    # State transitions
    transitions = change_payload.get("state_transitions", [])
    if transitions:
        prompt_parts.extend([
            "",
            "## State Transitions (Routine — Skip)",
            "",
            "These are routine state changes and do not merit gbrain updates:",
        ])
        for t in transitions:
            if t.get("from") != t.get("to"):
                prompt_parts.append(f"- {t['title']}: `{t.get('from', '?')}` → `{t.get('to', '?')}`")
    
    # Removed headings
    removed = change_payload.get("removed_headings", [])
    if removed:
        prompt_parts.extend([
            "",
            "## Headings Removed",
            "",
            "These items were removed and may need gbrain updates:",
        ])
        for h in removed:
            prompt_parts.append(f"- {h['title']} ({h.get('keyword', '')})")
    
    prompt_parts.extend([
        "",
        "## Instructions",
        "",
        "For each entity above that merits a gbrain update:",
        "",
        "1. **Search gbrain first** — use `mcp_gbrain_search()` or `mcp_gbrain_resolve_slugs()`",
        "   to check if the page already exists. Do NOT create duplicates.",
        "2. **If page exists:** update the compiled truth with the new information.",
        "   Add a timeline entry for this change.",
        "3. **If page doesn't exist:** create a new page following the gbrain page-writer",
        "   conventions (frontmatter, two-layer model, citations, back-links).",
        "4. **Link to parent entity** — if this is a child of an existing EPIC/project",
        "   with a gbrain page, add a back-link from the parent.",
        "5. **Citation format:** `[Source: org change hook, {script}/{operation}, {date}]`",
        "6. **Return a summary** of what pages were created/updated and why.",
        "",
        f"**Change timestamp:** {datetime.now(timezone.utc).isoformat()}",
    ])
    
    return "\n".join(prompt_parts)


class GbrainUpdateAdapter:
    """
    Adapter that evaluates org change reports and determines gbrain actions.
    
    This adapter does NOT execute the gbrain writes — it generates structured
    prompts that the calling code (a Hermes subagent or cron job) should execute.
    """
    
    def __init__(self):
        self.log_path = GBRAIN_AUDIT_LOG
    
    def evaluate(self, change_report: dict) -> dict:
        """
        Evaluate a change report and determine what gbrain actions to take.
        
        Returns:
        {
            "merits_gbrain": bool,
            "subagent_prompt": str (or None if no action needed),
            "decisions": [
                {
                    "entity": str,
                    "action": "create_page" | "update_page" | "skip" | "search_first",
                    "suggested_slug": str,
                    "page_type": str,
                    "reason": str,
                }
            ],
            "audit": {...},
        }
        """
        merits = change_report.get("merits_gbrain", False)
        
        if not merits:
            return {
                "merits_gbrain": False,
                "subagent_prompt": None,
                "decisions": [],
                "decision_count": 0,
                "reason": change_report.get("reason", "No gbrain update needed"),
            }
        
        decisions = []
        
        # Analyze new headings
        for h in change_report.get("new_headings", []):
            slug = resolve_gbrain_slug(h["title"], h)
            page_type = estimate_page_type(h["title"], h.get("keyword", ""))
            decisions.append({
                "entity": h["title"],
                "action": "search_first",
                "suggested_slug": slug,
                "page_type": page_type,
                "keyword": h.get("keyword", ""),
                "level": h.get("level", 0),
                "parent": h.get("parent_title", "(top-level)"),
                "properties": h.get("properties", {}),
                "reason": f"New {h.get('keyword', 'item')} created",
            })
        
        # Analyze metadata changes
        for mc in change_report.get("metadata_changes", []):
            slug = resolve_gbrain_slug(mc["title"], mc)
            decisions.append({
                "entity": mc["title"],
                "action": "update_page",
                "suggested_slug": slug,
                "page_type": "concept",
                "keyword": mc.get("keyword", ""),
                "properties_changed": mc.get("properties", {}),
                "reason": f"Structural property changes on {mc['title']}",
            })
        
        # Analyze removed headings
        for h in change_report.get("removed_headings", []):
            slug = resolve_gbrain_slug(h["title"], h)
            decisions.append({
                "entity": h["title"],
                "action": "update_page",
                "suggested_slug": slug,
                "page_type": "concept",
                "keyword": h.get("keyword", ""),
                "reason": f"Item removed: {h['title']}",
            })
        
        subagent_prompt = build_subagent_prompt(change_report)
        
        result = {
            "merits_gbrain": True,
            "subagent_prompt": subagent_prompt,
            "decisions": decisions,
            "decision_count": len(decisions),
        }
        
        return result


def load_report(report_path_or_dict) -> dict:
    """Load a change report from a file path or dict."""
    if isinstance(report_path_or_dict, dict):
        return report_path_or_dict
    with open(report_path_or_dict, "r") as f:
        return json.load(f)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Route org change diffs to gbrain page updates"
    )
    parser.add_argument("--payload", help="Path to JSON change report file")
    parser.add_argument("--from-hook", help="Path to hook report JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show decisions without generating final prompt")
    parser.add_argument("--print-prompt", action="store_true",
                        help="Print the subagent prompt")
    
    args = parser.parse_args()
    
    if not args.payload and not args.from_hook:
        print(json.dumps({"error": "Provide --payload or --from-hook"}, indent=2))
        sys.exit(1)
    
    payload_path = args.payload or args.from_hook
    report = load_report(payload_path)
    
    adapter = GbrainUpdateAdapter()
    result = adapter.evaluate(report)
    
    if args.dry_run:
        print(json.dumps({
            "merits_gbrain": result["merits_gbrain"],
            "decision_count": result.get("decision_count", 0),
            "decisions": [
                {
                    "entity": d["entity"],
                    "action": d["action"],
                    "suggested_slug": d["suggested_slug"],
                    "reason": d["reason"],
                }
                for d in result.get("decisions", [])
            ],
        }, indent=2))
        return
    
    if args.print_prompt and result.get("subagent_prompt"):
        print(result["subagent_prompt"])
        return
    
    print(json.dumps({
        "merits_gbrain": result["merits_gbrain"],
        "decision_count": result.get("decision_count", 0),
        "subagent_prompt_len": len(result.get("subagent_prompt", "") or ""),
        "decisions": result.get("decisions", []),
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
