---
name: gbrain-meeting-ingestion
description: "Process meeting transcripts, call notes, and calendar event notes into structured gbrain pages. Identifies attendees, extracts decisions and action items, creates meeting pages with attendee enrichment."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, ingestion, meetings, second-brain]
    related_skills: [second-brain, gbrain-page-writer, gbrain-query, gbrain-enrich, gbrain-ingest]
---

# GBrain Meeting Ingestion

Process meeting transcripts, call notes, and calendar event notes into structured gbrain pages. Identifies attendees, extracts decisions and action items, and creates meeting pages with attendee enrichment and cross-linking.

## When to Use

- User says "save these meeting notes", "ingest this meeting transcript"
- User shares call notes or meeting minutes
- User mentions a meeting happened and provides details
- Calendar integration delivers meeting notes automatically
- Called by gbrain-ingest when content is classified as `meeting`

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_brain-filing-rules.md
read_file /data/.hermes/skills/gbrain/second-brain/references/schema.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Determine Meeting Slug

Format: `meetings/YYYY-MM-DD-topic`

- Date based on when the meeting occurred (not when ingested)
- Topic: brief slug of the meeting purpose
- Example: `meetings/2026-05-13-second-brain-sprint`

### Step 3: Dedup Check

```
mcp_gbrain_search(query="meeting <topic> <date>")
mcp_gbrain_resolve_slugs(partial="meetings/")
```

If duplicate meeting exists - UPDATE with new details or add to notes section. Do NOT create duplicate meeting pages.

### Step 4: Extract Meeting Structure

From the raw notes/transcript, extract:

| Field | Description | Always Available? |
|-------|-------------|-------------------|
| **Date** | When the meeting happened | Usually |
| **Attendees** | Who was there | Usually |
| **Topics** | What was discussed | Always |
| **Decisions** | What was decided | Usually |
| **Action Items** | Who needs to do what | Sometimes |
| **Duration** | How long it lasted | Sometimes |
| **Context** | Why this meeting happened | Usually |

### Step 5: Identify Attendees

For each attendee mentioned:
1. Check if they have a brain page: `mcp_gbrain_resolve_slugs(partial="<name>")`
2. If they do not exist yet, note them as potential new pages
3. Consider triggering gbrain-enrich if the user talks about them significantly

### Step 6: Build Page Content

**Above the line (compiled truth):**

```markdown
---
type: meeting
title: <Meeting Title> - YYYY-MM-DD
tags: [meeting, <topic>]
attendees: [Person A, Person B]
created: YYYY-MM-DD
---

# Meeting: <Title> (YYYY-MM-DD)

> One-paragraph summary: what this meeting was about and why it matters.

## Attendees
- **Person A** (@people/person-a) - Role in meeting
- **Person B** (@people/person-b) - Role in meeting

## Topics Discussed
1. **Topic 1** - {summary of discussion}
2. **Topic 2** - {summary of discussion}

## Decisions Made
- {Decision 1} [Source: Meeting notes, YYYY-MM-DD]
- {Decision 2} [Source: ...]

## Action Items
- [ ] **Action** - Owner: Person A (due: date)
- [ ] **Action** - Owner: Person B (due: date)

## Key Quotes
- "{Exact quote from the meeting}" - Speaker [Source: Meeting notes, YYYY-MM-DD]

## Personal Relevance
- How this meeting connects to your projects and goals
- Follow-ups you personally need to handle

## Open Threads
- {Unresolved questions, items to revisit}

---

## Timeline
- **YYYY-MM-DD** | [Source: Meeting notes] - Meeting held. {Context on what prompted the meeting}.
```

### Step 7: Update Attendee Pages

For regular contacts (user meets them repeatedly):
- Trigger gbrain-enrich to update their page with meeting context
- Add timeline entry: "Attended [meeting title] on YYYY-MM-DD"

### Step 8: Write Page

```
mcp_gbrain_put_page(slug="meetings/YYYY-MM-DD-topic", content="<full markdown>")
```

### Step 9: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="meetings/YYYY-MM-DD-topic",
    date="YYYY-MM-DD",
    summary="{Title} meeting",
    detail="Attendees: {list}. Key decisions: {summary}."
)
```

### Step 10: Create Back-Links

For every attendee and mentioned entity with a brain page:

```
mcp_gbrain_add_link(from="meetings/YYYY-MM-DD-topic", to="<entity_slug>", link_type="references")
mcp_gbrain_add_link(from="<entity_slug>", to="meetings/YYYY-MM-DD-topic", link_type="attended")  # for attendees
```

Back-linking is mandatory — see `second-brain/references/quality.md`.

## Quality Rules

- **Decisions over discussion** — what was decided matters more than the full transcript
- **Action items are mandatory** — a meeting without action items may not be worth keeping
- **Quotes preserve context** — who said what, not just what was said
- **Attendee enrichment** — only for people the user interacts with regularly. One-off meeting participants get a basic page link, not a full dossier.
- **Confidence on decisions** — if something is unclear from the notes, mark as "unconfirmed" rather than assuming

Quality conventions (citations, back-links, notability) are defined in `second-brain/references/quality.md`.

## Common Pitfalls

- **No date** — if date is unknown, use ingestion date and note "approximate"
- **Missing attendees** — if not stated, do not guess who was there. Mark as "not specified."
- **Paraphrasing decisions** — use exact wording from notes. "Decided X" not "they talked about X"
- **Over-enrichment** — not every attendee needs a full dossier. Use judgment.
- **Broken attendee slugs** — verify slug resolution before creating links
- **No action items listed** — do not fabricate them. Note "no action items recorded."

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Date and topic clear
- [ ] Attendees identified and resolved
- [ ] Decisions extracted with citations
- [ ] Action items recorded (or noted as absent)
- [ ] Attendee pages updated if regular contacts
- [ ] Personal relevance section present
- [ ] Quality conventions followed (citations, back-links, notability — see second-brain/references/quality.md)
- [ ] Timeline entry added for this meeting
