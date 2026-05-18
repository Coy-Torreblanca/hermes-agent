---
name: gbrain-page-writer
description: "Use when writing or updating any page in gbrain — people, companies, projects, concepts, meetings, ideas. Loads quality/filing/schema conventions via read_file before every write. Handles dedup, frontmatter, two-layer structure, citations, and back-links."
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
- **You discover canonical config data, schema values, design decisions, or compliance rules that skill files currently inline** — gbrain pages are the source of truth. Write the data to gbrain, then update the skill file to reference the gbrain slug. Do NOT leave config data duplicated in skill files. Discovered May 15, 2026: Emacs VALUE_ALL values, hierarchy rules, and orthogonality conventions were inlined in SKILL.md instead of stored in gbrain.

## Workflow

Follow these steps in exact order when writing ANY brain page:

### Step 1: Load Conventions

Call `read_file` with each convention reference:
- `read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md`
- `read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md`
- `read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md`
- `read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md`

No need to `wait` — `read_file` is synchronous. All conventions are loaded before the next step.

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

For article/research pages that relate to existing concepts or projects, also use **`applies_to`** links:
`mcp_gbrain_add_link(from="<article_page>", to="<concept_or_project_slug>", link_type="applies_to", context="<how it applies>")`

**Bidirectional linking is preferred** — when you add an `applies_to` link from an article to a project, ALSO add a `references` link from the project back to the article:
`mcp_gbrain_add_link(from="<project_slug>", to="<article_slug>", link_type="references", context="<context>")`
And add a timeline entry to the connected project page:
`mcp_gbrain_add_timeline_entry(slug="<project_slug>", date="YYYY-MM-DD", summary="Referenced in <article title>", detail="<one-line context>")`

Back-linking is mandatory — see `second-brain/references/quality.md`.

### Step 9: Preserve Raw Source (Optional)

If the page was created from an uploaded document, message file, or raw source artifact, preserve the original for provenance:

`mcp_gbrain_file_upload(path="<file_path>", page_slug="<this_slug>")`

**🚨 File upload path restriction:** `mcp_gbrain_file_upload` only accepts paths within the Hermes working directory (typically data repos, not `/tmp/` or cache dirs). If you saved a user's uploaded document to `/data/.hermes/cache/documents/`, that path will be rejected. **Fix:** Copy the file to a valid path under the working directory first (e.g. `/data/syncthing/Sync/org/` or repo root), then upload from there. Discovered 2026-05-16: tried to upload from `/data/.hermes/cache/documents/` and received `invalid_params` — upload path must be within the working directory.

## Common Pitfalls

- **Skipping the dedup check** → creates duplicate pages for the same entity
- **No frontmatter** → page is unqueryable. Always include type, title, tags.
- **Missing citations** → facts are untraceable. Every claim needs [Source: ...].
- **Writing above the line without updating timeline** → evidence lost
- **Paraphrasing the user's words** → preserve exact phrasing. The language IS the insight.
- **No back-links** → broken graph. Every entity mention must link back.
- **Inlining config data in skill files instead of gbrain** — when a user correction involves config values, schema values, or design decisions (e.g., "VALUE values should be X", "priority and VALUE are orthogonal"), the canonical data goes into a gbrain page. Skill and reference files point to gbrain slugs. Do NOT update the skill file with the values directly — update gbrain, then point from the skill. Discovered May 15, 2026.
- **Future-possible projects go to gbrain, not org** — When the user decides not to commit to an idea but wants to keep it for later: (1) remove from tasks.org, (2) create a gbrain `concepts/` page with `status: future-possible`, (3) cross-link to source research/writing pages, (4) add timeline entry noting it's deferred. These pages surface during sprint planning via gbrain query + project-review-workflow.

## Verification Checklist

- [ ] Conventions loaded via read_file before writing
- [ ] Dedup check performed (search + resolve_slugs)
- [ ] Slug follows filing rules (primary subject → directory)
- [ ] Frontmatter present (type, title, tags, created)
- [ ] Two-layer structure (compiled truth + timeline)
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added if event-driven
