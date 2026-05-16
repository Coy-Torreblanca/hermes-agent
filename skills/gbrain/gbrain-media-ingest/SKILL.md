---
name: gbrain-media-ingest
description: "Process rich media into structured gbrain pages: video transcripts, audio podcasts, PDF documents, screenshots, and YouTube links. Extracts key content and creates media pages with summaries and cross-links."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, ingestion, media, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, gbrain-ingest]
---

# GBrain Media Ingest

Process rich media content — video, audio, PDF, screenshots, YouTube links — into structured gbrain pages. Extracts key content, creates summaries, and cross-links to relevant entities.

## When to Use

- User shares a YouTube link, podcast, or video for the brain to remember
- User provides a PDF, document, or screenshot they want indexed
- User says "watch this and summarize it for my brain"
- Called by gbrain-ingest when content is classified as `media`
- Automation pipeline (RSS, email) delivers media attachments

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Identify Media Type

| Media | Slug Prefix | Type Field | Extraction Method |
|-------|-------------|------------|-------------------|
| YouTube/video | `media/` | `media` | Download transcript or watch via browser |
| Podcast/audio | `media/` | `media` | Transcribe or get show notes |
| PDF document | `media/` | `media` | Extract text via pymupdf/marker-pdf |
| Screenshot/image | `media/` | `media` | Vision analysis of screenshot |
| General document | `media/` | `media` | Read file and extract structure |

### Step 3: Dedup Check

```
mcp_gbrain_search(query="<title or URL>")
mcp_gbrain_resolve_slugs(partial="<topic>")
```

If content already exists - UPDATE with new context. Do NOT duplicate.

### Step 4: Extract Content

Use appropriate extraction method based on media type:

- **YouTube:** Use `youtube-content` skill to get transcript, then summarize
- **PDF/DOCX:** Use `ocr-and-documents` skill for text extraction
- **Screenshots:** Use `vision_analyze` tool to describe content
- **Audio podcast:** Summarize provided show notes or transcript

Call the appropriate extraction skill:
```
skill_view(name="youtube-content")  # for video
skill_view(name="ocr-and-documents")  # for PDF/scans
```

### Step 5: Build Page Content

**Above the line (compiled truth):**

```markdown
---
type: media
title: <Content Title>
tags: [media, <topic>]
source_url: <original URL if applicable>
media_type: <video/audio/pdf/screenshot>
created: YYYY-MM-DD
---

# Title

> One-paragraph summary: what this media is and why it matters.

## Content Summary
- Key topic or thesis
- Main points (3-5 bullets)
- Notable quotes or statistics

## Key Takeaways
- {What to remember from this content}

## Personal Relevance
- Why this matters to you / your projects
- Connections to existing brain pages

## Related Entities
- People mentioned (with slug links)
- Projects or concepts referenced

## Open Threads
- {Questions raised, follow-ups, things to research}
```

**Below the line (timeline):**

```
---

## Timeline
- **YYYY-MM-DD** | [Source: {source}] - Ingested. {First impression or note}.
```

### Step 6: Write Page

```
mcp_gbrain_put_page(slug="media/<slug>", content="<full markdown>")
```

### Step 7: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="media/<slug>",
    date="YYYY-MM-DD",
    summary="Ingested media: {title}",
    detail="Type: {media_type}. Source: {URL}. Key: {one-line takeaway}."
)
```

### Step 8: Create Back-Links

For every person/company/concept mentioned that has a brain page:

```
mcp_gbrain_add_link(from="media/<slug>", to="<entity_slug>", link_type="references")
```

Back-linking is mandatory — see `second-brain/references/quality.md`.

## Extraction Guidance

### Video/YouTube
- Get transcript first (highest fidelity)
- If no transcript available, use browser to watch and take notes
- Capture: speaker names, key arguments, timestamped highlights

### PDF/Documents
- Full text extraction via OCR tools
- Focus on: title, author, date, key arguments, data/tables
- For long documents: extract executive summary + key sections

### Screenshots
- Use vision_analyze to describe content
- Capture: what is shown, notable elements, any text
- Context matters - why was this screenshot taken?

## Common Pitfalls

- **No extraction tool available** - tell the user what is needed (e.g., "I need a transcript or show notes")
- **Over-summarization** - preserve key quotes and specifics. A vague summary is worse than no entry.
- **Missing personal relevance** - always answer "why does this matter to the user"
- **Duplicate ingestion** - always dedup before creating
- **Skipping entity detection** - media content is rich with named entities. Extract them.

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Media type identified correctly
- [ ] Dedup check performed
- [ ] Content extracted (transcript, OCR, vision analysis)
- [ ] Key points and quotes preserved
- [ ] Personal relevance section present
- [ ] Related entities extracted and linked
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added for this ingestion
