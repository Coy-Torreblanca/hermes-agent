---
name: gbrain-ingest
description: Generic "ingest this" auto-router. Classifies incoming content type (idea, media, meeting, voice-note) and dispatches to the appropriate sub-skill. Single entry point for all ingestion into gbrain.
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, ingestion, router, second-brain]
    related_skills: [second-brain, gbrain-idea-ingest, gbrain-media-ingest, gbrain-meeting-ingestion, gbrain-voice-note-ingest]
---

# GBrain Ingest — Auto-Router

Single entry point for ALL content ingestion into gbrain. Classifies incoming content by type and dispatches to the appropriate specialized sub-skill. Never ingests directly — always delegates.

## When to Use

- User says "ingest this", "save this to my brain", "add this to gbrain"
- User shares a link, article, screenshot, voice memo, or meeting notes
- User says "read this and remember it"
- Any service (RSS, calendar, email hook) has content to persist
- Cron job output needs to be saved as a brain page

## Workflow

### Step 1: Classify Content

Analyze the incoming content to determine type:

| Signal | Type | Dispatch Skill |
|--------|------|----------------|
| URL (article, tweet, blog, link) | `idea` | gbrain-idea-ingest |
| PDF, image, screenshot, YouTube link | `media` | gbrain-media-ingest |
| Meeting transcript, call notes, calendar event notes | `meeting` | gbrain-meeting-ingestion |
| Audio file, voice memo, speech-to-text result | `voice-note` | gbrain-voice-note-ingest |
| General thought, concept, observation in text | `idea` | gbrain-idea-ingest |

### Step 2: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 3: Dispatch to Sub-Skill

Load the appropriate sub-skill:

```
skill_view(name="gbrain-idea-ingest")
```

or

```
skill_view(name="gbrain-media-ingest")
```

or

```
skill_view(name="gbrain-meeting-ingestion")
```

or

```
skill_view(name="gbrain-voice-note-ingest")
```

Follow the sub-skill's workflow. The sub-skill handles dedup, page structure, citations, and back-links.

### Step 4: Confirm Ingestion

After the sub-skill completes, summarize what was ingested:

- Page slug and title
- Page type
- Source material summary
- Any enrichment opportunities discovered during ingestion

### Step 5: Log Ingestion Event

```
mcp_gbrain_log_ingest(
    source_type="<content_type>",
    source_ref="<url_or_reference>",
    pages_updated=["<slug>"],
    summary="Ingested <content_type>: <description>"
)
```

## Classification Heuristics

### URL Detection
- Contains `http://` or `https://` → likely idea or media
- YouTube, Vimeo → media
- Twitter/X, LinkedIn, blog → idea
- PDF, .docx → media

### Media Detection
- Mention of video, audio recording, podcast, screenshot
- File extensions: .pdf, .mp3, .mp4, .png, .jpg, .docx
- References to "screenshot", "recording", "document"

### Meeting Detection
- References to a meeting, call, sync, standup, 1:1
- Transcript keywords: "said", "discussed", "agreed", "next steps"
- Calendar event notes format

### Voice Note Detection
- Audio file reference
- "Voice memo", "voice note", "recorded", "dictated"
- Speech-to-text output format

## Sub-Skill Reference

| Skill | Content Types | Page Type | Key Behavior |
|-------|---------------|-----------|--------------|
| gbrain-idea-ingest | Links, articles, tweets, ideas, concepts | `idea`, `concept`, `writing` | Preserves exact wording, extracts key claims |
| gbrain-media-ingest | Video, audio, PDF, screenshots, YouTube | `media` | Processes rich media to structured notes |
| gbrain-meeting-ingestion | Meeting transcripts, call notes | `meeting` | Identifies attendees, decisions, action items |
| gbrain-voice-note-ingest | Voice memos, dictations | `meeting`, `idea` | Preserves exact phrasing, timestamps |

## Common Pitfalls

- **Ingesting directly** — always delegate. This skill is a router, not a writer.
- **Wrong classification** — if ambiguous, ask the user: "Is this an idea, a meeting note, a voice memo, or media?"
- **Missing load** — must load the sub-skill before dispatching. The sub-skill has its own convention loading.
- **No dedup check** — sub-skills handle dedup internally. Don't pre-check here.
- **Forgetting log** — always log ingestion events for traceability.

## Verification Checklist

- [ ] Content classified correctly (idea/media/meeting/voice-note)
- [ ] Appropriate sub-skill loaded via skill_view()
- [ ] Sub-skill workflow followed completely (includes quality conventions)
- [ ] Ingestion confirmed with summary to user
- [ ] Ingestion event logged via mcp_gbrain_log_ingest
- [ ] If ambiguous, user consulted for classification
