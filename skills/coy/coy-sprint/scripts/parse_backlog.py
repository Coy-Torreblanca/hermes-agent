#!/usr/bin/env python3
"""Parse backlog items from tasks.org for sprint planning.
Outputs items sorted by VALUE (Critical → Low) then by POINTS ascending.
Only includes STORY/TODO items with SPRINT: backlog or no SPRINT.
Usage: python3 parse_backlog.py [--max-points N] [--value-only VALUE]
"""

import re, sys, argparse
from datetime import datetime, date

parser = argparse.ArgumentParser()
parser.add_argument('--max-points', type=int, default=16)
parser.add_argument('--value-only', type=str, default=None)
parser.add_argument('--stale', type=int, default=0,
                    help='Flag items untouched for N+ sprint cycles (1 sprint ≈ 2 weeks)')
parser.add_argument('--file', type=str, default='/data/syncthing/Sync/org/work/tasks.org')
args = parser.parse_args()

with open(args.file) as f:
    content = f.read()

items = []
current_item = None
value_order = {'Essential': 0, 'Important': 1, 'Nice-to-have': 2, 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}

for line in content.split('\n'):
    heading_match = re.match(r'^(\*+)\s+(STORY|EPIC|TODO)\s*(?:\[#(A|B|C)\]\s*)?(.+?)(?:\s+:[\w:]+:)?$', line)
    if heading_match:
        if current_item and current_item.get('sprint', '').strip() in ('backlog', ''):
            items.append(current_item)
        current_item = {
            'level': len(heading_match.group(1)),
            'keyword': heading_match.group(2),
            'priority': heading_match.group(3) or '',
            'title': heading_match.group(4).strip(),
            'points': '', 'value': '', 'sprint': '', 'goal': '', 'created': ''
        }
        continue

    if current_item:
        pts = re.match(r'\s*:POINTS:\s+(.+)', line)
        val = re.match(r'\s*:VALUE:\s+(.+)', line)
        spr = re.match(r'\s*:SPRINT:\s+(.+)', line)
        gl = re.match(r'\s*:GOAL:\s+(.+)', line)
        cr = re.match(r'\s*:CREATED:\s+(.+)', line)
        if pts: current_item['points'] = pts.group(1).strip()
        if val: current_item['value'] = val.group(1).strip()
        if spr: current_item['sprint'] = spr.group(1).strip()
        if gl: current_item['goal'] = gl.group(1).strip()
        if cr: current_item['created'] = cr.group(1).strip()

if current_item and current_item.get('sprint', '').strip() in ('backlog', ''):
    items.append(current_item)

# Filter and sort
backlog = []
for item in items:
    if item['keyword'] in ('STORY', 'TODO') and item['sprint'] in ('backlog', '') and item['value']:
        if args.value_only and item['value'] != args.value_only:
            continue
        try:
            pts = int(item['points']) if item['points'] else 0
        except ValueError:
            pts = 0
        if pts > args.max_points:
            continue
        backlog.append({
            'priority': item['priority'],
            'points': pts,
            'value': item['value'],
            'keyword': item['keyword'],
            'title': item['title'],
            'goal': item['goal'][:100] if item.get('goal') else '',
            'created': item['created'],
            'stale': False
        })

backlog.sort(key=lambda x: (value_order.get(x['value'], 99), x['points']))

# ── Stale Detection ────────────────────────────────────────────────────────────
if args.stale > 0:
    today = date.today()
    for s in backlog:
        created_str = s.get('created', '')
        if created_str:
            m = re.search(r'(\d{4}-\d{2}-\d{2})', created_str.strip())
            if m:
                try:
                    created_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
                    days_old = (today - created_date).days
                    sprints_old = days_old / 14  # 1 sprint ≈ 2 weeks
                    if sprints_old >= args.stale:
                        s['stale'] = True
                except ValueError:
                    pass

# Output
committed = 0
for s in backlog:
    stale_marker = "⏰ " if s.get('stale') else ""
    flag = f"[{s['priority']}]" if s['priority'] else "   "
    print(f"{stale_marker}{flag} {s['keyword']} {s['title'][:70]}")
    print(f"    POINTS: {s['points']} | VALUE: {s['value']}")
    if s['goal']:
        print(f"    GOAL: {s['goal']}")
    committed += s['points']
    if committed >= args.max_points:
        break

print(f"\nTOTAL: {committed} pts")
