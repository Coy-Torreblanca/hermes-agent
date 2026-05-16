---
name: gbrain-reports
description: "Generate, save, and load timestamped reports from cron jobs and brain operations. Cron jobs save their output as brain pages; the skill lets you browse past reports, compare snapshots, and generate new reports on demand."
version: 1.0.0
author: Coy
license: MIT
metadata:
  hermes:
    tags: [gbrain, reports, cron, second-brain]
    related_skills: [second-brain, gbrain-maintain, gbrain-query]
---

# GBrain Reports

Generate, save, load, and compare timestamped reports from cron jobs and brain operations. Every cron job (gbrain-dream, gbrain-doctor, gbrain-orphans, gbrain-contradictions) saves its output as a persistent brain page. This skill lets you browse past reports, compare snapshots over time, and generate new reports on demand.

## When to Use

- User says "show me the latest report", "get the dream cycle report"
- User says "run a report", "generate a brain health report"
- User wants to compare "last week vs this week" for any metric
- Cron job output needs to be saved as a brain page
- User asks "what changed since last time"

## Workflow

### Step 1: Load Conventions

```
read_file /data/.hermes/skills/gbrain/second-brain/references/quality.md
read_file /data/.hermes/skills/gbrain/second-brain/references/_output-rules.md
```

### Step 2: Identify Report Target

Determine what kind of report the user wants:

| Request | Report Type | Slug Prefix |
|---------|-------------|-------------|
| "brain health", "doctor" | Brain health dashboard | `reports/brain-health-YYYY-MM-DD` |
| "dream cycle", "autopilot" | Dream cycle summary | `reports/dream-cycle-YYYY-MM-DD` |
| "orphans", "orphan report" | Orphan page report | `reports/orphans-YYYY-MM-DD` |
| "contradictions" | Contradiction report | `reports/contradictions-YYYY-MM-DD` |
| "custom report" | On-demand synthesis | `reports/custom-YYYY-MM-DD-{topic}` |

### Step 3: Load Latest Report (Browse)

To show the most recent report of a type:

```
mcp_gbrain_search(query="reports/ dream-cycle")
# OR
mcp_gbrain_list_pages(type="source", limit=10, updated_after="7d")
mcp_gbrain_get_page(slug="reports/<type>-<date>")
```

### Step 4: Compare Reports (Optional)

If the user wants a comparison:

```
mcp_gbrain_get_page(slug="reports/<type>-<older-date>")
mcp_gbrain_get_page(slug="reports/<type>-<newer-date>")
```

Compare key metrics and highlight changes:
- Metrics that improved
- Metrics that worsened
- New issues since last report
- Issues that were resolved

### Step 5: Generate New Report (On-Demand)

If the user wants a fresh report instead of viewing past ones:

**For brain health:**
```
mcp_gbrain_get_health()
mcp_gbrain_run_doctor()
# Format into report
```

**For dream cycle:**
```
skill_view(name="gbrain-maintain")
# Follow Operation 5: Dream Cycle
```

**For orphans:**
```
mcp_gbrain_find_orphans(include_pseudo=false)
# Format into report
```

**For contradictions:**
```
mcp_gbrain_find_contradictions(limit=20)
# Format into report
```

### Step 6: Build Report Page

**Above the line (compiled truth):**

```markdown
---
type: source
title: "<Report Type> - YYYY-MM-DD"
tags: [report, <type>]
generated: YYYY-MM-DD HH:MM
source: <cron job name or "manual">
---

# <Report Type> — YYYY-MM-DD

## Summary
{One paragraph summary of findings}

## Key Metrics
| Metric | Value | Change vs Last | Status |
|--------|-------|----------------|--------|
| {Metric 1} | {value} | {+/- N} | {green/yellow/red} |
| {Metric 2} | {value} | {+/- N} | {green/yellow/red} |

## Findings
### {Finding category 1}
- {Detail}

### {Finding category 2}
- {Detail}

## Recommendations
- {What to do based on findings}
```

**Below the line (raw data):**

```

---

## Raw Data
{Full tool output preserved for audit}
```

### Step 7: Save Report

```
mcp_gbrain_put_page(slug="reports/<type>-YYYY-MM-DD", content="<report markdown>")
```

### Step 8: Add Timeline Entry

```
mcp_gbrain_add_timeline_entry(
    slug="reports/<type>-YYYY-MM-DD",
    date="YYYY-MM-DD",
    summary="Generated {type} report",
    detail="Key finding: {one-line}. Recommendations: {summary}."
)
```

## Report Format Standards

### Date Convention
- Reports use YYYY-MM-DD date format in the slug
- If multiple reports of the same type on the same day, append sequence: `reports/dream-cycle-2026-05-13-2`

### Metric Display
| Status | Indicator | Meaning |
|--------|-----------|---------|
| 🟢 Green | Healthy | No action needed |
| 🟡 Yellow | Warning | Needs attention soon |
| 🔴 Red | Critical | Needs immediate action |

### Comparison Format
```
| Metric | This Week | Last Week | Change | Trend |
|--------|-----------|-----------|--------|-------|
| Health Score | 72 | 65 | +7 | 📈 |
| Embed Coverage | 45% | 30% | +15% | 📈 |
| Orphans | 891 | 1091 | -200 | 📉 |
```

## Common Pitfalls

- **Missing comparison baseline** — if no previous report exists, note "first report — no comparison available"
- **Overwriting previous reports** — each report gets a unique date slug. NEVER overwrite a past report.
- **No raw data** — always include the full tool output in the "Raw Data" section for auditability
- **Metrics without context** — a number without comparison is meaningless. Always show trend or baseline.
- **Report noise** — do not generate reports unless asked. Cron jobs handle scheduled reports.

## Report Types Reference

| Slug Pattern | Generated By | Frequency | Key Metrics |
|-------------|--------------|-----------|-------------|
| `reports/brain-health-YYYY-MM-DD` | gbrain-doctor cron | Weekly (Mon) | Score, embed %, stale, orphans, dead links |
| `reports/dream-cycle-YYYY-MM-DD` | gbrain-dream cron | Nightly (2am) | Pages processed, embeds, backlinks, purges |
| `reports/orphans-YYYY-MM-DD` | gbrain-orphans cron | Weekly (Sat) | Orphan count, top 10, enrichment suggestions |
| `reports/contradictions-YYYY-MM-DD` | gbrain-contradictions cron | Daily (9am) | High/med/low contradictions, conflict pairs |

## Verification Checklist

- [ ] Conventions loaded via skill_view()
- [ ] Report type identified (browse, compare, or generate)
- [ ] For browse: latest report loaded and displayed
- [ ] For compare: metrics compared with delta and trend
- [ ] For generate: fresh data collected via appropriate tools
- [ ] Report page follows standard format (metrics, findings, recommendations)
- [ ] Raw data preserved below the line
- [ ] Report saved with unique date slug
- [ ] Timeline entry added for the report
