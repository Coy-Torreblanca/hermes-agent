---
name: gbrain-citation-fixer
description: "Find and fix broken citations across gbrain pages. Scans for uncited claims, malformed citation patterns, and missing source dates. Chains into gbrain-maintain for batch repair workflows."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, maintenance, citations, second-brain]
    related_skills: [second-brain, gbrain-maintain, gbrain-page-writer, gbrain-query]
---

# GBrain Citation Fixer

Find and fix broken citations across gbrain pages. Scans for uncited claims, malformed citation patterns, orphan brackets, and missing source dates. Designed to be chained from gbrain-maintain during brain health sessions.

## When to Use

- User says "check my citations", "fix broken citations", "audit sources"
- Called from gbrain-maintain during citation audit (Operation 7)
- Dream cycle flagged citation problems during lint
- You encounter a page with missing or broken citations during normal work
- After bulk ingestion — verify all new pages have proper citations

## Workflow

### Step 1: Load Conventions

```
skill_view(name="second-brain", file_path="references/quality.md")
skill_view(name="second-brain", file_path="references/_output-rules.md")
```

### Step 2: Identify Citation Issues

Scan pages for these common citation problems:

| Problem | Pattern | Severity |
|---------|---------|----------|
| Missing citation | Factual claim with no `[Source: ...]` | High |
| Broken bracket | `[Source: ...` (no closing bracket) | High |
| Empty source | `[Source: ]` | Medium |
| No date | `[Source: User]` without date | Medium |
| Stale date | Citation date > 6 months old for time-sensitive claims | Low |
| Wrong format | `[source: ...]` (lowercase) or `(Source: ...)` (parens) | Low |
| Orphan `[Source:` | Hanging text that looks like a broken citation attempt | High |

### Step 3: Choose Scan Strategy

**Targeted scan** (recommended): Scan a specific page or set of pages.

```
mcp_gbrain_get_page(slug="<specific_page>")
# Parse content for citation issues
```

**Broad scan** (bulk): Use brain health tools to find pages with issues.

```
mcp_gbrain_run_doctor()
# Review results for citation-related findings
mcp_gbrain_search(query="[Source:")  # Find pages with citations
mcp_gbrain_search(query="- **[Source:")  # Find timeline-style citations
```

### Step 4: Fix Each Issue

For each identified issue, fix using `mcp_gbrain_put_page` with corrected content.

**Missing citation fix:**
1. Read the full page context
2. Trace each factual claim to its source (conversation, journal entry, user statement)
3. Add `[Source: {identified source}, YYYY-MM-DD]` inline
4. If source cannot be determined, add a note: `[Source: unknown — needs verification]`

**Broken bracket fix:**
```
# Before
Some claim here [Source: User, conversation

# After
Some claim here [Source: User, conversation, YYYY-MM-DD]
```

**Stale date fix:**
- Update date if the claim is still current
- Add context note if the claim status has changed
- If no longer verifiable, mark as `[Source: historical, needs reverification]`

### Step 5: Log Repair

```
mcp_gbrain_add_timeline_entry(
    slug="<page_slug>",
    date="YYYY-MM-DD",
    summary="Citation fix: {type of fix}",
    detail="Fixed {N} citation issues. Details: {what was changed}."
)
```

### Step 6: Report Results

Report to the user:
- Number of pages scanned
- Number of issues found and fixed
- Issues that could not be fixed (with reasons)
- Pages that need manual review

## When to Chain to gbrain-maintain

After fixing citations, if the page needs deeper maintenance:

- Stale content detected → offer to trigger gbrain-maintain (Operation 2: Fix Stale Pages)
- Orphan pages found → offer orphan enrichment (Operation 3)
- Dead links found → offer dead link detection (Operation 4)

```
skill_view(name="gbrain-maintain")
# Follow relevant operation
```

## Citation Quality Standards

From quality.md conventions:

| Element | Required? | Example |
|---------|-----------|---------|
| Source type | Always | `[Source: User, ...]` |
| Date | Always | `[Source: User, conversation, 2026-05-13]` |
| Context | Recommended | `[Source: User, conversation about second brain, 2026-05-13]` |
| URL (web sources) | Always | `[Source: arxiv, https://..., 2026-05-13]` |
| Source precedence | Follow ranking | User > compiled > timeline > external |

## Common Pitfalls

- **Fixing without context** — do not add a citation if you do not know the source. Mark as "unknown" instead.
- **Over-writing** — use targeted patch edits, not full page rewrites, when possible
- **Automated fixes without review** — show the user what you plan to change before executing on bulk fixes
- **Missing the timeline** — timeline entries can have citation issues too. Scan both layers.
- **Wrong source type** — do not guess. "Inferred" is valid only if you can trace the inference path.

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Pages scanned for citation issues
- [ ] Each issue traced to source (or marked as unknown)
- [ ] Fixes applied with correct citation format
- [ ] User shown changes before bulk execution
- [ ] Timeline entries added for repairs
- [ ] Follow-up maintenance chained if needed
- [ ] Quality conventions followed (citations, back-links — see second-brain/references/quality.md)
- [ ] Remaining issues documented for manual review
