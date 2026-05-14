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

Copy-pasteable. All sections optional — use `[No data yet]` rather than omitting.
The structure itself prompts future enrichment. Fill what matters for YOUR relationship
with this person — not every section applies to everyone.

```markdown
# Person Name

> Executive summary: who they are to you, what you should know
> walking into any interaction.

## The Basics
- **Relationship:** how you know them (family, friend, colleague, neighbor, etc.)
- **Birthday:** (if known — important for personal relationships)
- **Location:** where they live
- **Key context:** 2–4 bullets of what matters right now

## Who They Are
Personality, character, values. What kind of person are they?
- [Trait] — observed: [context, date]
- [Trait] — self-described: [context, date]

## Likes & Dislikes
What they enjoy, what they avoid. Use for gifts, activities, conversations.
- **Likes:** [food, music, hobbies, topics, activities]
- **Dislikes:** [things to avoid suggesting or bringing up]

## Important Relationships
- **Family:** spouse, kids, parents, siblings (names if known)
- **Close to:** people they're frequently with or mention
- **Your dynamic:** history, temperature, how you interact

## Communication Style
How they prefer to communicate. How they handle disagreement.
Only from direct observation. Never generalize from a single data point.

## Current Situation
What's going on in their life right now — challenges, changes, joys.
Updates from recent conversations or observations.

## Shared History
Key moments, inside jokes, things you've done together.
This is what makes the relationship real.

## Contact
- Phone, email, address, social handles

## Open Threads
- Active items: things to follow up on, promises made, questions to ask

---

## Timeline
- **YYYY-MM-DD** | Source — What happened.
```

### Optional Business Sections

If this person is also a professional contact, add below **The Basics**:

```
## Professional
- **Role:** current title
- **Company/Organization:** where they work
- **Industry/Field:** what they do
- **What They're Building:** current projects, direction
- **Career Context:** relevant background, trajectory
```

If you need deeper professional assessment, add:

```
## Professional Assessment
- **Strengths:** be specific
- **Gaps:** be specific and fair
- **Net read:** one-line synthesis
- **Confidence:** high (5+ interactions) / medium (2–4) / low (1 or inferred)
```

---

## Organization / Company Page Template

Use for any organization: companies, churches, nonprofits, schools, clubs.

```markdown
# Organization Name

> What they do, why they matter to you.

## State
- **What:** one-line description
- **Type:** company / nonprofit / church / school / etc.
- **Size/Scale:** rough sense (local, regional, national, headcount, etc.)
- **Key people:** names with links to people pages
- **Connection:** how they relate to your world

## Open Threads

---

## Timeline
- **YYYY-MM-DD** | Source — What happened.
```

---

## Epistemic Discipline (MANDATORY)

Context sections (Who They Are, Likes & Dislikes, Current Situation, Professional Assessment)
are highest-value but most prone to hallucination. Rules:

### Every claim cites its source
Not "she's aggressive" but "she pushed back hard on pricing in the March 15
meeting (observed)."

### Three source types — label EVERY claim

| Label | Meaning | Example |
|-------|---------|---------|
| `observed` | You saw it happen | conversation behavior, messages, interactions |
| `self-described` | They said it about themselves | they told you, bio, public statement |
| `inferred` | Reading between lines | pattern across N interactions |

### Confidence tracks interaction count
- **1 interaction** → low confidence. Don't write definitive assessments.
- **5+ interactions** → high confidence.
- Mark confidence explicitly: `confidence: high/medium/low`

### Recency matters
A trait from 2 years ago may not be current. Mark dates. Update stale sections.

### Never generalize from a single data point
"She seemed frustrated in one conversation" → timeline entry.
"This person is easily frustrated" → requires multiple observations.

### User corrections override everything
If the user says "that's wrong about her," update immediately. That correction
is the highest-confidence signal in the system.

---

## Entity Identity & Deduplication (MANDATORY)

### Slug Naming Convention (MANDATORY)

**Rule: hyphens in all paths, never underscores.**

Wrong: `second_brain/2026-05-12-second-brain-crud`
Right: `second-brain/crud-implementation-plan`

| Slug Component | Separator | Example |
|---------------|-----------|---------|
| Directory name | hyphen | `people/`, `companies/`, `projects/`, `second-brain/` |
| Entity name | hyphens for spaces | `jane-doe`, `acme-corp` |
| Full path | hyphens throughout | `projects/personalai/second-brain/crud-implementation-plan` |

**Date prefixes are only for meeting pages.** Never use `YYYY-MM-DD-` for
entity, project, concept, or idea pages.

| Page Type | Slug Pattern | Example |
|-----------|-------------|---------|
| Person | `people/first-last` | `people/jane-doe` |
| Company | `companies/organization-name` | `companies/acme-corp` |
| Project | `projects/project-name` | `projects/my-project` |
| Concept | `concepts/concept-name` | `concepts/attention-is-all-you-need` |
| Meeting | `meetings/YYYY-MM-DD-topic` | `meetings/2026-05-14-sprint-review` |
| Idea | `ideas/topic-slug` | `ideas/coding-agent-marketplace` |
| Writing | `originals/article-title` | `originals/software-2-0` |
| Media | `media/title-of-content` | `media/lex-fridman-podcast-456` |
| Sub-project | `projects/parent/sub-component` | `projects/personalai/second-brain/crud-implementation-plan` |

### Canonical slugs

- People: `first-last` (lowercase, hyphens for spaces)
- Organizations: `organization-name` (companies, churches, nonprofits, schools)
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
