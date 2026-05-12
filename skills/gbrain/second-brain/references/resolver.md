# Second Brain — Hermes Agent Resolver

> **This file is autoloaded into the Hermes system prompt.** It teaches the agent WHAT gbrain is, WHEN to use it, and WHICH skills to load.

## What gbrain Is

gbrain is your second brain — a knowledge graph storing everything you know about people, companies, projects, concepts, meetings, and ideas. It lives in a Postgres database with hybrid search (keyword + vector). Hermes reads and writes it via MCP tools (`mcp_gbrain_*`).

**Core principle:** The brain knows things you don't remember. Search it before guessing.

## When to Use gbrain

**ALWAYS search gbrain before answering questions about:**
- People ("who is...", "what do I know about...")
- Companies, projects, deals
- Past decisions, meetings, conversations
- Concepts, ideas, frameworks you've captured
- Anything you might have written down before

**ALWAYS write to gbrain when:**
- User corrects you about a person/company/fact → write immediately
- User shares something worth remembering (idea, decision, observation)
- You conclude something worth storing (findings, state changes)
- Any operational skill produces durable output

## Available Tools

| Tool | Use For |
|------|---------|
| `mcp_gbrain_search` | Keyword search — fast, always works. Start here. |
| `mcp_gbrain_query` | Hybrid search (keyword + vector). Use when search is thin. |
| `mcp_gbrain_get_page` | Read a full page when you know the slug. |
| `mcp_gbrain_put_page` | Create or update a page. **Must load page-writer conventions first.** |
| `mcp_gbrain_add_timeline_entry` | Add a dated event to a page. |
| `mcp_gbrain_add_link` | Create a relationship edge between pages. |
| `mcp_gbrain_get_backlinks` | See who references this page. |
| `mcp_gbrain_get_timeline` | Get dated events for a page. |
| `mcp_gbrain_resolve_slugs` | Fuzzy slug lookup. |
| `mcp_gbrain_traverse_graph` | Walk the relationship graph. |
| `mcp_gbrain_get_health` | Brain health dashboard. |
| `mcp_gbrain_get_stats` | Page count, chunk count, etc. |
| `mcp_gbrain_delete_page` | Soft-delete a page (recoverable for 72h). |

## The Lookup Chain (MANDATORY ORDER)

1. **`mcp_gbrain_search`** — keyword search first. Fast, zero API cost.
2. **`mcp_gbrain_query`** — hybrid search if keyword results are thin.
3. **`mcp_gbrain_get_page`** — read full page if you found a relevant slug.
4. **External knowledge only after steps 1-3 return nothing useful.**

Never skip to external knowledge without searching gbrain. The answer is probably there.

## Skill Dispatch

When you need to perform a gbrain operation, load the appropriate skill:

| Operation | Skill to Load |
|-----------|--------------|
| Write/save a page | `skill_view(name="gbrain-page-writer")` |
| Search/query/lookup | `skill_view(name="gbrain-query")` |
| Enrich a person/company | `skill_view(name="gbrain-enrich")` (Phase 2) |
| Ingest content | `skill_view(name="gbrain-ingest")` (Phase 2) |
| Brain health/maintenance | `skill_view(name="gbrain-maintain")` (Phase 2) |

**Foundation skill:** `skill_view(name="second-brain")` loads the core conventions. The operational skills above load it automatically — you don't need to load both.

## Iron Laws

1. **Search before you guess.** The brain has information you don't remember.
2. **Cite everything.** Every fact written to gbrain needs `[Source: ...]`.
3. **Back-link everything.** Every entity mention must link back. An unlinked mention is a broken brain.
4. **Preserve exact phrasing.** The user's language IS the insight. Never paraphrase.
5. **Dedup before create.** Search existing pages before creating new ones.

## What NOT to Use gbrain For

- **Tasks and todos** → org-mode files (`/data/syncthing/Sync/org/`)
- **Live sprint state** → `tasks.org` directly (gbrain snapshots are stale)
- **Reminders and scheduling** → Hermes cron + Google Tasks
- **Sub-agent orchestration** → Hermes `delegate_task`
- **Journal entries** → `coy-journal` skill (which may write timeline entries TO gbrain, but journaling itself is Hermes-native)
- **Skill creation** → Hermes `skill_manage`
- **Cron scheduling** → Hermes `cronjob`
