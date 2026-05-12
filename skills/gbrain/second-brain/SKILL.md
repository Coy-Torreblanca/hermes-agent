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

## When to Use

Load this skill when:
- User asks about anything that might be in gbrain (people, companies, projects, concepts)
- You need to write, search, or enrich brain pages
- You need to know WHERE to file something or HOW to write it correctly
- Before any `mcp_gbrain_put_page` call

## Sub-Skills (Load as Needed)

| Trigger | Skill |
|---------|-------|
| "write this to gbrain", "create a page for", "save this" | `gbrain-page-writer` |
| "search for", "what do we know about", "look up" | `gbrain-query` |
| "enrich", "create person page", "update company page" | `gbrain-enrich` |
| "ingest this link/article/idea" | `gbrain-ingest` |
| "brain health", "check citations", "maintenance" | `gbrain-maintain` |

## Deep References (Context Expansion)

Before writing any brain page, load the quality rules:

* Call `skill_view` with `name="second-brain"` and `file_path="references/quality.md"`

Before filing content or creating a new page, load the filing rules:

* Call `skill_view` with `name="second-brain"` and `file_path="references/_brain-filing-rules.md"`

Before writing page content, load the schema:

* Call `skill_view` with `name="second-brain"` and `file_path="references/schema.md"`
