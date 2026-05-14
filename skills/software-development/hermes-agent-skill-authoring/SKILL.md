---
name: hermes-agent-skill-authoring
description: "Author and maintain the skill library: SKILL.md format, class-level architecture, preference embedding, active maintenance. Covers in-repo and user-local skills."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [writing-plans, requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

Skills live in two locations:

## Skill Library Architecture

Skills are the agent's procedural memory — reusable approaches for recurring task classes. The library must be well-structured for both the agent to find the right skill and the user to maintain it.

### Class-Level, Not Flat

Every skill should represent a **class of task**, not a single session's work. Signals a name is too narrow:
- Contains a specific PR number, error string, feature codename, or date
- Only makes sense in the context of today's debug session
- Describes a one-off fix rather than a reusable approach

Good names: `systematic-debugging`, `debugging-hermes-tui-commands`, `test-driven-development`
Bad names: `fix-the-403-on-parse-endpoint`, `debug-session-may-14`, `audit-traefik-logs-today`

If the name only makes sense for today's task, fall back to extending an existing umbrella or adding a support file under it.

### Rich SKILL.md + References/ Directory

Each umbrella skill should have:
- **SKILL.md**: The governing document — triggers, workflow, pitfalls, conventions. This is where preferences and corrections live (not in memory).
- **`references/`**: Session-specific detail — error transcripts, reproduction recipes, provider quirks, condensed knowledge banks (quoted research, API docs, domain notes). Write them concise; they are not mirrors of upstream docs.
- **`templates/`**: Starter files meant to be copied and modified — boilerplate configs, scaffolding, known-good examples.
- **`scripts/`**: Statically re-runnable actions — verification scripts, fixture generators, deterministic probes.

A long flat list of narrow skills means the agent can't find the right one, and the user has to maintain dozens of near-identical entries.

### Embedding User Preferences in SKILL.md Body

When the user corrects your style, tone, format, workflow, or approach, the correction belongs in the **SKILL.md body** of the skill that governs that class of task — not just in memory.

Memory captures: "who the user is and what the current situation is."
Skills capture: "how to do this class of task for this user."

Priority order for embedding:
1. **User style/format criticism** → update the relevant skill's "Common Pitfalls" or add a "Style" subsection
2. **User workflow/sequence correction** → update the relevant skill's workflow steps or triggers
3. **New technique/tool-usage pattern** → add as a recipe or pitfall in the governing skill

When you receive a correction signal from the user or the signal detector, do not just save it to memory. Update the skill immediately.

### Active Maintenance (Default On)

"Nothing to save" should not be the default. Every session should produce at least one skill update — even if small. Scan for these signals every session:
- User corrected your approach or style → embed in governing skill
- A skill you loaded was outdated → patch it now
- You discovered a new technique, fix, or workaround → capture it
- A new class of task appeared → consider creating an umbrella

A pass that does nothing is a missed learning opportunity, not a neutral outcome.

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** on the active branch.
6. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **Always commit** the edit — in-repo skills are source, not runtime state.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Duplicating cross-cutting conventions (MECE violation).** Quality rules (citations, back-links, source precedence) and domain conventions (filing rules, schemas) belong in centralized reference files loaded via `skill_view()`, not redefined inline in each skill. If multiple skills repeat the same rules verbatim, they violate MECE — the rule is defined in one place and referenced, not copied. Before adding a "Quality Rules" or "Conventions" section to any skill, check if a canonical version already exists in a reference file under the governing umbrella skill. If it does, remove the inline duplication and add a `skill_view()` call instead.

7. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

8. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

9. **Skipping skill updates after a clean session.** "Nothing to save" is a real option but should NOT be the default. Every session produces at least one learning — a correction, a technique, a pitfall. Scan for it and capture it. A pass that does nothing is a missed learning opportunity.

10. **Putting corrections in memory instead of SKILL.md.** When the user corrects your style, workflow, or approach, embed the lesson in the skill body that governs that task class. Memory captures who the user is; skills capture how to work for this user. If the correction is about how to do the task, it belongs in the skill.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch
