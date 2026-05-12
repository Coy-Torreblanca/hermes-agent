#!/usr/bin/env python3
"""Generate RSS feed from Hermes changelog (git log of /data/syncthing/Sync/)."""
import subprocess, sys, os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

REPO = "/data/syncthing/Sync"
OUTPUT = os.path.expanduser("~/.hermes/www/changelog.xml")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# Get last 50 commits
result = subprocess.run(
    ["git", "-C", REPO, "log", "--format=%H|%ai|%an|%s", "-50"],
    capture_output=True, text=True
)

now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
items = []

for line in result.stdout.strip().split("\n"):
    if not line:
        continue
    parts = line.split("|", 3)
    if len(parts) < 4:
        continue
    commit_hash, date_str, author, subject = parts
    # Convert git date to RFC 822
    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        rfc_date = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        rfc_date = now
    
    items.append(f"""    <item>
      <title>{escape(subject)}</title>
      <link>https://hermes.local/changelog/{commit_hash[:8]}</link>
      <guid>{commit_hash}</guid>
      <pubDate>{rfc_date}</pubDate>
      <author>{escape(author)}</author>
      <description>{escape(subject)}</description>
    </item>""")

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Hermes Changelog</title>
    <link>https://hermes.local/changelog</link>
    <description>Every change made to Coy's org files, wiki, gbrain syncs, and Hermes config — tracked via git.</description>
    <lastBuildDate>{now}</lastBuildDate>
    <generator>hermes-changelog.py</generator>
{"".join(items)}
  </channel>
</rss>"""

with open(OUTPUT, "w") as f:
    f.write(rss)

print(f"Changelog RSS written to {OUTPUT} ({len(items)} entries)")
