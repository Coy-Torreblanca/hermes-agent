---
name: evangelism-tracking
description: Track spiritual touchpoints (verses, conversations, milestones) with non-believers using gbrain person pages and timeline entries. Load when Coy is sharing verses, having spiritual conversations, or tracking someone's journey toward faith.
---

# Evangelism Tracking

Track spiritual engagement with people Coy is sharing the gospel with. Each person gets a gbrain page with faith posture and history; each touchpoint gets a timeline entry; feedback is logged separately and drives future verse selection.

## Core Workflow

### 1. Person Context (gbrain)
- Ensure the person has a gbrain page (`people/<name>`) with: spiritual posture (believer/non-believer/open/resistant), relationship, relevant life context, and any verse history
- If page is sparse, search gbrain broadly — related family pages, trip pages, journal entries may hold context

### 2. Verse Selection
- Read the person's gbrain page AND timeline BEFORE suggesting a verse
- For someone dipping their toes: warm and invitational over dense or confrontational. Clear promise language over proverbial density. Jesus's own words often land well.
- Surface 2-4 options with rationales; let Coy choose
- The person's actual feedback (not theological instinct) should drive the next pick

### 3. Logging Touchpoints
For each verse or spiritual conversation:
```
mcp_gbrain_add_timeline_entry
  slug = people/<name>
  date = <date sent>
  summary = "Daily verse sent: <reference>"
  detail = "<passage text> — context for why this verse was chosen"
  source = "hermes-agent"
```

### 4. Logging Feedback
When the person reacts, add a SEPARATE timeline entry (same date):
```
summary = "Feedback: <key takeaway>"
detail = "<full feedback> — what this tells us about verse preference going forward"
```

### 5. Using Feedback
Before suggesting the next verse, re-read the timeline. The feedback trail tells you what register to stay in, what to avoid, and what themes resonate.

## Critical Pitfalls

### Verify before logging
**Never assume a suggested verse was actually sent.** If Coy says "I sent him something from Isaiah 65," ask what specific passage before logging. If you log a suggestion as fact, you'll have to add noisy "CORRECTED:" entries later — gbrain has no timeline-delete tool.

### gbrain has no timeline-delete
If you log an incorrect timeline entry, the fix is to add a new entry with `summary = "CORRECTED: <correct data>"` and note the discrepancy in `detail`. There is no delete-timeline-entry tool.

### "Note this" means gbrain
When Coy says "note this" or "track these," he expects the data to land in gbrain, not just be acknowledged in chat. He will follow up with "Did you add this to his gbrain?" — save yourself the check-back.

## Verse Selection Principles

For someone at the "interested but not committed" stage:
- **Warm over confrontational** — "God has plans for you" over "repent and believe"
- **Accessible over dense** — simple promise language over prophetic/poetic density
- **Jesus's voice** — Matthew 11:28-30, John's gospel invitations
- **Track the register** — if they respond to one kind, stay in that neighborhood

For someone further along or already believing, adjust accordingly.
