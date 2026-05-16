#!/usr/bin/env python3
"""
org_query.py — Structured read/write for org-mode files.
Eliminates regex fragility in agent ↔ org-mode interactions.

Usage:
  # Read operations (file as first arg)
  org_query.py tasks.org --summary           # Dashboard: STARTED, NEXT, sprint load
  org_query.py tasks.org --find-active        # All active tasks with parent EPIC chain
  org_query.py tasks.org --find-epic "30ai"   # Full subtree under matching EPIC
  org_query.py tasks.org --sprint 4           # All items in sprint 4
  org_query.py tasks.org --insert-point "Second Brain"  # Where to insert child under EPIC
  org_query.py tasks.org --children-of "Second Brain"    # Direct children of heading
  org_query.py tasks.org --heading "Four-Stage RAG"      # Find heading by regex
  org_query.py tasks.org --stats              # Point totals, velocity, capacity
  org_query.py tasks.org --validate           # Check for WIP violations, orphans, etc.
  org_query.py tasks.org --verify-line 42     # Read back a specific line (raw, no dedup)

  # Write operations (no file arg needed)
  org_query.py --create-todo '{"title":"...","body":"..."}'     # Deterministic create
  org_query.py --dry-run '{"title":"...","body":"..."}'         # Preview without writing

Output: JSON to stdout. Exit codes: 0 = success, 1 = error.
"""

import json
import re
import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─── Constants ──────────────────────────────────────────────────────────────

