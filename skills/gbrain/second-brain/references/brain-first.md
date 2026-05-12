# Brain-First Lookup Convention

**Read this before doing ANY entity/person/company/fact lookup.**

Sub-agents and fresh sessions inherit MCP gbrain tools but not the knowledge of
when and how to use them. This file is that knowledge.

## Available MCP GBrain Tools

Your tool inventory includes these (all prefixed `mcp_gbrain_`):

| Tool | Use for |
|------|---------|
| `mcp_gbrain_search` | Keyword search — fast, always works |
| `mcp_gbrain_query` | Hybrid search (keyword + semantic) — best quality |
| `mcp_gbrain_get_page` | Direct page read when you know the slug |
| `mcp_gbrain_get_links` | Outgoing links from a page |
| `mcp_gbrain_get_backlinks` | Who references this entity |
| `mcp_gbrain_get_timeline` | Dated events for an entity |
| `mcp_gbrain_resolve_slugs` | Fuzzy slug resolution |
| `mcp_gbrain_traverse_graph` | Walk the relationship graph |
| `mcp_gbrain_put_page` | Create or update a brain page |
| `mcp_gbrain_add_timeline_entry` | Add a dated event |
| `mcp_gbrain_add_link` | Add a relationship edge |

All tools are accessed via MCP with the `mcp_gbrain_` prefix.

## The Lookup Chain (MANDATORY ORDER)

1. **`mcp_gbrain_search`** first — keyword search, fast, zero API cost
2. **`mcp_gbrain_query`** if search is thin — hybrid semantic search, uses embedding API
3. **`mcp_gbrain_get_page`** if you found a slug — read the full compiled truth
4. **External APIs only after steps 1-2 return nothing useful**

Never skip to external APIs without completing steps 1-2. The brain has
thousands of pages. The answer is almost always there.

## Rules

- **Score > 0.5 = use it.** Don't reach for external APIs when the brain answered.
- **User's direct statements are highest-authority data.** The brain captures
  what the user said in meetings, conversations, and notes. External sources
  are supplementary.
- **Every brain page reference in output** should use a clickable link format
  appropriate to the deployment (GitHub URL, local path, or slug).

## Entity Page Conventions

Standard directory structure:

| Directory | Type | Example |
|-----------|------|---------|
| `people/` | person | `people/paul-graham.md` |
| `companies/` | company | `companies/stripe.md` |
| `deals/` | deal | `deals/stripe-series-c.md` |
| `meetings/` | meeting | `meetings/2026-04-23-weekly-sync.md` |
| `projects/` | project | `projects/gbrain.md` |
| `yc/` | yc | `yc/batch-w26.md` |

When creating new pages, include proper frontmatter with `type`, `title`,
and `tags` fields.

## When Spawning Further Sub-agents

If you spawn your own sub-agents, include this line in their task prompt:

> Read `skills/gbrain/second-brain/references/brain-first.md` before starting work.

This ensures the convention propagates through any depth of sub-agent chain.
