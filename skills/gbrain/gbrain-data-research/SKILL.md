---
name: gbrain-data-research
description: "Extract structured information from unstructured sources: emails, documents, chat logs, and web content. Parses entities, relationships, dates, and key facts, then writes structured pages to gbrain."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, research, extraction, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, gbrain-ingest]
---

# GBrain Data Research

Extract structured information from unstructured sources: emails, documents, chat logs, and web content. Parses entities, relationships, dates, and key facts, then writes structured pages to gbrain.

## When to Use

- User says "extract the key info from this email", "research this document"
- User provides a long document or message and wants structured notes
- User asks "what is in that file?" — extract key facts first
- Email hook or document pipeline delivers content for structured extraction
- During ingestion pipeline — if content is too large or complex for gbrain-ingest

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/repo-architecture.md
```

### Step 2: Read Source

Read the source content:

```
# For files
read_file(path="<file_path>")

# For emails (via himalaya skill)
skill_view(name="himalaya")
```

### Step 3: Identify Extraction Targets

Decide what to extract based on source type:

| Source Type | Extraction Targets |
|-------------|-------------------|
| Email | Sender, date, subject, key requests, decisions, action items, attached entities |
| Document/PDF | Title, author, date, key arguments, data points, named entities |
| Chat log | Participants, decisions, action items, timestamped events |
| Web content | Source URL, publication date, key claims, author, entities |
| Mixed/long text | People mentioned, companies, dates, decisions, action items |

### Step 4: Extract Structured Data

For each entity/piece of data found:

1. **Entity check:** Does this person/company/concept already have a brain page?
   ```
   mcp_gbrain_resolve_slugs(partial="<entity_name>")
   mcp_gbrain_search(query="<entity_name>")
   ```

2. **Relation extraction:** What relationships exist between entities?
   - Person A mentions Person B → potential relationship
   - Company X acquired Company Y → business event
   - Person A works at Company Z → employment fact

3. **Timeline extraction:** Extract time-bound facts
   - Events with dates
   - Decisions made at specific times
   - Duration-based activities

### Step 5: Write Updates to Existing Pages

For each entity with an existing brain page:
- Update compiled truth if new information is found
- Add timeline entry for the new data point
- Add back-links from the source to the entity

```
mcp_gbrain_get_page(slug="<entity_slug>")
# Determine what to add
mcp_gbrain_put_page(slug="<entity_slug>", content="<updated content>")
mcp_gbrain_add_timeline_entry(slug="<entity_slug>", date="YYYY-MM-DD", summary="...", detail="...")
```

### Step 6: Create New Pages (if Needed)

If extraction reveals new notable entities, follow gbrain-page-writer workflow:

```
skill_view(name="gbrain-page-writer")
# Follow 8-step write workflow
```

### Step 7: Link Related Entities

For all entities found in the source:

```
mcp_gbrain_add_link(from="<entity_A>", to="<entity_B>", link_type="<relationship>")
```

Common link types: `works_at`, `invested_in`, `partner_of`, `acquired`, `references`, `collaborates_with`

### Step 8: Report Findings

Report to the user:
- Source analyzed
- Entities found (existing + new)
- Relationships extracted
- Timeline events added
- Recommended follow-ups

## Relationship Link Types

| Link Type | Direction | Example |
|-----------|-----------|---------|
| `works_at` | person → company | `people/jane-doe → companies/acme-corp` |
| `references` | bidirectional | Any entity mentions another |
| `partner_of` | bidirectional | `companies/acme → companies/beta-inc` |
| `invested_in` | person/company → company | `people/john-investor → companies/startup-x` |
| `acquired` | company → company | `companies/big-co → companies/small-startup` |
| `collaborates_with` | bidirectional | `people/ada → people/bob` |
| `attended` | person → meeting | `people/jane-doe → meetings/2026-05-13-sprint` |

## Common Pitfalls

- **Over-extraction** — not every name mentioned needs a brain page. Apply the notability gate.
- **Wrong link types** — verify the nature of a relationship before creating links. Guessing creates noise.
- **Missing context** — extract the context around a fact, not just the fact itself. Context is what makes it retrievable.
- **Duplicate entities** — always dedup before creating new pages. Check aliases.
- **Stale extraction** — dates matter. A fact from a 2023 document may not be current in 2026.

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Source content fully read and analyzed
- [ ] Extraction targets identified by source type
- [ ] Entities checked against existing brain pages
- [ ] Existing pages updated with new timeline entries
- [ ] New pages created only for notable entities (notability gate passed)
- [ ] Relationships linked with correct types
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Findings reported to user with recommended follow-ups
