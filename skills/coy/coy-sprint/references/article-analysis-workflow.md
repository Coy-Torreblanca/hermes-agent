# Article Analysis → Icebox Stories + gbrain (absorbed from repeated workflow)

Pattern used May 10, 2026 with OncoAgent paper and HBR Agentic Marketing article.

## When to Use

- Coy sends a URL and asks "what can I learn from this" or "create stories for this"
- Coy wants to save an article "for later surfacing"
- Any research paper, blog post, or strategy article worth capturing

## Branch Decision

After presenting analysis to Coy, **ask which path**:

| Situation | Path | Action |
|-----------|------|--------|
| Coy has bandwidth, concept is actionable soon | **P1: Create Icebox Stories** | Create `** STORY` entries under relevant EPIC in tasks.org |
| Concept is interesting but far off / no bandwidth / "keep for later" | **P2 path (gbrain-only deferral):** Save to gbrain at `concepts/<slug>`, tag `deferred` + `reading-list`, cross-link to projects. No org tasks.

**Discovered May 15, 2026:** Coy explicitly prefers gbrain-only deferral for concepts that are too far out to sprint. His words: "I have too much in org mode currently." The brain handles surfacing via query, anomaly detection, and project review workflow.

For P2, skip Steps 3 (Create Icebox Stories) and 5 (Present summary table with EPICs) — proceed directly to Step 4 with enhanced linking.

## Workflow

### 1. Fetch & Extract

```bash
curl -sL "<url>" | python3 -c "
import sys, re, json
html = sys.stdin.read()
# Try __NEXT_DATA__ first (paywalled sites like HBR)
m = re.search(r'<script id=\"__NEXT_DATA__\".*?>(.*?)</script>', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    # Navigate to find article body...
# Fallback: scrape prose, strip tags
"
```

### 2. Analyze & Map

Extract transferable patterns:
- What technologies/patterns does it describe?
- Which of Coy's projects could benefit? (30ai, Bible site, Hermes, Personal AI)
- What's the mapping? (e.g., "Brand Code" → gbrain)
- What's the priority order?

Present analysis BEFORE creating stories — give Coy a chance to trim/adjust.

### 3. Create Icebox Stories

For each high-value transferable pattern:

1. **Determine parent EPIC** — use org_query.py to find correct EPIC:
   ```
   python3 ~/.hermes/scripts/org_query.py tasks.org --find-epic "Bible"
   ```
2. **Find insertion point** — get exact line and level:
   ```
   python3 ~/.hermes/scripts/org_query.py tasks.org --insert-point "My Holy Bible v1 [ICEBOX]"
   ```
3. Generate UUID via `python3 -c "import uuid; print(str(uuid.uuid4()).upper())"`
4. Build STORY block with full properties + body citing source
5. Use `patch` to insert — anchor on a unique string near the insertion point
6. **Verify parent EPIC** — run org_query.py to confirm correct placement

### 4. Save to gbrain

**P1 path (icebox stories):** Create a page at `concepts/<slug>` with:
- Full article citation (authors, date, source, URL)
- Key concepts extracted
- Application to Coy's projects (the mapping)
- Cross-reference icebox story names
- Tags: `transferable-patterns`, `research-paper` or `strategy-article`
- Link to relevant gbrain project pages via `mcp_gbrain_add_link`

**P2 path (gbrain-only deferral):** Same gbrain page structure PLUS:
- Add tag `deferred` AND tag `reading-list` to the research page via `mcp_gbrain_add_tag`
- Add timeline entry noting the deferral decision and why (Coy's bandwidth, not priority)
- Add `applies_to` links from the article page to EVERY project mentioned. Use `mcp_gbrain_add_link(from=wiki/research/<slug>, to=<project_slug>, link_type="applies_to", context="<how it applies>")`
- **Add bidirectional back-links** — for EVERY `applies_to` link, also add a `references` link from the project page back to the article: `mcp_gbrain_add_link(from=<project_slug>, to=wiki/research/<slug>, link_type="references", context="<context>")`. This ensures project pages mention relevant reading list items.
- **Add timeline entries to connected project pages** — for each project you linked, add a timeline entry: `mcp_gbrain_add_timeline_entry(slug=<project_slug>, date="YYYY-MM-DD", summary="Referenced in <article title>", detail="<one-line context>")`. This surfaces the reading list item when viewing project history.
- **Back-link relevant org-mode TODOs** — search tasks.org for TODOs whose scope overlaps with the article. For each match, patch the TODO body to add a `Reference: concepts/<slug> — <one-line why>` line. This connects reading list items directly to actionable work items.
- Ensure the complementary cross-link between paired articles (OncoAgent ↔ HBR as complements)
- Write a concept page at `concepts/deferred-icebox-management` tracking the deferral pattern (first instance only)
- Save to memory: the deferred items, tags, and surfacing mechanism

### 5. Present Summary & Clean Up

**P1 path (icebox stories):** Present a clean table: story name, points, parent EPIC. Confirm gbrain page is saved and linked.

**P2 path (gbrain-only deferral):** Present:
- Confirm gbrain page is saved with all `applies_to` links
- Confirm `deferred` tag added
- Confirm timeline entry recorded
- **Delete the corresponding `** STORY` entry from inbox.org** — the concept now lives in gbrain only. Coy explicitly prefers this: "I have too much in org mode currently." (May 15, 2026)

## Story Format Template

```
** STORY <Title> :<tags>:
:PROPERTIES:
:ID:       <UUID>
:CREATED:  [YYYY-MM-DD Day HH:MM]
:SPRINT:   backlog
:POINTS:   <Fibonacci>
:VALUE:    <Critical|Essential|High|Medium|Low>
:GOAL:     <Binary definition of done>
:END:
Source: <Article citation>

<Body: context, implementation notes, dependencies>
```

## Reference

Two consecutive uses May 10, 2026:
- OncoAgent: 4 stories, gbrain page at `concepts/oncoagent-multi-agent-rag`
- HBR Agentic Marketing: 4 stories, gbrain page at `concepts/agentic-marketing-organization-hbr`
