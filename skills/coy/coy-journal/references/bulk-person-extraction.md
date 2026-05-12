# Bulk Person Extraction from Journal Timelines

When Coy asks to "create gbrain pages for every person mentioned in the past N days" — this is the workflow.

## 1. List all journal pages in range

```
mcp_gbrain_list_pages(type="journal", limit=30)
```

Journal pages use slug `journal/YYYY-MM-DD`. The list_pages call returns only existing pages — if a date range has gaps, those days simply don't have journal entries.

## 2. Pull all journal timelines in parallel

One `mcp_gbrain_get_timeline(slug="journal/YYYY-MM-DD")` call per day. Do ALL of them in a single parallel batch — timeline reads don't trigger rate limits the way writes do.

## 3. Extract unique person names

Scan every timeline entry's `summary` and `detail` fields. People appear as:
- Explicit names: "Melody", "Javier", "Sabrina"
- Relationship tags: "Coy's dad", "Melody's brother"
- Context clues: "boss", "the waiter", "Tanya's parents"

Build a set of unique person slugs (`people/<name>`). Normalize names: lowercase, hyphens for spaces.

## 4. Cross-reference against existing pages

Batch `mcp_gbrain_get_page(slug="people/<name>")` calls for every candidate. Do this in groups of ~8 to avoid rate limits. A `page_not_found` error means the page doesn't exist and needs creation. A successful result means the page already exists — skip it.

Common existing pages to skip: `coy-diego`, `people/melody-torreblanca`, `people/javier-torreblanca`, `people/sebastian-torreblanca`, `people/seph-torreblanca`, `people/mellyn-gilmore`, `mtg/players/*`.

## 5. Batch-create missing pages

Use `mcp_gbrain_put_page(slug, content)` — it's an upsert, safe to call even if the page already exists. Create pages in groups of **6-8** to avoid gbrain MCP rate limits. Wait for each batch to complete before firing the next.

### Page content template

```yaml
---
type: person
tags: [family|work|church|friend, optional-subcategory]
---

# Display Name

One-line description. Relationship to Coy.

## Context Date Range
- Key events and interactions extracted from timeline entries
- Include date references

## Related
- [[people/related-person|Related Person]]
```

### Slug conventions
- Family: `people/<firstname>` (Sabrina, Diego, Christina, Lily, Tanya)
- Work: `people/<firstname>` (Prem, Ganesh, Joe) — boss gets full name: `people/shawn-white`
- Church: `people/<firstname>-ctk` for CTK, `people/<firstname>-good-shepherd` for Good Shepherd
- Friends: `people/<firstname>-<context>` for disambiguation (e.g., `people/sean-ralph`, `people/david-sebastian-friend`)

## 6. Known name corrections

- **Shawn White** (boss) — NOT "Sean" (corrected May 12, 2026)
- **Finley "Fif"** — MTG player, NOT "Did"

## Pitfalls

- **gbrain MCP rate limiting on writes:** The server becomes unreachable after ~5 rapid failures. Keep batches to 6-8 parallel calls. If it goes down, wait ~60 seconds.
- **Maria Elena vs Mariaelena:** These may be the same person or different. Mariaelena is Tanya's mother (Alfonso's wife). Maria Elena was met at Sebastian's house. Create separate pages with a "verify" note until confirmed.
- **"Did" is actually "Fif" (Finley):** A previous journal correction established this. Don't recreate the error.
- **Don't over-segregate minor mentions:** One-off mentions (Sienna, Citlali, Arianna) can be noted on the primary person's page (Sean Ralph, Miguel) rather than getting standalone pages. Use judgment — Coy said "every person" but 2-sentence stubs for children of friends are low-value.
