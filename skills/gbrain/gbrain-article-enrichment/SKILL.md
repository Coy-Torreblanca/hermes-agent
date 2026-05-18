---
name: gbrain-article-enrichment
description: "REFERENCE DOC — This is now a Hermes cron job, not an interactive skill. See /app/hermes_cron/config.yaml job 'gbrain-article-enrichment'. This document describes the workflow used by that cron job."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, enrichment, articles, dream-cycle, cron, reference]
    related_skills: [second-brain, gbrain-maintain, gbrain-query, gbrain-page-writer]
---

# GBrain Article Enrichment — Reference Document

> ⚠️ **This is now a Hermes cron job, not an interactive skill.**
> The workflow below runs automatically as the `gbrain-article-enrichment` cron job,
> defined in `/app/hermes_cron/config.yaml` (schedule: `0 9 * * 0` — Sundays at 9 AM).
> Do NOT load this skill interactively — use the cron job instead.

## What It Does

Periodically enriches article, writing, idea, and media pages in gbrain by:
1. Finding pages with few or no inbound links (orphans, partially connected)
2. Extracting entities from each page (people, companies, concepts, projects)
3. Creating cross-links from the article to existing entity brain pages
4. Creating minimal stub pages for notable entities not yet in gbrain
5. Adding timeline entries to entity pages showing the article reference

## Cron Job Details

| Field | Value |
|-------|-------|
| **Name** | `gbrain-article-enrichment` |
| **Schedule** | `0 9 * * 0` (Sundays at 9 AM) |
| **Location** | `/app/hermes_cron/config.yaml` |
| **Skills loaded** | `second-brain` |
| **Deliver to** | Discord |
| **Rate limit** | 20 articles per run |

## Workflow (for reference)

### Step 1: Find Target Articles

Use `mcp_gbrain_find_orphans(include_pseudo=false)` and filter to article/research types (research-paper, resource, article).

**⚠️ Truncation pitfall:** When the brain has many orphans (800+), the MCP tool's output can exceed 190K chars and get truncated. You'll see only the first ~100 orphans. Work around:

1. Use `mcp_gbrain_list_pages(sort="updated_desc", limit=200)` to get recently-updated pages with their types
2. Cross-reference returned slugs against your truncated orphans list
3. For candidates you can't resolve, use `mcp_gbrain_get_backlinks(slug="<candidate>")` and `mcp_gbrain_get_links(slug="<candidate>")` to determine orphan status on a case-by-case basis
4. Prioritize the most recently updated orphans first (they're the active content)

**Priority:**
1. Pages with 0 inbound backlinks (orphans — highest priority)
2. Pages with 1-2 inbound backlinks but missing bidirectional connections to derived concepts
3. Most recently updated pages first
4. Pages tagged as high-value

### Step 2: Analyze Content

For each article:
- Read full content via `mcp_gbrain_get_page(slug="<slug>")`
- Extract entities: people, companies, organizations, projects, **concepts**, locations
- Also extract **derived concepts** — brain pages that were created *based on* this article (e.g., a LangGraph concept page derived from the OncoAgent paper)
- Only extract entities that are **substantively discussed**, not merely mentioned

### Step 3: Check Existing Links

Before linking, understand the current state:

1. **Check outbound links:** `mcp_gbrain_get_links(slug="<article>")` — what does the article already link to?
2. **Check inbound backlinks:** `mcp_gbrain_get_backlinks(slug="<article>")` — what pages already link here?
3. **Cross-reference:** If a concept page backlinks TO the article (found in step 2), but the article doesn't link FORWARD to that concept, you have a **missing bidirectional link**.

**Key insight:** Research articles often link TO projects (applies_to links) but don't link back TO the concept pages that were *derived from* them. The derived concepts link TO the article, but the article doesn't reciprocate. Fix this.

### Step 4: Resolve and Link

For each extracted entity:
- Check existing pages: `mcp_gbrain_resolve_slugs(partial="<name>")` or `mcp_gbrain_query(query="<name>", limit=5)`
- If page exists → `mcp_gbrain_add_link(from="<article>", to="<entity>", link_type="references")`
- If an existing concept page backlinks TO the article but the article doesn't link to it → add the reciprocal link: `mcp_gbrain_add_link(from="<article>", to="<concept>", link_type="references")`
- If no page exists → evaluate notability. Most external entities (HubSpot, BCG, individual authors) do NOT pass the notability gate — don't create stubs for them.
- **Also scan for unlinked references:** search for pages that mention the article by name but don't have graph links (e.g., a concept like `deferred-icebox-management` referencing "OncoAgent paper" without linking). Connect those too.

### Step 5: Skip Well-Connected

If article already has 5+ outbound links (`mcp_gbrain_get_links`), skip it — already enriched. BUT: still check for missing reciprocal links (step 3 pattern). If missing reciprocals exist, add them even if the article has 5+ total outbound links.

### Step 6: Report

Summary to Discord: articles processed, entities linked, missing reciprocal links fixed, unlinked references connected, entities skipped (notability gate).

## Quality Rules

- **Notability gate** — only create stubs for entities likely referenced again
- **Substantive linking** — only link entities central to the article
- **Timeline on entity pages** — every back-link needs a timeline entry
- **Max 20 per run** — avoids context overflow and resource exhaustion
- **No-op awareness** — skip articles already well-connected (5+ outbound links)

## Relationship to Other Cron Jobs

| Cron Job | Schedule | Covers |
|----------|----------|--------|
| `gbrain-orphans` | Sat 9 AM | Lists orphans for Coy to review (passive) |
| `gbrain-article-enrichment` | Sun 9 AM | **Automatically enriches** orphans by linking entities (active) |

The orphans cron tells Coy what's disconnected. The article enrichment cron **does the work** of connecting them.
