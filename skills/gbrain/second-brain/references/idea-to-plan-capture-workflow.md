# Idea-to-Plan Capture Workflow (gbrain + Org)

> Capturing an idea for a future system improvement requires two simultaneous writes: a gbrain concept page to preserve the full thinking, and an org story to commit it to a backlog. Neither alone is sufficient. The gbrain page holds the depth; the org story holds the accountability.

## When to Use

- User says "document this for later" or "create a task for this idea"
- User proposes a system improvement during conversation
- User reflects on a design tension and you want to save the thinking
- Any idea that needs both **durable knowledge** (the thinking) and **actionable commitment** (a task)

## Workflow

### Phase 1: Capture the Thinking (gbrain)

Create a gbrain concept page that preserves the full reasoning:

1. **Deterministic slug**: `concepts/<idea-slug>` (use hyphens, stay under 60 chars)
2. **Executive summary**: One-paragraph what and why
3. **Problem statement**: What was observed, the concrete trigger
4. **Options / solutions**: Numbered list with trade-offs per option
5. **Evaluation criteria**: How to know if the idea worked
6. **See Also**: Cross-link to related concept pages, plugin docs, requirements pages
7. **Timeline entry**: The conversation that spawned this, user's exact words preserved
8. **Back-links**: Link from this page to all related pages (and vice versa)

### Phase 2: Create the Org Story

Create a story under the appropriate EPIC with a body that tells the user how to surface gbrain context:

1. **Use `--create-todo`** with `destination: "<EPIC> [ICEBOX]"` and `keyword: "STORY"`
2. **GOAL**: A one-sentence definition of done
3. **Points**: Estimate realistically (1-3 for prompt edits, 3-5 for code changes)
4. **Body**: Must include language like: "When reviewing this task: ask Mochi to surface gbrain examples of [faulty behavior] and recommendations for resolution. See: gbrain concepts/<idea-slug>."
5. **SPRINT**: Backlog (unless explicitly assigned)
6. **Verify**: `--children-of "<EPIC>"` to confirm insertion

### Phase 3: Connect Both

The gbrain page and org story form a bidirectional pair:
- The org story's body references the gbrain slug so Coy knows where to look
- The gbrain page's See Also section links to the EPIC (via text reference)
- When Coy asks to "surface the plan for X", load the gbrain concept page

## Example

From 2026-05-17 session:

**gbrain page:** `concepts/signal-detector-improvement-plan`
- Problem: Signal Detector fires false positives for org-mode captures
- 5 proposed solutions ranked by investment level
- Concrete examples from the session documented
- Evaluation criteria for success

**Org story:** `** STORY Improve Signal Detector — reduce false positives` under `* EPIC Personal AI v2 [ICEBOX]`
- GOAL: "Signal Detector stops firing false positives for org-mode content while maintaining genuine write signal detection"
- Body: "When reviewing this task: ask Mochi to surface gbrain examples of faulty Signal Detector behavior..."
- Points: 3, SPRINT: backlog

## Pitfalls

- **Don't skip the gbrain page.** A bare org story with just a title and body loses the depth of analysis. The user won't remember the 5 options, the trade-offs, or the concrete examples months later.
- **Don't skip the org story.** A gbrain concept page with no task attached is an aspiration that never gets scheduled. The backlog is where ideas become commitments.
- **Make the body navigable.** The body must include explicit language telling Coy to ask Mochi to surface gbrain context. Otherwise he won't know the brain page exists, or what to ask for.
- **Icebox is correct for planned improvements.** Unless Coy explicitly assigns a sprint number, planned improvements go to [ICEBOX] under the appropriate EPIC. Don't guess the sprint.
- **Verify the EPIC exists.** Use `--find-epic "<EPIC name>"` before creating. If it doesn't exist, ask Coy where to put it. Don't create orphan stories.
