#!/usr/bin/env python3
"""
org_query.py — Structured read/write for org-mode files.
Eliminates regex fragility in agent ↔ org-mode interactions.

Usage:
  org_query.py tasks.org --summary           # Dashboard: STARTED, NEXT, sprint load
  org_query.py tasks.org --find-active        # All active tasks with parent EPIC chain
  org_query.py tasks.org --find-epic "30ai"   # Full subtree under matching EPIC
  org_query.py tasks.org --sprint 4           # All items in sprint 4
  org_query.py tasks.org --insert-point "30ai [ICEBOX]"  # Where to insert child under EPIC
  org_query.py tasks.org --children-of "Second Brain"    # Direct children of heading
  org_query.py tasks.org --heading "Four-Stage RAG"      # Find heading by regex
  org_query.py tasks.org --stats              # Point totals, velocity, capacity
  org_query.py tasks.org --validate           # Check for WIP violations, orphans, etc.

Output: JSON to stdout. Exit codes: 0 = success, 1 = error.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional


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
        heading_match = re.match(r'^(\*+)\s+(TODO|NEXT|STARTED|DONE|CANCELLED|STORY|STORY-NEXT|STORY-STARTED|STORY-DONE|STORY-WAITING|WAITING|EPIC)?\s*(\[#(A|B|C)\])?\s*(.*)', line)

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
    # This is populated during parsing via parent_title
    result = find_heading(headings, target_title)
    if not result:
        return []
    chain = [result['title']]
    current = result
    # Walk up using parent pointers from the tree
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
    """Find where to insert a new child under an EPIC.
    Returns the line number after the last child (or after EPIC properties if no children).
    """
    epic = find_epic(headings, epic_name)
    if not epic:
        return {'error': f'EPIC containing "{epic_name}" not found'}

    if epic['children']:
        last_child = epic['children'][-1]
        return {
            'epic': epic['title'],
            'epic_line': epic['line_start'],
            'insert_after_line': last_child['line_end'] - 1,  # Last line of last child's body
            'last_child': last_child['title'],
            'level': epic['level'] + 1,  # Children are one level deeper
            'stars': '*' * (epic['level'] + 1),
        }
    else:
        # No children — insert after EPIC properties
        return {
            'epic': epic['title'],
            'epic_line': epic['line_start'],
            'insert_after_line': epic['line_start'] + len(epic['properties']) + 2,  # After :END:
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

    # Check for top-level STORYs without EPIC parent (orphans)
    for h in headings:
        if h['keyword'] == 'STORY' and h['level'] == 1:
            warnings.append({
                'rule': 'HIERARCHY',
                'message': f'Top-level STORY without EPIC parent: {h["title"]}',
                'line': h['line_start'],
            })

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

    def count_by_keyword(hs, kw):
        total = 1 if any(h['keyword'] == kw for h in [hs]) else 0
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

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(json.dumps({'error': f'File not found: {filepath}'}))
        sys.exit(1)

    headings = parse_org(filepath)

    if len(sys.argv) < 3:
        # Default: full parse output
        print(json.dumps({'headings': headings}, indent=2, default=str))
        return

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
            # Return the full subtree
            print(json.dumps(epic, indent=2, default=str))
        else:
            print(json.dumps({'error': f'EPIC matching "{name}" not found'}))

    elif cmd == '--sprint':
        sprint = int(sys.argv[3]) if len(sys.argv) > 3 else 4
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

    else:
        print(json.dumps({'error': f'Unknown command: {cmd}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()
