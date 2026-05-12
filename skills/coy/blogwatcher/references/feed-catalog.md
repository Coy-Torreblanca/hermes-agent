# RSS Feed Catalog

12 feeds configured in blogwatcher-cli. DB at `/data/.blogwatcher-cli/blogwatcher-cli.db`.
All commands require `BLOGWATCHER_DB=/data/.blogwatcher-cli/blogwatcher-cli.db`.

## Cloud Providers (6)

| Feed | URL | RSS Feed |
|------|-----|----------|
| AWS Blog | https://aws.amazon.com/blogs/aws/ | https://aws.amazon.com/blogs/aws/feed/ |
| Azure Blog | https://azure.microsoft.com/en-us/blog/ | https://azure.microsoft.com/en-us/blog/feed/ |
| Railway | https://blog.railway.com | https://blog.railway.com/rss.xml |
| Kubernetes | https://kubernetes.io | https://kubernetes.io/feed.xml |
| Cloudflare | https://blog.cloudflare.com | https://blog.cloudflare.com/rss/ |
| CNCF | https://www.cncf.io | https://www.cncf.io/blog/feed/ |

## AI / Research (6)

| Feed | URL | RSS Feed |
|------|-----|----------|
| OpenAI | https://openai.com/news | https://openai.com/news/rss.xml |
| HuggingFace | https://huggingface.co/blog | https://huggingface.co/blog/feed.xml |
| DeepMind | https://deepmind.google | https://deepmind.google/blog/rss.xml |
| Karpathy | https://karpathy.bearblog.dev | https://karpathy.bearblog.dev/feed/ |
| Arxiv AI | https://arxiv.org | https://rss.arxiv.org/rss/cs.AI |
| Arxiv CL | https://arxiv.org/list/cs.CL/recent | https://rss.arxiv.org/rss/cs.CL |

**Karpathy feed note:** Bearblog supports both Atom (`/feed/`, `/feed.xml`) and RSS (`/rss/`). All tested as working (200 + correct content-type). Added May 12, 2026.

## Dead Ends (no RSS available)

- **Anthropic** — Next.js + Sanity CMS, no RSS endpoint. Old `/blog` redirects to `/news`.
- **GCP** — Returns HTML only (client-side rendered). Old FeedBurner feed dead since 2018.
- **Mistral** — No RSS feed found.
- **Meta AI** — No RSS feed found.
- **Google Research** — No RSS feed found.

## Changelog RSS

Script: `~/.hermes/scripts/changelog_rss.py`
Output: `~/.hermes/www/changelog.xml`
Source: git log of `/data/syncthing/Sync`
