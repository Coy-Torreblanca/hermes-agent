# Refile Script Pattern — Python Heredoc

Use this pattern for bulk org file operations (inbox → tasks.org, inbox → personal.org) to avoid the `read_file` line-number prefix corruption pitfall.

## Why

`read_file` returns lines in `NNN|CONTENT` format. Extracting and writing those lines to another file embeds the prefixes. The pattern below reads files directly via `open()` and writes via `open(..., 'w')` — no line numbers, no corruption.

## Pattern

```bash
python3 << 'PYEOF'
import re, uuid

# ── Read source files directly ──
with open('/data/syncthing/Sync/org/inbox.org') as f:
    inbox = f.read()
with open('/data/syncthing/Sync/org/work/tasks.org') as f:
    tasks = f.read()
with open('/data/syncthing/Sync/org/personal/personal.org') as f:
    personal = f.read()

# ── Extract items from inbox ──
# Work items come before '* PersonalInbox' header
work_match = re.search(r'(\*\* TODO.*?)(?=\* PersonalInbox)', inbox, re.DOTALL)
work_item = work_match.group(1).rstrip() if work_match else ""

# Personal items come after '* PersonalInbox' header
personal_match = re.search(r'\* PersonalInbox\n(.*)', inbox, re.DOTALL)
personal_items = personal_match.group(1).rstrip() if personal_match else ""

# ── Transform TODO → STORY (work items) ──
work_story = re.sub(r'\*\* TODO', '** STORY', work_item, count=1)

# Replace properties drawer with full metadata
new_props = f""":PROPERTIES:
:ID:       {uuid.uuid4().hex[:32].upper()}
:CREATED:  [YYYY-MM-DD Day HH:MM]
:SPRINT:   backlog
:POINTS:   N
:VALUE:    High
:GOAL:     ...
:END:"""

work_story = re.sub(r':PROPERTIES:.*?:END:', new_props, work_story, flags=re.DOTALL)

# ── Transform personal items ──
items = re.split(r'\n(?=\*\* TODO)', personal_items)
transformed = []

for item in items:
    item = item.strip()
    if not item:
        continue
    
    # Build metadata for this item
    new_props = f""":PROPERTIES:
:ID:       {uuid.uuid4().hex[:32].upper()}
:CREATED:  [YYYY-MM-DD Day]
:SPRINT:   4
:POINTS:   N
:VALUE:    Medium
:GOAL:     ...
:END:"""
    
    # Replace existing or add new properties drawer
    if ':PROPERTIES:' in item:
        item = re.sub(r':PROPERTIES:.*?:END:', new_props, item, flags=re.DOTALL)
    else:
        headline_end = item.index('\n') if '\n' in item else len(item)
        item = item[:headline_end] + '\n' + new_props + item[headline_end:]
    
    transformed.append(item)

# ── Append to destination files ──
tasks_new = tasks.rstrip() + '\n\n' + work_story + '\n'
with open('/data/syncthing/Sync/org/work/tasks.org', 'w') as f:
    f.write(tasks_new)

personal_new = personal.rstrip() + '\n\n' + '\n\n'.join(transformed) + '\n'
with open('/data/syncthing/Sync/org/personal/personal.org', 'w') as f:
    f.write(personal_new)

# ── Clean inbox.org ──
cleaned = re.sub(
    r'(\* Inbox\n).*?(\n\* PersonalInbox)',
    r'\1\2',
    inbox,
    flags=re.DOTALL
)
cleaned = re.sub(r'(\* PersonalInbox\n).*', r'\1', cleaned, flags=re.DOTALL)
with open('/data/syncthing/Sync/org/inbox.org', 'w') as f:
    f.write(cleaned)

# ── Verify ──
print("Last 5 lines of tasks.org:")
with open('/data/syncthing/Sync/org/work/tasks.org') as f:
    for l in f.readlines()[-5:]:
        print(repr(l.rstrip()))
print("\nLast 5 lines of personal.org:")
with open('/data/syncthing/Sync/org/personal/personal.org') as f:
    for l in f.readlines()[-5:]:
        print(repr(l.rstrip()))
print("\ninbox.org:")
with open('/data/syncthing/Sync/org/inbox.org') as f:
    print(f.read())
PYEOF
```

## Key Rules

1. **Never use `read_file` → extract → write.** The line number prefixes (`NNN|`) will corrupt the destination file.
2. **Always use `open()` directly** inside a Python heredoc for bulk moves.
3. **Verify after writing** — read back the last few lines of each destination file.
4. **Use `re.DOTALL`** for properties drawer replacement (`:PROPERTIES:.*?:END:`).
5. **Propose before executing.** Present the exact org text to Coy, get approval, then run the script.
