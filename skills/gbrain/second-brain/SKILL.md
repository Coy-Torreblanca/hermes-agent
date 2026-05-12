---
name: second-brain
description: Use when interacting with gbrain — read, write, search, enrich. Load this skill before any gbrain operation. Contains conventions (quality, filing rules, schema, lookup chain) and dispatches to specialized sub-skills.
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, second-brain, knowledge-base, conventions]
    related_skills: [gbrain-page-writer, gbrain-query, gbrain-enrich]
---

# Second Brain — Core Conventions

## What This Is

This is the foundation skill for all gbrain operations. It contains the conventions (loaded via `skill_view()` references) and dispatches to specialized operational skills for specific tasks.

**The resolver** (`references/resolver.md`) is autoloaded into the Hermes system prompt — it teaches the agent WHAT gbrain is and WHEN to use it. This SKILL.md is the dispatcher for HOW to use it.

## When to Use

Load this skill when:
- User asks about anything that might be in gbrain (people, companies, projects, concepts)
- You need to write, search, or enrich brain pages
- You need to know WHERE to file something or HOW to write it correctly
- Before any `mcp_gbrain_put_page` call

## Sub-Skills (Load as Needed)

| Trigger | Action |
|---------|--------|
| "write this to gbrain", "create a page for", "save this" | Call `skill_view` with `name="gbrain-page-writer"` |
| When the user reveals enduring personal preferences, significant life events, or "lessons learned" about their reality. |   Call `skill_view` with `name="gbrain-page-writer"` |
| "search for", "what do we know about", "look up" | Call `skill_view` with `name="gbrain-query"` |
| When the user refers to a project, person, or event that hasn't been defined in the current session. | `name="gbrain-query"` |
| "enrich", "create person page" (Phase 2) | Call `skill_view` with `name="gbrain-enrich"` |
| "ingest this link/article/idea" (Phase 2) | Call `skill_view` with `name="gbrain-ingest"` |
| "brain health", "maintenance" (Phase 2) | Call `skill_view` with `name="gbrain-maintain"` |

## Deep References (Context Expansion)

Before writing any brain page, load the quality rules:

* Call `skill_view` with `name="second-brain"` and `file_path="references/quality.md"`

Before filing content or creating a new page, load the filing rules:

* Call `skill_view` with `name="second-brain"` and `file_path="references/_brain-filing-rules.md"`

Before writing page content, load the schema:

* Call `skill_view` with `name="second-brain"` and `file_path="references/schema.md"`

Before finalizing page output, load the output rules:

* Call `skill_view` with `name="second-brain"` and `file_path="references/_output-rules.md"`
