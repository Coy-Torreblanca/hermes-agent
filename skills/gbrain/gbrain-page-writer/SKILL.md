---
name: gbrain-page-writer
description: Use when writing or updating any page in gbrain — people, companies, projects, concepts, meetings, ideas. Loads quality/filing/schema conventions via skill_view() before every write. Handles dedup, frontmatter, two-layer structure, citations, and back-links.
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, page-writing, second-brain, crud]
    related_skills: [second-brain, gbrain-query]
---

# GBrain Page Writer

Dedicated skill for creating and updating gbrain pages. Every `mcp_gbrain_put_page` call MUST go through this skill's workflow.

## When to Use

- User says "write this to gbrain", "save this", "create a page for..."
- You've collected information and need to persist it to the second brain
- User corrected you about a person/company/fact — write immediately
- Any operational skill (enrich, ingest, signal-detector) needs to write a page

## Workflow

Follow these steps in exact order when writing ANY brain page:

### Step 1: Load Conventions

Call `skill_view` with `name="second-brain"` and `file_path="references/quality.md"`.
Call `skill_view` with `name="second-brain"` and `file_path="references/_brain-filing-rules.md"`.
Call `skill_view` with `name="second-brain"` and `file_path="references/schema.md"`.
Call `skill_view` with `name="second-brain"` and `file_path="references/_output-rules.md"`.

Wait for all conventions to load before proceeding.

### Step 2: Determine Slug

Follow the decision protocol from _brain-filing-rules.md:
1. Identify the PRIMARY SUBJECT (a person? company? concept? project?)
2. Determine the directory: people/, companies/, projects/, concepts/, etc.
3. Form the slug: `directory/slug-name` (NO .md extension for gbrain slugs)
   - Follow the decision protocol from _brain-filing-rules.md (loaded in Step 1) for the complete directory listing (people/, companies/, concepts/, originals/, meetings/, media/, sources/, civic/, etc.)

### Step 3: Dedup Check

Before creating a new page, search gbrain for existing pages:
- `mcp_gbrain_search(query="<name>")` — keyword search
- `mcp_gbrain_resolve_slugs(partial="<name>")` — fuzzy slug match
- If found → UPDATE the existing page. Do NOT create a duplicate.
- If not found → CREATE a new page.

### Step 4: Build Page Content

Every page follows the two-layer model from schema.md:

**Above the line (compiled truth):**
- YAML frontmatter: type, title, tags, created
- Executive summary: one paragraph, what you need to know
- Structured state fields (role, company, status, etc.)
- Open threads (active items — remove when resolved)
- See Also (cross-links)

**Below the line (timeline):**
- `---` separator
- `## Timeline`
- Reverse-chronological entries: `- **YYYY-MM-DD** | Source — What happened.`

### Step 5: Add Citations

Every fact gets `[Source: ...]` inline:
- User statements: `[Source: User, context, YYYY-MM-DD]`
- Observations: `[Source: observed, YYYY-MM-DD]`
- Synthesis: `[Source: compiled from ...]`

### Step 6: Write Page

`mcp_gbrain_put_page(slug="<slug>", content="<full markdown with frontmatter>")`

### Step 7: Add Timeline Entry

If this write was triggered by an event (conversation, decision, observation):
`mcp_gbrain_add_timeline_entry(slug="<slug>", date="YYYY-MM-DD", summary="<one-line>", detail="<context>")`

### Step 8: Create Back-Links

For every person/company mentioned in the page that has a brain page:
`mcp_gbrain_add_link(from="<this_page>", to="<entity_page>", link_type="references")`

Back-linking is mandatory — see `second-brain/references/quality.md`.

## Common Pitfalls

- **Skipping the dedup check** → creates duplicate pages for the same entity
- **No frontmatter** → page is unqueryable. Always include type, title, tags.
- **Missing citations** → facts are untraceable. Every claim needs [Source: ...].
- **Writing above the line without updating timeline** → evidence lost
- **Paraphrasing the user's words** → preserve exact phrasing. The language IS the insight.
- **No back-links** → broken graph. Every entity mention must link back.

## Verification Checklist

- [ ] Conventions loaded via skill_view() before writing
- [ ] Dedup check performed (search + resolve_slugs)
- [ ] Slug follows filing rules (primary subject → directory)
- [ ] Frontmatter present (type, title, tags, created)
- [ ] Two-layer structure (compiled truth + timeline)
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added if event-driven