INBOX_PATH = '/data/syncthing/Sync/org/inbox.org'
TASKS_PATH = '/data/syncthing/Sync/org/work/tasks.org'
PERSONAL_PATH = '/data/syncthing/Sync/org/personal/personal.org'

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Only these fields get written to inbox (POINTS/VALUE/GOAL are triage's job)
INBOX_ALLOWED_FIELDS = {'title', 'body', 'priority', 'tags', 'keyword', 'sprint'}


# ─── Utility ────────────────────────────────────────────────────────────────

def make_uuid() -> str:
    """Generate a deterministic-format UUID matching Emacs org-id-get-create format."""
    return uuid_lib.uuid4().hex[:16].upper()


def make_created_timestamp() -> str:
    """Generate org-mode timestamp: [2026-05-14 Thu]"""
    now = datetime.now()
    return now.strftime(f'[%Y-%m-%d {WEEKDAYS[now.weekday()]}]')


def value_from_priority(priority: Optional[str]) -> Optional[str]:
    """[DEPRECATED — not called automatically]
    Utility to map priority tag to a VALUE, if desired.
    Priorities and VALUE are orthogonal axes in Emacs. This function exists for
    callers who explicitly want this mapping, but --create-todo no longer uses it.
    Canonical values (from Emacs org-global-properties VALUE_ALL): Essential, Important, Nice-to-have.
    Priority mapping: A→Essential, B→Important, C→Nice-to-have.
    """
    mapping = {'A': 'Essential', 'B': 'Important', 'C': 'Nice-to-have'}
    return mapping.get(priority) if priority else None


def infer_priority_tag(params: dict) -> str:
    """Build priority tag string from params."""
    priority = params.get('priority')
    if priority in ('A', 'B', 'C'):
        return f' [#{priority}]'
    return ''


def infer_tags(params: dict) -> str:
    """Build trailing tag string from params."""
    tags = params.get('tags', [])
    if tags:
        return ' :' + ':'.join(tags) + ':'
    return ''


def format_branch_name(type_name: str, title: str) -> str:
    """Convert type and title into a git-friendly branch name.
    Matches Emacs my/format-branch-name from common-org-config.el.
    Examples: feature/add-login-page, bugfix/fix-null-pointer
    """
    type_str = type_name.lower().strip() if type_name else 'feature'
    title_str = title.lower().strip() if title else ''
    # Replace non-alphanumeric characters with hyphens
    slugged = re.sub(r'[^a-z0-9]+', '-', title_str)
    # Clean up double hyphens
    cleaned = re.sub(r'-+', '-', slugged)
    # Trim leading/trailing hyphens
    trimmed = cleaned.strip('-')
    if not trimmed:
        trimmed = 'new-task'
    return f'{type_str}/{trimmed}'


def make_deterministic_block(params: dict, stars_override: str = None) -> tuple:
    """
    Generate a deterministic org-mode block with fixed property order.
    Property order: ID → CREATED → SPRINT → POINTS → VALUE → GOAL → TYPE → BRANCH → REPO

    stars_override: if provided, use this for the heading stars instead of
    auto-detecting from destination. Inbox uses '*' (level 1, matching Emacs
    capture templates). Under-EPIC insertion calculates from EPIC level.

    Returns (block_string, resolved_params) where resolved_params
    contains all auto-derived values (ID, CREATED, VALUE, GOAL).
    Callers use resolved_params — never duplicate the derivation logic.
    """
    title = params.get('title', 'Untitled')
    body = params.get('body', '')
    keyword = params.get('keyword', 'TODO')
    priority_tag = infer_priority_tag(params)
    tags_str = infer_tags(params)
    sprint = params.get('sprint', 'backlog')
    destination = params.get('destination', 'inbox') or 'inbox'
    is_inbox = destination.lower() == 'inbox'

    # Always generate these
    todo_id = make_uuid()
    created = make_created_timestamp()

    # Resolve VALUE — only include if explicitly provided.
    # VALUE is a triage-time property (set during refile for EPIC/STORY items,
    # per Emacs common-org-config.el lines 289-292). Never auto-derive from
    # priority — they are orthogonal axes.
    resolved_value = params.get('value')

    # Resolve GOAL — only include if explicitly provided.
    # GOAL is prompted during refile for EPIC/STORY items (common-org-config.el
    # lines 295-296). Quick inbox and task capture never set it.
    resolved_goal = params.get('goal')

    # Resolve TYPE, BRANCH, REPO — code change properties.
    # Matches Emacs capture template "d: Dev: Code Change" (common-org-config.el lines 190-205)
    # and refile metadata prompt (lines 274-281).
    # TYPE: feature, bugfix, hotfix, or chore
    # BRANCH: auto-generated from TYPE + title when TYPE is provided
    # REPO: optional repo link
    resolved_type = params.get('type')
    resolved_repo = params.get('repo')
    resolved_branch = params.get('branch')
    if resolved_type and not resolved_branch:
        resolved_branch = format_branch_name(resolved_type, title)

    # Resolved params — never duplicate this derivation elsewhere
    resolved_params = {
        'title': title,
        'body': body,
        'keyword': keyword,
        'priority': params.get('priority'),
        'tags': params.get('tags', []),
        'sprint': sprint,
        'destination': destination,
        'is_inbox': is_inbox,
        'id': todo_id,
        'created': created,
        'value': resolved_value,
        'goal': resolved_goal,
        'points': params.get('points'),
        'type': resolved_type,
        'branch': resolved_branch,
        'repo': resolved_repo,
    }

    # Build properties drawer — fixed order
    props = []
    props.append(f':ID:       {todo_id}')
    props.append(f':CREATED:  {created}')
    props.append(f':SPRINT:   {sprint}')

    # POINTS: only for non-inbox destinations
    if not is_inbox and params.get('points') is not None:
        props.append(f':POINTS:   {params["points"]}')

    # VALUE: only for non-inbox destinations
    if not is_inbox and resolved_value:
        props.append(f':VALUE:    {resolved_value}')

    # GOAL: only for non-inbox destinations
    if not is_inbox and resolved_goal:
        props.append(f':GOAL:     {resolved_goal}')

    # TYPE/BRANCH/REPO: code change properties (non-inbox only)
    if resolved_type:
        props.append(f':TYPE:     {resolved_type}')
        if resolved_branch:
            props.append(f':BRANCH:   {resolved_branch}')
    if resolved_repo:
        props.append(f':REPO:     {resolved_repo}')

    # Build the block
    heading = f'{keyword}{priority_tag} {title}{tags_str}'
    # Emacs capture templates use level-1 headings (*) for all captures
    # Inbox mode: * TODO (matches Emacs "i" quick capture)
    # Under-EPIC mode: stars_override from insert_point (e.g. ** for EPIC+1)
    stars = stars_override if stars_override else ('**' if not is_inbox else '*')
    block_lines = [f'{stars} {heading}']
    block_lines.append(':PROPERTIES:')
    block_lines.extend(props)
    block_lines.append(':END:')

    if body:
        block_lines.append('')
        block_lines.append(body)

    block = '\n'.join(block_lines) + '\n'
    return block, resolved_params


def resolve_destination(destination: str) -> str:
    """Resolve a destination string to an absolute filepath."""
    dest = destination.lower().strip() if destination else 'inbox'

    if dest == 'inbox':
        return INBOX_PATH
    if dest == 'tasks' or dest == 'work':
        return TASKS_PATH
    if dest == 'personal':
        return PERSONAL_PATH

    # If it's already an absolute path, use it
    if dest.startswith('/'):
        return dest

    # Otherwise, treat as an EPIC name in tasks.org
    return TASKS_PATH


# ─── Write Operations ───────────────────────────────────────────────────────

def verify_line(filepath: str, line_num: int) -> dict:
    """
    Read back a specific line using raw open(), bypassing read_file dedup.
    Returns {'line': N, 'content': '...', 'total_lines': N}.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {'error': f'File not found: {filepath}'}

    total = len(lines)
    if line_num < 1 or line_num > total:
        return {'error': f'Line {line_num} out of range (1-{total})'}

    return {
        'line': line_num,
        'content': lines[line_num - 1].rstrip('\n'),
        'total_lines': total,
    }


def insert_at_line(filepath: str, insert_after: int, block: str) -> dict:
    """
    Insert block after a specific line number using raw file I/O.
    Returns {'inserted_at': N, 'total_lines': N, 'confirm': '...'}.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {'error': f'File not found: {filepath}'}

    if insert_after < 0 or insert_after > len(lines):
        return {'error': f'Insert position {insert_after} out of range (0-{len(lines)})'}

    # Insert block at position (0-indexed, after insert_after - 1)
    indent = '\n'
    block_lines = block.split('\n')
    inserted = [l + '\n' if not l.endswith('\n') else l for l in block_lines]
    insert_pos = insert_after  # 0-indexed position

    lines[insert_pos:insert_pos] = inserted

    with open(filepath, 'w') as f:
        f.writelines(lines)

    # Post-write verification
    new_total = len(lines)
    confirm_start = max(0, insert_pos - 1)
    confirm_end = min(new_total, insert_pos + len(inserted) + 1)
    confirm_lines = lines[confirm_start:confirm_end]

    return {
        'inserted_at': insert_pos + 1,
        'total_lines': new_total,
        'confirm': ''.join(confirm_lines).strip(),
    }


def create_todo(filepath: str, params: dict, dry_run: bool = False) -> dict:
    """
    Main entry point for deterministic todo creation.
    Validates, generates block, writes or dry-runs.
    """
    block, resolved = make_deterministic_block(params)
    destination = resolved['destination']
    is_inbox = resolved['is_inbox']
    todo_id = resolved['id']

    if dry_run:
        return {
            'dry_run': True,
            'destination': filepath,
            'block': block.strip(),
            'params': resolved,
        }

    # If inbox destination: simple append (zero risk)
    if is_inbox:
        try:
            with open(filepath, 'a') as f:
                f.write('\n')
                f.write(block)
        except FileNotFoundError:
            return {'error': f'File not found: {filepath}'}

        # Post-write verification
        verify = verify_line(filepath, 1)
        return {
            'success': True,
            'action': 'append',
            'destination': filepath,
            'todo_id': todo_id,
            'title': resolved['title'],
            'params': resolved,
            'verification': verify,
        }

    # Under-EPIC destination: insert via file I/O
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return {'error': f'File not found: {filepath}'}

    from io import StringIO
    headings = parse_org(filepath)

    epic_name = destination
    insert_info = insert_point(headings, epic_name)
    if 'error' in insert_info:
        return insert_info

    # Regenerate block with correct stars for EPIC level
    block, resolved = make_deterministic_block(params, stars_override=insert_info['stars'])

    insert_after = insert_info['insert_after_line']
    result = insert_at_line(filepath, insert_after, block)

    if 'error' in result:
        return result

    return {
        'success': True,
        'action': 'insert_under_epic',
        'destination': filepath,
        'epic': epic_name,
        'insert_after_line': insert_after,
        'todo_id': todo_id,
        'title': resolved['title'],
        'params': resolved,
        'result': result,
    }


# ─── Existing Parsing/Query Functions ───────────────────────────────────────

def parse_org(filepath: str) -> list[dict]:
    """Parse an org-mode file into a list of heading trees."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    headings = []
    stack = []  # (level, heading_dict) ancestry

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Detect heading: starts with * followed by space
        heading_match = re.match(r'^(\*+)\s+(STORY-STARTED|STORY-NEXT|STORY-DONE|STORY-WAITING|STARTED|NEXT|DONE|CANCELLED|STORY|WAITING|EPIC|TODO)?\s*(\[#(A|B|C)\])?\s*(.*)', line)

        if heading_match:
            stars = heading_match.group(1)
            level = len(stars)
            keyword = heading_match.group(2) or 'TODO'
            priority = heading_match.group(4)  # A, B, C
            title_and_tags = heading_match.group(5) or ''

            # Extract tags from end of heading: :tag1:tag2:
            tags = []
            tag_match = re.search(r'\s:(.+?):$', title_and_tags)
            if tag_match:
                tags = tag_match.group(1).split(':')
                title = title_and_tags[:tag_match.start()].strip()
            else:
                title = title_and_tags.strip()

            heading = {
                'level': level,
                'keyword': keyword,
                'priority': priority,
                'title': title,
                'tags': tags,
                'properties': {},
                'body': [],
                'children': [],
                'line_start': i + 1,  # 1-indexed
            }

            i += 1

            # Parse property drawer (must immediately follow heading)
            if i < len(lines) and lines[i].strip() == ':PROPERTIES:':
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(':END:'):
                    prop_match = re.match(r'^:(\w+):\s+(.*)', lines[i].strip())
                    if prop_match:
                        heading['properties'][prop_match.group(1).upper()] = prop_match.group(2).strip()
                    i += 1
                i += 1  # Skip :END:

            # Parse body (lines until next heading or EOF)
            while i < len(lines):
                line = lines[i].rstrip('\n')
                if re.match(r'^\*+\s', line):
                    break
                heading['body'].append(line)
                i += 1

            heading['body_text'] = '\n'.join(heading['body']).strip()
            heading['line_end'] = i  # Line where next section starts (or EOF)

            # Place in tree
            # Pop from stack until we find a parent (lower level)
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                parent_level, parent_heading = stack[-1]
                parent_heading['children'].append(heading)
                heading['parent_title'] = parent_heading['title']
                heading['parent_keyword'] = parent_heading['keyword']
            else:
                headings.append(heading)

            stack.append((level, heading))
        else:
            i += 1

    return headings


def find_heading(headings: list[dict], pattern: str, partial: bool = True) -> Optional[dict]:
    """Find a heading by regex or partial title match."""
    for h in headings:
        if partial and pattern.lower() in h['title'].lower():
            return h
        if re.search(pattern, h['title'], re.IGNORECASE):
            return h
        result = find_heading(h['children'], pattern, partial)
        if result:
            return result
    return None


def find_epic(headings: list[dict], name: str) -> Optional[dict]:
    """Find an EPIC by name (partial match)."""
    for h in headings:
        if h['keyword'] in ('EPIC',) and name.lower() in h['title'].lower():
            return h
        result = find_epic(h['children'], name)
        if result:
            return result
    return None


def find_all_matching(headings: list[dict], pattern: str, keyword: str = None) -> list[dict]:
    """Find all headings matching pattern, optionally filtered by keyword."""
    results = []
    for h in headings:
        if pattern.lower() in h['title'].lower():
            if keyword is None or h['keyword'] == keyword:
                results.append(h)
        results.extend(find_all_matching(h['children'], pattern, keyword))
    return results


def find_active(headings: list[dict]) -> list[dict]:
    """Find all STARTED, NEXT, STORY-STARTED, STORY-NEXT tasks."""
    active_keywords = {'STARTED', 'NEXT', 'STORY-STARTED', 'STORY-NEXT'}
    results = []
    for h in headings:
        if h['keyword'] in active_keywords:
            results.append(h)
        results.extend(find_active(h['children']))
    return results


def get_ancestor_chain(headings: list[dict], target_title: str) -> list[str]:
    """Get the EPIC > STORY chain for a heading."""
    result = find_heading(headings, target_title)
    if not result:
        return []
    chain = [result['title']]
    current = result
    def walk_up(haystack, target, path):
        for h in haystack:
            if h['title'] == target['title']:
                return [h['title']] + path
            if h['children']:
                r = walk_up(h['children'], target, [h['title']] + path)
                if r:
                    return r
        return None
    return walk_up(headings, result, []) or []


def sprint_items(headings: list[dict], sprint_num: int) -> list[dict]:
    """Find all items with SPRINT property = sprint_num."""
    results = []
    sprint_str = str(sprint_num)
    for h in headings:
        if h['properties'].get('SPRINT') == sprint_str:
            results.append(h)
        results.extend(sprint_items(h['children'], sprint_num))
    return results


def sprint_summary(headings: list[dict], sprint_num: int) -> dict:
    """Dashboard summary: active, next, sprint load, velocity."""
    items = sprint_items(headings, sprint_num)
    active = find_active(headings)

    total_points = sum(int(h['properties'].get('POINTS', '0')) for h in items)
    completed_points = sum(int(h['properties'].get('POINTS', '0')) for h in items if h['keyword'] in ('DONE', 'STORY-DONE'))

    return {
        'sprint': sprint_num,
        'total_items': len(items),
        'total_points_committed': total_points,
        'points_completed': completed_points,
        'points_remaining': total_points - completed_points,
        'capacity': 16,
        'capacity_used_pct': round(total_points / 16 * 100, 1),
        'active_tasks': [
            {
                'title': h['title'],
                'keyword': h['keyword'],
                'points': h['properties'].get('POINTS', '0'),
                'value': h['properties'].get('VALUE', ''),
                'epic': h.get('parent_title', '(top-level)'),
                'line': h['line_start'],
            }
            for h in active
        ],
        'sprint_items': [
            {
                'title': h['title'],
                'keyword': h['keyword'],
                'points': h['properties'].get('POINTS', '0'),
                'value': h['properties'].get('VALUE', ''),
                'line': h['line_start'],
            }
            for h in items
        ],
    }


def insert_point(headings: list[dict], epic_name: str) -> dict:
    """Find where to insert a new child under an EPIC."""
    epic = find_epic(headings, epic_name)
    if not epic:
        return {'error': f'EPIC containing "{epic_name}" not found'}

    if epic['children']:
        last_child = epic['children'][-1]
        return {
            'epic': epic['title'],
            'epic_line': epic['line_start'],
            'insert_after_line': last_child['line_end'] - 1,
            'last_child': last_child['title'],
            'level': epic['level'] + 1,
            'stars': '*' * (epic['level'] + 1),
        }
    else:
        return {
            'epic': epic['title'],
            'epic_line': epic['line_start'],
            'insert_after_line': epic['line_start'] + len(epic['properties']) + 2,
            'last_child': None,
            'level': epic['level'] + 1,
            'stars': '*' * (epic['level'] + 1),
        }


def children_of(headings: list[dict], name: str) -> list[dict]:
    """Get direct children of a heading."""
    h = find_heading(headings, name)
    if not h:
        return []
    return [
        {
            'title': c['title'],
            'keyword': c['keyword'],
            'points': c['properties'].get('POINTS', '0'),
            'sprint': c['properties'].get('SPRINT', 'backlog'),
            'line': c['line_start'],
        }
        for c in h['children']
    ]


def validate(headings: list[dict]) -> dict:
    """Check for rule violations."""
    issues = []
    warnings = []

    # Rule 1: Single WIP — only one STARTED
    active = find_active(headings)
    started = [h for h in active if h['keyword'] in ('STARTED', 'STORY-STARTED')]
    if len(started) > 1:
        issues.append({
            'rule': 'SINGLE WIP',
            'message': f'{len(started)} tasks in STARTED state (max 1)',
            'tasks': [h['title'] for h in started],
        })

    # Check for top-level TODOs without STORY parent
    def check_todo_parent(hs, parent_keyword=None):
        for h in hs:
            if h['keyword'] == 'TODO' and parent_keyword not in ('STORY', 'STORY-STARTED', 'STORY-NEXT', 'STORY-DONE', 'STORY-WAITING'):
                issues.append({
                    'rule': 'ORPHAN_TODO',
                    'message': f'TODO without STORY parent: {h["title"]}',
                    'line': h['line_start'],
                })
            check_todo_parent(h.get('children', []), h['keyword'])
    check_todo_parent(headings)

    # Check for items with SPRINT but no POINTS
    all_items = sprint_items(headings, 4) + sprint_items(headings, 3)
    for h in all_items:
        if not h['properties'].get('POINTS'):
            warnings.append({
                'rule': 'MISSING POINTS',
                'message': f'No POINTS set: {h["title"]}',
                'line': h['line_start'],
            })

    return {
        'issues': issues,
        'warnings': warnings,
        'active_count': len(active),
        'started_count': len(started),
        'next_count': len([h for h in active if h['keyword'] in ('NEXT', 'STORY-NEXT')]),
    }


def stats(headings: list[dict]) -> dict:
    """Overall statistics."""
    def count_all(hs):
        total = len(hs)
        for h in hs:
            total += count_all(h['children'])
        return total

    all_keywords = {}
    def collect_keywords(hs):
        for h in hs:
            kw = h['keyword']
            all_keywords[kw] = all_keywords.get(kw, 0) + 1
            collect_keywords(h['children'])
    collect_keywords(headings)

    epics = [h for h in headings if h['keyword'] == 'EPIC']
    for h in headings:
        epics.extend([c for c in h['children'] if c['keyword'] == 'EPIC'])

    return {
        'total_headings': count_all(headings),
        'top_level_count': len(headings),
        'epic_count': len(epics),
        'keyword_breakdown': all_keywords,
        'epics': [
            {
                'title': e['title'],
                'children_count': len(e['children']),
                'total_points': sum(int(c['properties'].get('POINTS', '0')) for c in e['children']),
                'sprint': e['properties'].get('SPRINT', 'backlog'),
            }
            for e in epics
        ],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: org_query.py <file.org> [--cmd] [args]'}))
        sys.exit(1)

    first_arg = sys.argv[1]

    # ─── Write-mode commands (no filepath needed) ──────────────────────
    if first_arg == '--create-todo' or first_arg == '--dry-run':
        if len(sys.argv) < 3:
            print(json.dumps({'error': f'Usage: org_query.py {first_arg} \'{{"title":"...","body":"..."}}\''}))
            sys.exit(1)

        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(json.dumps({'error': f'Invalid JSON: {e}'}))
            sys.exit(1)

        if not params.get('title'):
            print(json.dumps({'error': 'title is required'}))
            sys.exit(1)

        destination = params.get('destination', 'inbox')
        filepath = resolve_destination(destination)
        is_dry_run = first_arg == '--dry-run'

        result = create_todo(filepath, params, dry_run=is_dry_run)
        print(json.dumps(result, indent=2))
        return

    # ─── Read-mode commands (filepath as first arg) ────────────────────
    filepath = first_arg
    if not Path(filepath).exists():
        print(json.dumps({'error': f'File not found: {filepath}'}))
        sys.exit(1)

    if len(sys.argv) < 3:
        # Default: full parse output
        headings = parse_org(filepath)
        print(json.dumps({'headings': headings}, indent=2, default=str))
        return

    # Parse the file for all read commands
    headings = parse_org(filepath)
    cmd = sys.argv[2]

    if cmd == '--summary':
        sprint = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        print(json.dumps(sprint_summary(headings, sprint), indent=2))

    elif cmd == '--find-active':
        active = find_active(headings)
        print(json.dumps([
            {
                'title': h['title'],
                'keyword': h['keyword'],
                'level': h['level'],
                'points': h['properties'].get('POINTS', '0'),
                'sprint': h['properties'].get('SPRINT', 'backlog'),
                'value': h['properties'].get('VALUE', ''),
                'goal': h['properties'].get('GOAL', ''),
                'line': h['line_start'],
                'epic_chain': h.get('parent_title', '(top-level)'),
            }
            for h in active
        ], indent=2))

    elif cmd == '--find-epic':
        name = sys.argv[3] if len(sys.argv) > 3 else ''
        epic = find_epic(headings, name)
        if epic:
            print(json.dumps(epic, indent=2, default=str))
        else:
            print(json.dumps({'error': f'EPIC matching "{name}" not found'}))

    elif cmd == '--sprint':
        sprint_arg = sys.argv[3] if len(sys.argv) > 3 else '4'
        try:
            sprint = int(sprint_arg)
        except ValueError:
            sprint = sprint_arg  # e.g. "backlog"
        items = sprint_items(headings, sprint)
        print(json.dumps([
            {
                'title': h['title'],
                'keyword': h['keyword'],
                'points': h['properties'].get('POINTS', '0'),
                'value': h['properties'].get('VALUE', ''),
                'goal': h['properties'].get('GOAL', ''),
                'line': h['line_start'],
                'epic': h.get('parent_title', '(top-level)'),
            }
            for h in items
        ], indent=2))

    elif cmd == '--insert-point':
        name = sys.argv[3] if len(sys.argv) > 3 else ''
        result = insert_point(headings, name)
        print(json.dumps(result, indent=2))

    elif cmd == '--children-of':
        name = sys.argv[3] if len(sys.argv) > 3 else ''
        children = children_of(headings, name)
        print(json.dumps(children, indent=2))

    elif cmd == '--heading':
        pattern = sys.argv[3] if len(sys.argv) > 3 else ''
        h = find_heading(headings, pattern)
        if h:
            print(json.dumps(h, indent=2, default=str))
        else:
            print(json.dumps({'error': f'Heading matching "{pattern}" not found'}))

    elif cmd == '--stats':
        print(json.dumps(stats(headings), indent=2))

    elif cmd == '--validate':
        print(json.dumps(validate(headings), indent=2))

    elif cmd == '--epics':
        all_epics = []
        def collect_epics(hs):
            for h in hs:
                if h['keyword'] == 'EPIC':
                    all_epics.append({
                        'title': h['title'],
                        'line': h['line_start'],
                        'children_count': len(h['children']),
                        'sprint': h['properties'].get('SPRINT', 'backlog'),
                        'tags': h['tags'],
                    })
                collect_epics(h['children'])
        collect_epics(headings)
        print(json.dumps(all_epics, indent=2))

    elif cmd == '--verify-line':
        line_num = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        result = verify_line(filepath, line_num)
        print(json.dumps(result, indent=2))

    else:
        print(json.dumps({'error': f'Unknown command: {cmd}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()
