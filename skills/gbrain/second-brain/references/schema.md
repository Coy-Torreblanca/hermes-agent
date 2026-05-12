> **This is a reference file loaded via `skill_view()`.**
> All brain writes use Hermes MCP tools: `mcp_gbrain_put_page`, `mcp_gbrain_add_link`, `mcp_gbrain_add_timeline_entry`.

# Brain Schema — Page Conventions & Templates

Abbreviated from GBRAIN_RECOMMENDED_SCHEMA. Covers page structure, templates,
epistemic discipline, and entity identity. For enrichment pipeline, ingest
workflows, and cron jobs, see the full schema in `/opt/gbrain/docs/`.

---

## Two-Layer Page Model (MANDATORY)

Every brain page has two layers separated by `---`:

**Above the line — Compiled Truth.** Always current, rewritten when new info
arrives. Executive summary first, then structured State fields, Open Threads
(active items — removed when resolved), and See Also.

**Below the line — Timeline.** Append-only, never rewritten.
Reverse-chronological evidence log. Each entry: date, source, what happened.

If someone asks "what's the current state?" → read above the line.
If someone asks "what happened?" → read below the line.

---

## Frontmatter Conventions (MANDATORY)

Every page starts with YAML frontmatter. Anything you'd want to query (role,
company, stage, tags) goes here — not buried in prose.

```yaml
---
type: person
title: Jane Doe
tags: [investor, ai-infra, tier-1]
aliases: ["J. Doe", "jdoe@company.com", "@janedoe"]
---
```

- `type`: one of `person`, `company`, `meeting`, `deal`, `project`, `concept`, `idea`, `writing`, `program`, `org`, `civic`, `media`, `personal`, `household`, `hiring`, `prompt`, `source`
- `title`: display name (may differ from slug)
- `tags`: lowercase, hyphenated. Use `tier-1`/`tier-2`/`tier-3` for enrichment priority
- `aliases`: all known name variants (misspellings, maiden names, nicknames, email addresses, social handles)

---

## Person Page Template

Copy-pasteable. All sections optional — use `[No data yet]` rather than
omitting. The structure itself prompts future enrichment.

```markdown
# Person Name

> Executive summary: who they are, why they matter, what you should
> know walking into any interaction.

## State
- **Role:** current title
- **Company:** current org
- **Relationship:** to you (friend, colleague, investor, etc.)
- **Key context:** 2–4 bullets of what matters right now

## What They Believe
Worldview, positions, first principles. Every claim cites source + type:
- [Belief] — observed: [tweet/meeting/article, date]
- [Belief] — self-described: [interview/bio, date]
- [Belief] — inferred: [pattern across N interactions, confidence: high/medium/low]

## What They're Building
Current projects, recent ships, product direction.

## What Motivates Them
Ambition drivers, career arc. Distinguish self-described from observed/inferred.

## Communication Style
How they prefer to communicate. How they handle disagreement.
Only from direct observation (meetings, emails, tweets). Never generalize from
a single data point. Mark confidence level.

## Hobby Horses
Topics they return to obsessively. Recurring themes in their public voice.

## Assessment
- **Strengths:** be specific
- **Gaps:** be specific and fair
- **Net read:** one-line synthesis
- **Confidence:** high (5+ interactions) / medium (2–4) / low (1 or inferred)
- **Last assessed:** YYYY-MM-DD

## Trajectory
Ascending, plateauing, pivoting, declining? Evidence.

## Relationship
History of interactions, temperature, dynamic.

## Contact
- Email, phone, X handle, LinkedIn, location

## Network
- **Close to:** people they're frequently seen with
- **Crew:** which cluster they belong to

## Open Threads
- Active items, pending intros, follow-ups

---

## Timeline
- **YYYY-MM-DD** | Source — What happened.
```

---

## Company Page Template

```markdown
# Company Name

> What they do, stage, why they matter.

## State
- **What:** one-line description
- **Stage:** Seed / Series A / Growth / Public
- **Key people:** names with links to people pages
- **Key metrics:** revenue, headcount, funding
- **Connection:** how they relate to your world

## Open Threads

---

## Timeline
- **YYYY-MM-DD** | Source — What happened.
```

---

## Epistemic Discipline (MANDATORY)

Context sections (Beliefs, Motivations, Communication Style, Assessment) are
highest-value but most prone to hallucination. Rules:

### Every claim cites its source
Not "she's aggressive" but "she pushed back hard on pricing in the March 15
meeting (observed)."

### Three source types — label EVERY claim

| Label | Meaning | Example |
|-------|---------|---------|
| `observed` | You saw it happen | meeting behavior, emails, tweets |
| `self-described` | They said it about themselves | interview, bio, public statement |
| `inferred` | Reading between lines | pattern across N interactions |

### Confidence tracks interaction count
- **1 meeting** → low confidence. Don't write definitive assessments.
- **5+ meetings** → high confidence.
- Mark confidence explicitly: `confidence: high/medium/low`

### Recency matters
A belief from 2 years ago may not be current. Mark dates. Update stale sections.

### Never generalize from a single data point
"She seemed frustrated in one meeting" → timeline entry.
"This person is easily frustrated" → requires multiple observations.

### User corrections override everything
If the user says "that's wrong about her," update immediately. That correction
is the highest-confidence signal in the system.

---

## Entity Identity & Deduplication (MANDATORY)

### Canonical slugs
- People: `first-last` (lowercase, hyphens for spaces)
- Companies: `company-name`
- Disambiguation: `david-liu-crustdata`, `david-liu-meta`

The filename IS the identity. All references, cross-links, and .raw/ sidecars
use this slug.

### Aliases
People have many names across sources. Frontmatter `aliases` captures all:

```yaml
aliases: ["Jenny Shao", "Jenny G. Shao", "JennyGShao", "jennifer.shao@company.com"]
```

Include: misspellings from transcripts, maiden names, nicknames, email
addresses, social handles. When enrichment encounters a new variant for
a known entity, add to aliases — do NOT create a new page.

### Dedup Protocol — before creating ANY page

1. **Search by name** — exact and fuzzy (`mcp_gbrain_search`, `mcp_gbrain_query`)
2. **Search aliases** — `mcp_gbrain_search` with name variants
3. **Check .raw/ sidecars** — matching email addresses or social handles
4. **If match found** → UPDATE existing page (add alias if name variant is new)
5. **If no match** → CREATE new page

### Merge Protocol — when duplicate pages are discovered

1. Pick the more complete page as survivor
2. Merge all timeline entries into survivor (chronological order)
3. Merge all aliases
4. Update all cross-references that pointed to the duplicate
5. Delete the duplicate (`mcp_gbrain_delete_page`)
