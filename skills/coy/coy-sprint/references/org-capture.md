# Org Capture (absorbed from org-capture skill)

Append a `** TODO` entry to `/data/syncthing/Sync/org/inbox.org`.
Maker-mode only — no POINTS, VALUE, or SPRINT. Triage handles routing later.

## When to Use

- Coy says "add a todo", "add to my list", "I need to remember to..."
- Coy fires off rapid items — capture each as its own TODO
- NOT for time-based reminders (those go to `reminder-db`)

## Format

```
** TODO Title here
Body text — enough context for Coy to understand during later triage.
Multi-line body is fine. Keep it flat (no sub-headings in capture mode).
```

## Rules

1. **Append to end of file** — all captures go to one inbox. Triage decides destination.
2. **Body context required** — bare headline without body is useless in triage.
3. **No metadata** — no POINTS, VALUE, SPRINT, tags. That's triage's job.
4. **Don't read inbox.org first** — just append. This is capture, not review.
5. **Confirm with Coy before writing** unless he's clearly in rapid-fire capture mode.

## Implementation

```bash
printf '\n** TODO Title here\nBody text here\n' >> /data/syncthing/Sync/org/inbox.org
```

Single command, zero reads, appends a blank line + the TODO.

## Pitfalls

- **Whitespace in titles** — wrap the printf format string in double quotes, not single, so variables expand. Escape internal double quotes.
- **Not for reminders** — time-based alerts use `reminder-db`. This is for task capture only.
- **Syncthing sync** — changes appear on the Mac within seconds. No manual sync needed.
