---
name: gbrain-query
description: Answer questions using the brain's knowledge with 3-layer search, synthesis, and citation propagation. Use when the user asks a question, wants a lookup, or needs information from the brain.
version: 1.0.0
author: Adapted from gbrain query skill
metadata:
  hermes:
    tags: [gbrain, query, search, knowledge-base]
    related_skills: [second-brain, gbrain-page-writer, gbrain-enrich]
tools:
  - mcp_gbrain_search
  - mcp_gbrain_query
  - mcp_gbrain_get_page
  - mcp_gbrain_list_pages
  - mcp_gbrain_get_backlinks
  - mcp_gbrain_traverse_graph
  - mcp_gbrain_get_timeline
  - mcp_gbrain_get_health
  - mcp_gbrain_get_chunks
mutating: false
---

# Gbrain Query Skill

Answer questions using the brain's knowledge with 3-layer search and synthesis.

## Contract

This skill guarantees:
- Every answer is grounded in brain content (no hallucination)
- Every claim has a citation tracing back to a specific page slug
- Gaps are flagged explicitly ("the brain doesn't have information on X")
- Source precedence is respected (user statements > compiled truth > timeline > external)
- Conflicting sources are noted with both citations

## Phases

1. **Decompose the question** into search strategies:
   - Keyword search for specific names, dates, terms
   - Semantic query for conceptual questions
   - Structured queries (list by type, backlinks) for relational questions
2. **Execute searches (escalation model):**
   - **Keyword first.** Start with `mcp_gbrain_search` for FTS matches. This is the fast path and often sufficient.
   - **Hybrid only when thin.** If keyword results are insufficient (too few hits, low relevance, poor coverage), fall back to `mcp_gbrain_query` for semantic+keyword with expansion.
   - **get_page when slug found.** Once a relevant page slug is identified, use `mcp_gbrain_get_page` for full context.
   - For structural queries: `mcp_gbrain_list_pages` by type or `mcp_gbrain_get_backlinks`.
3. **Read top results.** Review the top 3-5 search results (keyword or hybrid). Load full pages when chunk previews confirm relevance and deeper context is needed.
4. **Synthesize answer** with citations. Every claim traces back to a specific page slug.
5. **Flag gaps.** If the brain doesn't have info, say "the brain doesn't have information on X" rather than hallucinating.

## Anti-Patterns

- Answering from general knowledge when the brain has relevant content
- Hallucinating facts not in the brain
- Silently picking one source when sources conflict
- Loading full pages when search chunks are sufficient
- Ignoring source precedence (user statements are highest authority)

## Output Format

Answers should include:
- Direct response to the question
- Citations: "According to [Source: people/jane-doe, compiled truth]..."
- Gap flags: "The brain doesn't have information on X"
- Conflict notes when sources disagree

## Quality Rules

- Never hallucinate. Only answer from brain content.
- Cite sources: "According to concepts/do-things-that-dont-scale..."
- Flag stale results: if a search result shows [STALE], note that the info may be outdated
- For "who" questions, use `mcp_gbrain_get_backlinks` and typed links to find connections
- For "what happened" questions, use `mcp_gbrain_get_timeline`
- For "what do we know" questions, read compiled_truth directly via `mcp_gbrain_get_page`

## Token-Budget Awareness

Search returns **chunks**, not full pages. Read the excerpts first before deciding
whether to load a full page.

- `mcp_gbrain_search` / `mcp_gbrain_query` return ranked chunks with context snippets.
  These are often enough to answer the question directly.
- Only use `mcp_gbrain_get_page` to load the full page when a chunk confirms the
  page is relevant and you need more context (e.g., compiled truth, timeline).
- Use `mcp_gbrain_get_chunks` to review chunk-level content without pulling the full page.
- **"Tell me about X"** — get the full page (the user wants the complete picture).
- **"Did anyone mention Y?"** — search results are enough (the user wants a yes/no with evidence).

### Source precedence

When multiple sources provide conflicting information, follow this precedence:

1. **User's direct statements** (highest authority — what the user told you directly)
2. **Compiled truth** (the brain's synthesized, cited understanding)
3. **Timeline entries** (raw evidence, reverse-chronological)
4. **External sources** (web search, API enrichment — lowest authority)

When sources conflict, note the contradiction with both citations. Don't silently
pick one.

## Citation in Answers

When referencing brain pages in your answer, propagate inline citations:
- Cite the page: "According to [Source: people/jane-doe, compiled truth]..."
- When brain pages have inline `[Source: ...]` citations, propagate them so
  the user can trace facts to their origin
- When you synthesize across multiple pages, cite all sources

## Graph Traversal

For relationship questions ("who knows who at X?", "connections between A and B",
"who works at Acme?", "who attended the standup?"), use the graph layer instead
of full-text search:

- `mcp_gbrain_traverse_graph` with `slug`, `link_type`, `depth`, and `direction` params
- Available link types: `attended`, `works_at`, `invested_in`, `founded`, `advises`, `mentions`, `source`
- `direction: "in"` answers "who points to X?" (e.g., who works at company X)
- `direction: "out"` answers "what does X point to?" (default)
- `depth` controls multi-hop traversal (default 5, capped at 10)
- `mcp_gbrain_get_backlinks` lists incoming links to a page (simpler alternative for single-hop)

Examples:
- "Who works at Acme?" → `mcp_gbrain_traverse_graph(slug="companies/acme", link_type="works_at", direction="in")`
- "Who attended Demo Day W26?" → `mcp_gbrain_traverse_graph(slug="meetings/demo-day-w26", link_type="attended", direction="out")`
- "What companies has Emily advised?" → `mcp_gbrain_traverse_graph(slug="people/emily", link_type="advises", direction="out")`
- "Who has Alice met (via meetings)?" → `mcp_gbrain_traverse_graph(slug="people/alice", link_type="attended", depth=2)`

Combine with `mcp_gbrain_query` for queries that need BOTH semantic similarity AND
graph structure. Search results are ranked with a small backlink boost so well-
connected entities surface higher.

## Search Quality Awareness

If search results seem off (wrong results, missing known pages, irrelevant hits):
- Run `mcp_gbrain_get_health` to check index health and embedding coverage
- Check embedding coverage — partial embeddings degrade hybrid search
- Compare keyword search (`mcp_gbrain_search`) vs hybrid search (`mcp_gbrain_query`)
  for the same query to isolate whether the issue is embedding-related
- Report search quality issues in the maintain workflow

## Tools Used

- Keyword search (`mcp_gbrain_search`)
- Hybrid search (`mcp_gbrain_query`)
- Read a page (`mcp_gbrain_get_page`)
- List pages with filters (`mcp_gbrain_list_pages`)
- Check backlinks (`mcp_gbrain_get_backlinks`)
- Traverse the link graph (`mcp_gbrain_traverse_graph`)
- View timeline entries (`mcp_gbrain_get_timeline`)
- Brain health check (`mcp_gbrain_get_health`)
- Content chunks (`mcp_gbrain_get_chunks`)
