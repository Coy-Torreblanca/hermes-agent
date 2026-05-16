---
name: gbrain-enrich
description: "Build dossiers on people from journal entries, conversations, and observations (not API-based). Sources: journal mentions, conversation snippets, user corrections. Outputs two-layer person pages with compiled truth and timeline."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, enrich, dossiers, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, coy-journal]
---

# GBrain Enrich — Entity Dossiers

Build and enrich person/company pages from organic sources: journal entries, conversations, user observations, and corrections. NEVER uses external APIs for enrichment — only what the user has said or written.

## When to Use

- User says "tell me more about [person]", "enrich [person]'s page"
- User shared observations about someone in conversation
- You find a person page with sparse content that could be enriched
- After a conversation where the user spent significant time talking about someone
- User corrects you about someone — write the correction AND enrich
- During orphan enrichment (connected from gbrain-maintain)

## Workflow

### Step 1: Load Conventions

Before any enrich operation:

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/repo-architecture.md
```

Wait for all conventions to load before proceeding.

### Step 2: Identify the Subject

Determine the entity to enrich:
1. **Person:** `people/first-last`
2. **Company/Organization:** `companies/org-name`
3. **Project:** `projects/project-name`

Use `mcp_gbrain_resolve_slugs(partial="<name>")` to check if the page exists.

### Step 3: Gather Source Material

Collect raw source material about the subject:

- **Journal entries:** Search `mcp_gbrain_query(query="<name> journal")` for journal pages mentioning them
- **Conversations:** Search `mcp_gbrain_query(query="<name>")` for any brain pages that reference them
- **Timeline entries:** Use `mcp_gbrain_get_timeline(slug="people/<name>")` or query for timeline mentions
- **Back-links:** Use `mcp_gbrain_get_backlinks(slug="people/<name>")` to find pages that reference them
- **User corrections:** Any direct statement the user made about this person

### Step 4: Compile Dossier

Using all source material, build the enriched page. Follow the Person Page Template from schema.md:

**Above the line (compiled truth):**

```
# Person Name

> Executive summary: who they are to you, what matters walking into any interaction.

## The Basics
- **Relationship:** {how you know them}
- **Key context:** {2-4 bullets of what matters}

## Professional
- **Role:** {current title}
- **Company:** {where they work}

## Who They Are
- {Trait} - observed: {context, [Source: ...]}
- {Trait} - self-described: {context, [Source: ...]}

## Likes & Dislikes
- **Likes:** {specific items with sources}
- **Dislikes:** {specific items with sources}

## Important Relationships
- {People they are close to, with sources}

## Communication Style
- {How they communicate, from direct observation}

## Current Situation
- {What is going on in their life}

## Shared History
- {Key moments, context}

## Open Threads
- {Active items to follow up on}

---

## Timeline
- {reverse-chronological entries}
```

### Step 5: Epistemic Labeling

Every claim MUST be labeled with its source type:

| Label | Meaning | Example |
|-------|---------|---------|
| `observed` | You saw it happen | conversation behavior, messages |
| `self-described` | They said it about themselves | they told you, bio, public statement |
| `inferred` | Reading between lines | pattern across N interactions |

**Confidence rules:**
- 1 interaction - low confidence. No definitive assessments.
- 5+ interactions - high confidence.
- Mark explicitly: `confidence: high/medium/low`

### Step 6: Preserve Exact Phrasing

When quoting the user about someone, preserve their exact words. The language IS the insight.

- Wrong: "User says she is aggressive in meetings"
- Right: User described her as "really pushing back on pricing in the March 15 meeting" [Source: User, conversation, 2026-05-13]

### Step 7: Write or Update the Page

If page exists - UPDATE with new content while preserving existing timeline.
If page does not exist - CREATE new page.

```
mcp_gbrain_put_page(slug="people/<name>", content="<full markdown>")
```

### Step 8: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="people/<name>",
    date="YYYY-MM-DD",
    summary="Enriched from {source}",
    detail="Added sections: {list of sections updated}."
)
```

### Step 9: Create Back-Links

For every person/company/project mentioned in the enriched page that has a brain page:

```
mcp_gbrain_add_link(from="people/<name>", to="<entity_slug>", link_type="references")
```

Back-linking is mandatory — see `second-brain/references/quality.md`.

## Enrichment Triggers (When NOT Asked)

Proactively enrich when:

- **After a conversation** where the user talked about someone at length
- **User correction** - the correction itself is enrichment material
- **Orphan enrichment** - during brain maintenance, sparse person pages found
- **Journal review** - weekly, scan journal for people mentioned multiple times
- **New relationship** - user mentions someone new in ongoing context

DO NOT enrich proactively during a conversation unless the user pauses. Context matters - do not interrupt.

## Source Priority

| Priority | Source Type | Notes |
|----------|-------------|-------|
| 1 | User direct statements | Highest authority |
| 2 | Journal entries | Written reflections |
| 3 | Conversation transcripts | May need interpretation |
| 4 | Timeline entries | Raw evidence |

## Common Pitfalls

- **API enrichment** - THIS SKILL NEVER uses external APIs. Enrich from organic sources only.
- **Over-interpreting** - one data point is not a trait. Wait for 3+ observations.
- **Stale enrichment** - enrich using recent sources. Traits from 2 years ago may not be current.
- **Paraphrasing** - preserve exact user wording. Do not "clean up" their language.
- **Missing confidence** - always label epistemic confidence. Low confidence = timeline only, no compiled truth.

## Verification Checklist

- [ ] Conventions loaded via skill_view() before writing
- [ ] Subject page exists or created (dedup check performed)
- [ ] Source material gathered from journal, conversations, observations
- [ ] All claims labeled with source type (observed/self-described/inferred)
- [ ] Exact phrasing preserved where user spoke
- [ ] Confidence levels marked per section
- [ ] Two-layer structure (compiled truth + timeline)
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added for this enrichment pass
