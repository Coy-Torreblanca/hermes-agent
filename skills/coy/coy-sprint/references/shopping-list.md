# Shopping List Management (absorbed from shopping-list skill)

Manage `/data/syncthing/Sync/org/personal/shopping.org` — a running list of items to buy on Amazon.

## When to Use

- User says "add X to my shopping list" or "add X to the Amazon list"
- User says "remove X from my shopping list" or "I bought X"
- User says "what's on my shopping list?"
- User mentions needing to buy something (capture it — don't let it get lost)

## File

```
/data/syncthing/Sync/org/personal/shopping.org
```

## Format

Items are bare `** TODO` entries (no sprint metadata — this is not a sprint board):

```
** TODO Item description :tag:
:PROPERTIES:
:CREATED:  [YYYY-MM-DD Day HH:MM]
:GOAL:     Why we need this / what it's for
:END:
```

- No `:SPRINT:`, `:POINTS:`, or `:VALUE:` — shopping items aren't sprinted
- No `:ID:` — let Emacs auto-generate on next touch
- Tags are optional but encouraged (e.g., `:car:`, `:office:`, `:home:`)

## Commands

### Add an item

1. Read the current file to see what's there
2. Append the new `** TODO` block at the end
3. Set `:CREATED:` and `:GOAL:`

### Remove an item (purchased)

1. `search_files` for the item text to confirm it exists
2. Use `terminal` + Python to remove the heading + property drawer block
3. Do NOT just delete the heading line — remove the full block including properties

### View the list

```
read_file /data/syncthing/Sync/org/personal/shopping.org
```

Present as a simple bulleted list.

## Pitfalls

- Do NOT add sprint metadata (SPRINT, POINTS, VALUE) — this is not a sprint item
- Do NOT add `:ID:` — let Emacs generate on next file touch
- When removing, remove the full block (heading + properties), not just the heading line
- This is a running list, not a todo tracker — items stay until purchased, then removed
