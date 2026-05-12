---
name: blogwatcher
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool."
version: 2.1.0
author: JulienTant (fork of Hyaxia/blogwatcher)
license: MIT
metadata:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites:
  commands: [blogwatcher-cli]
---

# Blogwatcher

Track blog and RSS/Atom feed updates with the `blogwatcher-cli` tool. Supports automatic feed discovery, HTML scraping fallback, OPML import, and read/unread article management.

## Installation

Pick one method:

- **Go:** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker:** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **Binary (Linux amd64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (Linux arm64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Apple Silicon):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Intel):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

All releases: https://github.com/JulienTant/blogwatcher-cli/releases

### Docker with persistent storage

By default the database lives at `~/.blogwatcher-cli/blogwatcher-cli.db`. In Docker this is lost on container restart. Use `BLOGWATCHER_DB` or a volume mount to persist it:

```bash
# Named volume (simplest)
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# Host bind mount
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### Migrating from the original blogwatcher

If upgrading from `Hyaxia/blogwatcher`, move your database:

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

The binary name changed from `blogwatcher` to `blogwatcher-cli`.

## Common Commands

### Managing blogs

- Add a blog: `blogwatcher-cli add "My Blog" https://example.com`
- Add with explicit feed: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- Add with HTML scraping: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- List tracked blogs: `blogwatcher-cli blogs`
- Remove a blog: `blogwatcher-cli remove "My Blog" --yes`
- Import from OPML: `blogwatcher-cli import subscriptions.opml`

### Scanning and reading

- Scan all blogs: `blogwatcher-cli scan`
- Scan one blog: `blogwatcher-cli scan "My Blog"`
- List unread articles: `blogwatcher-cli articles`
- List all articles: `blogwatcher-cli articles --all`
- Filter by blog: `blogwatcher-cli articles --blog "My Blog"`
- Filter by category: `blogwatcher-cli articles --category "Engineering"`
- Mark article read: `blogwatcher-cli read 1`
- Mark article unread: `blogwatcher-cli unread 1`
- Mark all read: `blogwatcher-cli read-all`
- Mark all read for a blog: `blogwatcher-cli read-all --blog "My Blog" --yes`

## Environment Variables

All flags can be set via environment variables with the `BLOGWATCHER_` prefix:

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Path to SQLite database file |
| `BLOGWATCHER_WORKERS` | Number of concurrent scan workers (default: 8) |
| `BLOGWATCHER_SILENT` | Only output "scan done" when scanning |
| `BLOGWATCHER_YES` | Skip confirmation prompts |
| `BLOGWATCHER_CATEGORY` | Default filter for articles by category |

## Example Output

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

## Pitfalls

### HTTP Redirects (301/302/307)

Blogwatcher-cli does **not** follow HTTP redirects. If a feed URL returns 301, 302, or 307, the scan fails silently with "failed to fetch feed" or "Failed to detect feed type." Always resolve the final URL first:

```bash
curl -sI -L --max-time 5 "https://example.com/blog/rss.xml" | grep -E "^HTTP|^location"
```

Then use the final destination URL with `--feed-url`.

**Examples from this setup:**
- OpenAI: `/blog/rss.xml` → 307 → `/news/rss.xml` (resolved)
- Railway: `/rss/` → 301 → `/rss.xml` (resolved)
- DeepMind: `/blog/feed/` → 302 → `/blog/rss.xml` (resolved)

### Nitter / Twitter RSS

Nitter instances (`nitter.net/{account}/rss`) return valid RSS 2.0 XML (verified with `curl -A "Mozilla/5.0"`), but blogwatcher-cli **cannot parse it** — fails with "Failed to detect feed type." This is a known limitation. Nitter also requires a browser `User-Agent` header to return content (empty body otherwise). For Twitter/X feeds, use an alternative approach (custom script with xurl, or local RSS generation).

### Sites Without RSS

Some modern sites have no RSS/Atom feed at all:
- **Anthropic** (anthropic.com) — Next.js + Sanity CMS, no feed endpoints, all patterns 404
- **GCP Blog** (cloud.google.com/blog) — client-side JS rendering, all feed URLs return HTML, old FeedBurner feed is dead
- **Mistral** (mistral.ai/news) — 404 on all feed patterns
- **Meta AI** (ai.meta.com/blog) — 404 on all feed patterns

Always test a candidate feed URL with `curl -sI` before adding. If you get HTML content-type or 404, the site likely has no RSS.

### User-Agent Blocking

Some servers (notably Nitter) return empty bodies or 403 unless the request includes a browser `User-Agent`. Blogwatcher-cli uses Go's default HTTP client; if a feed returns 200 but zero articles on scan, the server may be blocking on UA.

## Automation

### Cron for daily scanning

```bash
# Scan all feeds silently, report only new articles
0 8 * * * BLOGWATCHER_DB=/path/to/blogwatcher-cli.db blogwatcher-cli scan 2>&1
```

### Environment setup

For this Hermes deployment, the database lives at a non-default path. All commands must set `BLOGWATCHER_DB`:

```bash
export BLOGWATCHER_DB=/data/.blogwatcher-cli/blogwatcher-cli.db
```

Or prepend to every command: `BLOGWATCHER_DB=/data/.blogwatcher-cli/blogwatcher-cli.db blogwatcher-cli ...`

Use `BLOGWATCHER_YES=1` to skip confirmation prompts on `remove` and `read-all`.

### Terminal timeout on `add` command

`blogwatcher-cli add` can time out when run via `terminal` tool (observed with karpathy.bearblog.dev). The command itself works fine — fall back to `execute_code` with subprocess:

```python
import subprocess, os
env = os.environ.copy()
env['BLOGWATCHER_DB'] = '/data/.blogwatcher-cli/blogwatcher-cli.db'
env['BLOGWATCHER_YES'] = '1'
subprocess.run(['blogwatcher-cli', 'add', '<name>', '<url>', '--feed-url', '<feed>'],
               capture_output=True, text=True, timeout=30, env=env)
```

Same pattern works for `scan`, `articles`, and `blogs`. Discovered May 12, 2026.
