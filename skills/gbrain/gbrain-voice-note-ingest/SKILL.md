---
name: gbrain-voice-note-ingest
description: "Process voice memos and dictations into gbrain pages with exact-phrasing preservation. Captures the raw verbatim content alongside structured extraction of key points, tasks, and entities."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, ingestion, voice, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, gbrain-ingest]
---

# GBrain Voice Note Ingest

Process voice memos, dictations, and transcribed audio recordings into gbrain pages. The most important rule: PRESERVE EXACT PHRASING. Voice notes capture raw, unfiltered thinking — that texture is the value.

## When to Use

- User shares a voice memo or audio recording
- User says "transcribe this and save it to my brain"
- User provides a speech-to-text output from a dictation
- Called by gbrain-ingest when content is classified as `voice-note`
- Automation pipeline delivers voice memo files

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Determine Page Type

Voice notes can contain several types of content. Classify based on content:

| Content | Page Type | Slug Prefix |
|---------|-----------|-------------|
| General thoughts, reflections | `idea` | `ideas/` |
| Journal entry, daily update | `writing` | `originals/` |
| Specific concept or idea | `concept` | `concepts/` |
| Task list or project plan | `personal` | `personal/` |
| Meeting or conversation notes | `meeting` | `meetings/` |

### Step 3: Preserve Exact Phrasing

The most critical step. Always include the FULL transcribed text verbatim in the page.

**Above the line (compiled truth):** structured extraction (key points, tasks, entities).
**Below the line (timeline):** the RAW TRANSCRIPT, preserved exactly.

This is the OPPOSITE of normal page structure — voice notes are valuable for their raw texture, not their structure.

### Step 4: Dedup Check

If the voice note references known topics:

```
mcp_gbrain_search(query="<topic from voice note>")
mcp_gbrain_resolve_slugs(partial="<entity name>")
```

Add to existing pages rather than creating new ones when the voice note elaborates on existing topics.

### Step 5: Build Page Content

**Above the line (compiled truth):**

```markdown
---
type: <type>
title: <Topic> - Voice Note YYYY-MM-DD
tags: [voice-note, <topic>]
recorded: YYYY-MM-DD
created: YYYY-MM-DD
---

# <Title>

> One-paragraph summary of the voice note content.

## Key Points
- {Structured point 1 from the voice note}
- {Structured point 2 from the voice note}

## Tasks & Action Items
- [ ] {Task extracted from voice note}

## Entities Mentioned
- {Person/company/concept referenced in the recording}

## Mood & Context
- {Tone of the recording — excited, frustrated, reflective}
- {Context: where/when it was recorded}

## Personal Relevance
- Why this matters to you / your projects

## Open Threads
- {Questions raised, things to follow up on}
```

**Below the line (raw transcript):**

```

---

## Raw Transcript

> {Exact verbatim text of the voice note, preserved character-for-character.
> Do NOT clean up, edit, or "improve" the wording. The language IS the insight.
> Include filler words, hesitations, re-starts — all of it.}
```

### Step 6: Write Page

```
mcp_gbrain_put_page(slug="<prefix>/<slug>", content="<full markdown>")
```

### Step 7: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="<prefix>/<slug>",
    date="YYYY-MM-DD",
    summary="Voice note: {topic}",
    detail="Mood: {tone}. Key extract: {one-line from raw transcript}."
)
```

### Step 8: Create Back-Links

For every entity mentioned that has a brain page:

```
mcp_gbrain_add_link(from="<prefix>/<slug>", to="<entity_slug>", link_type="references")
```

Back-linking is mandatory — see `second-brain/references/quality.md`.

## The "Exact Phrasing" Iron Law

Voice notes are the rawest form of personal knowledge capture. They contain:

- **Emotional texture** — excitement, frustration, uncertainty. This is INFORMATION.
- **Unfiltered thinking** — ideas still being formed. The rough edges matter.
- **Exact words** — the user chose those words. Paraphrasing loses meaning.

**NEVER:**
- Clean up grammar or sentence structure
- Remove "um", "uh", filler words
- Correct factual errors in the transcript (note them separately)
- Summarize away the raw content

**ALWAYS:**
- Include the full raw transcript verbatim
- Add a note if the transcript contains factual errors the user should correct
- Separate structured extraction (above the line) from raw content (below the line)

## Common Pitfalls

- **Paraphrasing instead of preserving** — the raw transcript is the most valuable part. Do not lose it.
- **Over-structuring** — voice notes are unstructured by nature. Do not force them into rigid categories.
- **Missing entity detection** — voice notes often name-drop. Extract every entity.
- **Wrong page type** — if unsure, use `ideas/` as the default. It can be reclassified later.
- **No mood context** — the emotional tone of a voice note is data. Capture it.
- **Cleaning up** — the user's exact words are sacred. Do not "fix" them.

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Page type determined and slug created
- [ ] Dedup check performed
- [ ] Full raw transcript preserved verbatim in timeline section
- [ ] Structured extraction (key points, tasks, entities) above the line
- [ ] Mood and context captured
- [ ] Personal relevance section present
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added for this voice note
