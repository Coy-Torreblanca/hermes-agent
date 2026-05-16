---
name: gbrain-publish
description: "Share brain pages as shareable links, summaries, or formatted outputs. Generates clean extracts from gbrain pages for sharing with others — without exposing the full brain structure."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, publishing, sharing, second-brain]
    related_skills: [second-brain, gbrain-query, gbrain-page-writer]
---

# GBrain Publish

Share brain pages as shareable summaries, extracts, or formatted outputs. Generates clean, context-appropriate versions of brain content for sharing with others — without exposing internal brain structure (slugs, link types, internal notes).

## When to Use

- User says "share this brain page", "export this for someone", "generate a summary"
- User wants to send someone a clean version of a person/company/project profile
- User wants to reference brain content in a document, email, or message
- User asks "what does my brain say about X" — offer to generate a shareable version
- Cron job output needs to be in a human-readable format

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Identify Target Page

Find the page the user wants to share:

```
mcp_gbrain_resolve_slugs(partial="<name>")
mcp_gbrain_get_page(slug="<slug>")
```

If the user did not specify, ask which page and what format.

### Step 3: Choose Output Format

| Format | Use Case | Includes |
|--------|----------|----------|
| **Summary** | Quick share in chat/message | Executive summary + key facts only |
| **Profile** | Sharing about a person/company | Clean person/company template, no internal fields |
| **Briefing** | Sending context to someone | What matters most + key timeline events |
| **Markdown** | Export to document | Full cleaned content, suitable for pasting |
| **Report** | Cron job output or scheduled delivery | Structured data + formatted output |

### Step 4: Sanitize Content

Remove or replace internal brain content:

| Remove | Replace With |
|--------|--------------|
| `[Source: ...]` citations | Clean prose (or keep if useful to the recipient) |
| Brain-internal slugs | Human-readable names |
| `(@people/slug)` links | Plain text `[Name]` |
| Link types (`references`, `works_at`) | Natural language ("works at", "mentioned in") |
| Open threads | Only include if relevant to the recipient |
| Internal notes or assessments marked `internal` | Omit entirely |
| Friction log entries | Omit |

### Step 5: Build Output

**Summary format:**
```
# {Title}

{Executive summary}

## Key Facts
- {Fact 1}
- {Fact 2}
- {Fact 3}

{Generated YYYY-MM-DD from personal knowledge base}
```

**Profile format (person):**
```
# {Name}

{Executive summary}

**Relationship:** {how you know them}
**Role:** {current position}
**Key context:** {important background}

{Optional: key traits or observations}

---

*Generated YYYY-MM-DD*
```

**Briefing format:**
```
# Briefing: {Topic}

## Context
{Why this matters right now}

## Key Points
{What someone needs to know}

## Recent Developments
{Recent timeline entries, cleaned}

---

*Generated YYYY-MM-DD from personal notes*
```

### Step 6: Deliver Output

Send the output in the user's preferred channel:

- **In chat:** Send the formatted text directly
- **As file:** Write to file and share path
- **Via email:** Compose email with the content (requires himalaya skill)

### Step 7: Log Publication

```
mcp_gbrain_add_timeline_entry(
    slug="<published_page>",
    date="YYYY-MM-DD",
    summary="Published: {format} version of {title}",
    detail="Format: {summary/profile/briefing}. Recipient/context: {how it was used}."
)
```

## Privacy & Safety Rules

- **No internal data in external shares** — never expose slugs, link types, internal notes, friction logs, or tentative assessments
- **No fabrication** — only include facts that exist in the brain. Do not fill gaps with assumptions.
- **Recipient awareness** — if sharing about a person, consider: would they want this shared? Use judgment.
- **Attribution** — do not attribute assessments to specific conversations unless the user approves

## Common Pitfalls

- **Internal data leak** — double-check for hidden internal fields before sharing
- **Over-sanitization** — removing too much context makes the output useless. Balance.
- **Fabrication** — when converting structured data to prose, do not add facts that were not in the brain
- **Stale data** — check the timeline for recency. Flag if data is old.
- **No delivery confirmation** — if sending via email, confirm the message was sent

## Verification Checklist

- [ ] Target page identified and read
- [ ] Output format chosen and appropriate for the use case
- [ ] Internal data sanitized (slugs, link types, internal notes removed)
- [ ] Output is accurate to the brain content (no fabrication)
- [ ] Output delivered to the user or target channel
- [ ] Timeline entry added for publication event
