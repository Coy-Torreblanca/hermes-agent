> **This is a reference file loaded via `skill_view()`.** All brain writes use `mcp_gbrain_put_page` with slugs derived from these rules.

# Repo Architecture — Filing Rules

> **Full filing rules:** See `references/_brain-filing-rules.md`

## The Rule

Every new page is filed by **primary subject** — not by format, not by source.
Ask: "What would you search for to find this page?"

## Directory Resolver

Walk this decision tree for every page:

| Primary Subject | Directory |
|----------------|-----------|
|| About a person | `people/{name-slug}` |
|| About a company | `companies/{name-slug}` |
|| A reusable concept, framework, or mental model | `concepts/{slug}` |
|| An original idea or thesis | `originals/{slug}` |
|| A meeting or call | `meetings/{slug}` |
|| Media content (video, podcast, article) | `media/{type}/{slug}` |
|| Raw data import | `sources/{slug}` |

## Decision Protocol

1. **Identify the primary subject.** What would you search for to find this page?
2. **Walk the decision tree** above. Pick the directory that matches.
3. **Cross-link.** Link from related directories (entity propagation is mandatory).
4. **Check notability.** See `references/quality.md` notability gate.
5. **When in doubt:** what would you search for?

For misfiling patterns, see `references/_brain-filing-rules.md`.

## Anti-Patterns

- Filing by format ("it's a PDF so it goes in sources/")
- Filing by source ("it came from email so it goes in sources/")
- Creating pages without checking if one already exists
- Using `sources/` for anything except raw data dumps

## Output Format

Advisory: "File this at `{type}/{slug}` because the primary subject is {reason}."
