---
name: gbrain-frontmatter-guard
description: "Validate and fix YAML frontmatter across gbrain pages. Ensures every page has correct type, title, tags, created date, and valid YAML syntax. System maintenance skill for brain integrity."
version: 1.1.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, maintenance, frontmatter, second-brain]
    related_skills: [second-brain, gbrain-maintain, gbrain-page-writer]
---

# GBrain Frontmatter Guard

Validate and fix YAML frontmatter across gbrain pages. Ensures every page has correct type, title, tags, created date, and valid YAML syntax. This is a system maintenance skill that keeps the brain queryable and structured.

## When to Use

- User says "check frontmatter", "fix page metadata", "validate pages"
- Dream cycle lint flagged frontmatter issues
- You encounter a page with missing or broken frontmatter during normal work
- After bulk ingestion — verify all new pages have valid frontmatter
- During gbrain-maintain session — run as a health check
- Before deploying to Railway — verify all committed pages pass validation

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Choose Scan Target

**Single page scan:**
```
mcp_gbrain_get_page(slug="<page_slug>")
# Validate frontmatter
```

**Batch scan (recent changes):**
```
mcp_gbrain_list_pages(sort="updated_desc", limit=50)
# Validate frontmatter of each page
```

**Batch scan (by type):**
```
mcp_gbrain_list_pages(type="<page_type>", limit=100)
# Validate frontmatter of all pages of a type
```

### Step 3: Validate Frontmatter

Check each page for these frontmatter requirements:

| Field | Required? | Validation | Default If Missing |
|-------|-----------|------------|-------------------|
| `type` | REQUIRED | Must be valid type from schema | Derive from slug prefix |
| `title` | REQUIRED | Non-empty string | Derive from slug |
| `tags` | REQUIRED | Array of strings | `[]` |
| `created` | REQUIRED | Valid ISO date | Use page creation date or today |
| `aliases` | Optional | Array of strings | Omit |
| `source_url` | When applicable | Valid URL | Omit |
| `recorded` | When applicable | Valid ISO date | Omit |
| `media_type` | When applicable | Known type | Omit |
| `attendees` | When applicable | Array of strings | Omit |

### Step 4: Valid Types (from schema.md)

`person`, `company`, `meeting`, `deal`, `project`, `concept`, `idea`, `writing`, `program`, `org`, `civic`, `media`, `personal`, `household`, `hiring`, `prompt`, `source`

### Step 5: Fix Issues

For each issue found, construct the corrected page:

**Missing or invalid type:**
- Derive from slug prefix: `people/` → `person`, `companies/` → `company`, `concepts/` → `concept`, `projects/` → `project`, `media/` → `media`, `meetings/` → `meeting`, `ideas/` → `idea`, `originals/` → `writing`
- If prefix does not map cleanly, use `concept` as safe default

**Missing title:**
- Derive from slug: `people/jane-doe` → `Jane Doe`
- Capitalize first letter of each word, replace hyphens with spaces

**Missing tags:**
- Derive from page type plus slug keywords
- Example: `people/jane-doe` → `[person]` (minimal — do not fabricate tags)
- Better to have minimal correct tags than wrong tags

**Missing created date:**
- Check timeline for earliest entry date
- If no timeline, use the date the page was first discovered/modified
- As last resort, use today's date

### Step 6: Write Fixed Page

```
mcp_gbrain_put_page(slug="<page_slug>", content="<corrected markdown>")
```

IMPORTANT: Preserve ALL existing content. Only modify the frontmatter section. Every other line must remain identical.

### Step 7: Log Repair

```
mcp_gbrain_add_timeline_entry(
    slug="<page_slug>",
    date="YYYY-MM-DD",
    summary="Frontmatter fix: {fields fixed}",
    detail="Fixed: {list of changes}. Original values preserved in page version history."
)
```

### Step 8: Report Results

Report to the user:
- Number of pages scanned
- Number of pages with issues
- Total issues found and fixed, grouped by type:
  - Missing type → fixed
  - Missing title → fixed
  - Missing tags → added default
  - Missing created → derived
  - Invalid YAML → corrected

## Validation Rules

### YAML Syntax
- Frontmatter must start with `---` on line 1
- Frontmatter must end with `---` (separate line)
- No tabs in YAML (use spaces)
- Values with colons must be quoted: `title: "My Title: Subtitle"`
- Tags are lowercase, hyphenated: `[person, investor, ai]`
- **Sources with `[[wikilinks]]` must be single-quoted** — `[[` is a YAML flow sequence indicator. `sources: [[page-a]], [[page-b]]` causes `frontmatter-yaml-parse`. Fix: `sources: '[[page-a]], [[page-b]]'`
- **Values containing double quotes must be single-quoted** — `description: 'Triggers on "find subdomains", "check ssl"'` to avoid `frontmatter-nested-quotes`

### Type-Specific Requirements

| Type | Required Fields | Optional Fields |
|------|----------------|-----------------|
| `person` | type, title, tags, created | aliases |
| `company` | type, title, tags, created | aliases |
| `meeting` | type, title, tags, created, attendees | |
| `media` | type, title, tags, created, media_type | source_url |
| `idea` | type, title, tags, created | source_url |
| `project` | type, title, tags, created | |

### What NOT to Fix

- Custom frontmatter fields not in the schema (they may have specific purposes)
- Tags that seem "wrong" but do not break querying — defer to the author
- Missing aliases — only add if obviously needed for dedup

## Common Pitfalls

- **Over-fixing** — only fix what is broken. Do not restructure valid frontmatter to match personal preferences.
- **Losing content** — always read the FULL page before rewriting. Partial reads lose content.
- **Wrong type inference** — a slug starting with `people/` is probably a person page, but always verify by reading the content before reassigning type.
- **Fabricating metadata** — do not invent tags, dates, or other metadata. Use safe defaults and document them.
- **Breaking valid pages** — if a page loads and displays correctly, the frontmatter may be valid YAML even if it looks unusual to you.

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Scan scope defined (single page, batch by type, recent changes)
- [ ] Each page validated against frontmatter requirements
- [ ] Only broken fields fixed (no cosmetic changes)
- [ ] Full page content preserved during rewrite
- [ ] Timeline entry added for each repair
- [ ] Results reported to user with summary counts
