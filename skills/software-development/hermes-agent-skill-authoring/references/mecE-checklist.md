# MECE Skill Audit Checklist

A repeatable process for checking the Hermes skill library for **Mutually Exclusive, Collectively Exhaustive** properties.

## When to Run

- User says "do a MECE check on skills" or "audit the skill library"
- Before creating a new umbrella skill (confirm no overlap with existing)
- After adding several new skills to a category

## Methodology

### 1. Inventory All Skills

Get the full list from `available_skills` in the system prompt, or scan on disk:

```bash
for dir in /data/.hermes/skills/*/; do
  category=$(basename "$dir")
  for skill_dir in "$dir"*/; do
    if [ -f "$skill_dir/SKILL.md" ]; then
      name=$(basename "$skill_dir")
      desc=$(head -5 "$skill_dir/SKILL.md" | grep "^description:" | sed 's/description: "//;s/"$//')
      echo "$category / $name — $desc"
    fi
  done
done
```

### 2. Check Mutual Exclusivity (Overlaps)

For each pair of skills in the same functional area, compare:

- **Trigger conditions**: Could the same user request activate both skills?
- **Description boundary**: Do the descriptions clearly differentiate when to use one vs the other?
- **related_skills**: Are cross-references documented?
- **On-disk duplicates**: Check for same skill name under different categories (e.g., `coy/blogwatcher` vs `research/blogwatcher`)

| Overlap Type | Severity | Action |
|-------------|----------|--------|
| Same skill, two copies on disk (different inodes) | 🔴 High | Delete duplicate, keep canonical, symlink if needed |
| Same skill listed in two categories (same file) | 🟡 Low | Document in SKILL.md cross-refs |
| Fuzzy boundary between two different skills | 🟡 Medium | Sharpen descriptions, add `related_skills` link |
| Complementary skills (different roles/lifecycle) | 🟢 None | No action needed |

### 3. Check Collective Exhaustiveness (Gaps)

For common user intents, ask: is there a skill that covers this?

- "I need to set up X" → infrastructure/provisioning skill?
- "Debug this error" → debugging skills exist, but which one?
- "Query the database" → database skill?
- "Manage containers" → Docker skill?
- "Clean up files" → file management skill?

List gaps as observations, not demands. The user decides if a gap needs filling.

### 4. Check Structural Health

- **Empty categories**: Directories with only a `DESCRIPTION.md` and no skills (e.g., `diagramming/`)
- **Dead references**: `related_skills` that don't resolve on disk
- **Drifted copies**: Same skill at two paths with different content (check `diff`)

### 5. Update gbrain

Save findings to `concepts/hermes-skill-dedup-audit` in gbrain with:
- What was found (overlaps, gaps, structural issues)
- What was resolved (deletions, symlinks, merges)
- What remains open

## Example Output

From the May 15, 2026 audit:
- 🔴 `research/blogwatcher` was a stale duplicate of `coy/blogwatcher` — deleted
- 🟡 `diagramming/` category on disk had zero skills (only a DESCRIPTION.md)
- 🟢 Coding agents (claude-code, codex, opencode) — proper MECE by provider
- 🟢 Kanban (orchestrator, worker) — proper MECE by role

[Source: compiled from CoyDiego session, Discord #secondbrain, 2026-05-15]
