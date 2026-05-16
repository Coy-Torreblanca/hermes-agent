---
name: gbrain-idea-ingest
description: Digest links, articles, tweets, blog posts, and free-form ideas into gbrain pages. Preserves exact wording, extracts key claims, creates concept/idea pages with proper structure.
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, ingestion, ideas, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, gbrain-ingest]
---

# GBrain Idea Ingest

Take external content — links, articles, tweets, blog posts, or free-form ideas — and persist them as structured gbrain pages with exact wording preservation, key claim extraction, and cross-linking.

## When to Use

- User shares a link and says "save this", "ingest this", "remember this"
- User pastes an article, tweet, or blog post for the brain to retain
- User has an idea or concept they want captured (even rough/unstructured)
- Called by gbrain-ingest when content is classified as `idea`
- RSS feed, email hook, or webhook delivers new content to persist

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Determine Page Type

| Content | Page Type | Slug Prefix | Example |
|---------|-----------|-------------|---------|
| External article/blog | `writing` | `originals/` | `originals/karpathy-software-2-0` |
| Tweet/social post | `writing` | `originals/` | `originals/tweet-accel-simulation` |
| Link/bookmark | `media` | `media/` | `media/arxiv-llm-safety-2026` |
| Free-form idea | `idea` | `ideas/` | `ideas/coding-agent-marketplace` |
| Concept/mental model | `concept` | `concepts/` | `concepts/brand-code` |

### Step 3: Dedup Check

Search gbrain for existing content:

```
mcp_gbrain_search(query="<title or URL>")
mcp_gbrain_resolve_slugs(partial="<topic>")
```

If content already exists → UPDATE with new context. Do NOT duplicate.
If URL already stored → add timeline entry for re-engagement. Do NOT duplicate.

### Step 4: Extract Content

For URLs: fetch and extract the content using terminal tools or delegate tasks.

For text content (tweet, message, idea): use the content directly.

### Step 5: Build Page Content

**Above the line (compiled truth):**

```markdown
---
type: <type>
title: <Title>
tags: [relevant, tags]
source_url: <original URL if applicable>
created: YYYY-MM-DD
---

# Title

> One-paragraph summary: what this is and why it matters.

## Key Claims
- {Claim 1} [Source: {publication}, {URL}, YYYY-MM-DD]
- {Claim 2} [Source: ...]

## Key Takeaways
- {Takeaway relevant to you}

## Personal Relevance
- Why this matters to you / your projects
- Connections to existing brain pages

## Open Threads
- {Questions raised, follow-ups}
```

**Below the line (timeline):**

```
---

## Timeline
- **YYYY-MM-DD** | [Source: {source}] — Ingested. {First impression or note}.
```

### Step 6: Preserve Exact Phrasing

When quoting the source, preserve the exact wording. Paraphrasing loses context.

- **For tweets:** quote the full tweet text in a blockquote
- **For articles:** quote the most salient passage(s) in blockquotes
- **For ideas:** use the user's exact words, not your interpretation

### Step 7: Write Page

```
mcp_gbrain_put_page(slug="<prefix>/<slug>", content="<full markdown>")
```

### Step 8: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="<prefix>/<slug>",
    date="YYYY-MM-DD",
    summary="Ingested: {title}",
    detail="Source: {URL or context}. Key takeaway: {one-line summary}."
)
```

### Step 9: Create Back-Links

For every person/company/concept mentioned that has a brain page:

```
mcp_gbrain_add_link(from="<this_page>", to="<entity_slug>", link_type="references")
```

Back-linking is mandatory — see `second-brain/references/quality.md`.

## Ingestion Quality Rules

- **No AI summary in place of the original** — always include at least one exact quote
- **No filler content** — if the source has only one valuable insight, capture that one insight, not the whole article
- **Tag for retrieval** — add tags matching filing conventions (not verbs like "ingested", "saved")
- **Personal relevance is mandatory** — the most important field. Why does this matter to the user?
- **Source URL** — always include in frontmatter when available

## Common Pitfalls

- **Paraphrasing the source** — use blockquotes for original text, not your summary
- **No dedup check** → duplicates for the same article/tweet
- **Missing personal relevance** — an article with no "why this matters" is noise
- **Over-tagging** — 2-4 tags max. Be precise, not exhaustive.
- **Swallowing errors** — if URL fetch fails, tell the user and offer alternatives (paste text instead)

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Page type determined correctly
- [ ] Dedup check performed (search + resolve_slugs)
- [ ] Original text preserved (exact quotes in blockquotes)
- [ ] Personal relevance section present
- [ ] Source URL in frontmatter (if applicable)
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added for this ingestion
