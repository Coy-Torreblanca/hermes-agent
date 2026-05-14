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

Use `mcp_gbrain_find_orphans(include_pseudo=false)` and filter to types: writing, idea, media, originals.

**Priority:**
1. Pages with 0 back-links (orphans — highest priority)
2. Pages with 1-2 back-links (partially connected)
3. Most recently updated pages
4. Pages tagged as high-value

### Step 2: Analyze Content

For each article:
- Read full content via `mcp_gbrain_get_page(slug="<slug>")`
- Extract entities: people, companies, organizations, projects, concepts, locations
- Only extract entities that are **substantively discussed**, not merely mentioned

### Step 3: Resolve and Link

For each extracted entity:
- Check existing pages: `mcp_gbrain_resolve_slugs(partial="<name>")`
- If page exists → `mcp_gbrain_add_link(from="<article>", to="<entity>", link_type="references")`
- Also add timeline entry: `mcp_gbrain_add_timeline_entry(slug="<entity>", summary="Referenced in <article>")`
- If no page exists → evaluate notability. Create stub only if likely to be referenced again.

### Step 4: Skip Well-Connected

If article already has 5+ outbound links (`mcp_gbrain_get_links`), skip it — already enriched.

### Step 5: Report

Summary to Discord: articles processed, entities linked, stubs created, entities skipped.

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
