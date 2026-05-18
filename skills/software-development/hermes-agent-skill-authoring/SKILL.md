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
- **`references/`**: Session-specific detail — error transcripts, reproduction recipes, provider quirks — AND condensed knowledge banks: quoted research, API docs, external authoritative excerpts, or domain notes you found while working on the problem. Write them concise and for the value of the task, not as a full mirror of upstream docs.
- **`templates/`**: Starter files meant to be copied and modified — boilerplate configs, scaffolding, known-good examples.
- **`scripts/`**: Statically re-runnable actions — verification scripts, fixture generators, deterministic probes.

A long flat list of narrow skills means the agent can't find the right one, and the user has to maintain dozens of near-identical entries.

### Memory vs. Skills — Sharp Boundary

Memory and skills serve different purposes. Confusing them is the most common skill-update mistake.

| Store | Purpose | Example |
|-------|---------|---------|
| **Memory** | Who the user is + what the current environment/situation is | "User prefers concise responses." "Project uses pytest with xdist." |
| **SKILL.md body** | How to do this class of task for this user | "Before presenting EPIC insertions, run `--dry-run` first. If rejected, adjust SPRINT to match parent." |

**The rule:** If a correction tells you HOW to do a task (sequence, rule, approach, tool preference, format preference), it goes in the SKILL.md body of the governing task skill. **Even if you also save it to memory**, the SKILL.md is the canonical location — and the memory entry should NOT duplicate the workflow instruction. Memory should only record the fact that the protocol exists or was established (e.g., "Dry-run validation protocol established May 18"), not re-state the procedure.

This applies especially to workflow preferences — the triage dry-run protocol, the habit toggle method, the refile cleanup step — all belong in the governing skill body, not in memory. Memory is for identity and environment facts, not for re-listing procedures.

[Source: CoyDiego correction, Lab/#secondbrain, 2026-05-18]

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
- **User corrected your style, tone, format, legibility, or verbosity** — Frustration signals like 'stop doing X', 'this is too verbose', 'don't format like this', 'why are you explaining', 'just give me the answer', 'you always do Y and I hate it', or an explicit 'remember this' are **FIRST-CLASS skill signals**, not just memory signals. Update the relevant governance skill(s) to embed the preference so the next session starts already knowing the right way.
- A skill you loaded was outdated → patch it now
- You discovered a new technique, fix, or workaround → capture it
- A new class of task appeared → consider creating an umbrella

A pass that does nothing is a missed learning opportunity, not a neutral outcome.

#### Preference Order (which action to take)

When a signal fires, prefer the **earliest action that fits** — don't skip ahead to "create new" if a simpler update would work:

1. **UPDATE A CURRENTLY-LOADED SKILL** — If you had a skill loaded via `skill_view()` and it covers the territory of the new learning, patch that one first. It is the skill that was in play, so it's the right one to extend.
2. **UPDATE AN EXISTING UMBRELLA** — If no loaded skill fits but an existing class-level umbrella does (check via `skills_list` + `skill_view`), patch it. Add a subsection, a pitfall, or broaden a trigger.
3. **ADD A SUPPORT FILE** under an existing umbrella — Add a `references/`, `templates/`, or `scripts/` file when the learning is a specific recipe, transcript, or reusable probe, not a workflow change. The umbrella's SKILL.md should gain a one-line pointer to the new file so future sessions discover it.
4. **CREATE A NEW CLASS-LEVEL UMBRELLA** — Only when no existing skill covers the class. The name MUST be at the class level (not a PR number, error string, feature codename, or today's-session artifact). If the proposed name only makes sense for today's task, fall back to 1, 2, or 3.

If you notice two existing skills that overlap, note it in your reply — the background curator handles consolidation at scale. Don't reorganize the library in a single session; just flag the overlap.

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
6. **🚨 Post-Creation Quality Gate 1: MECE Check.** After creating the skill, verify it doesn't overlap with existing skills:
   - Run `skills_list(category="<target-category>")` or scan the category directory
   - Compare descriptions and triggers of all peers in the same category
   - If ANY peer would activate on the same user request → flag the overlap, either merge into the existing skill or sharpen the boundary
   - Check for duplicate names across categories (e.g., same skill name in `coy/` and `research/`)
   - Document the resolution: if no overlap, note "clean MECE." If overlap found, take action before declaring done.
7. **🚨 Post-Creation Quality Gate 2: Modularity Check.** After creating the skill, test whether it can be split into multiple child skills:
   - **Read the SKILL.md.** Does it cover multiple distinct task classes that each have their own triggers, workflow, and pitfalls? If a section could be its own `skill_view()` candidate → it's a candidate for splitting.
   - **If multiple skills can be created from this parent:** split the deep-dive content into `references/*.md` or child skills. The SKILL.md should be the *index*, not the entire knowledge base.
   - **If it's one coherent task class:** keep it as a single parent skill regardless of file size. A large but coherent skill (like `coy-sprint` at ~32k chars covering the complete sprint management system) is better than an arbitrary split into non-viable fragments.
   - **Check the `references/` directory:** is it empty when it should have supporting docs? Does the SKILL.md inline content that belongs in reference files? Even a single-parent skill can benefit from moving reference material out of the SKILL.md body.
8. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

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

11. **Putting corrections in memory instead of SKILL.md.** When the user corrects your style, workflow, or approach, embed the lesson in the skill body that governs that task class. Memory captures who the user is; skills capture how to work for this user. If the correction is about how to do the task, it belongs in the skill.

12. **Creating wrapper/shim scripts in a skill's `scripts/` directory.** If a tool lives at a canonical path outside the skill directory (e.g., `~/.hermes/scripts/`), reference it by that path directly in SKILL.md commands and test imports. Do NOT place a wrapper in `scripts/` that `exec()`s the canonical script — it's unnecessary indirection. The user will call it out as "another script we don't need." Tests should use `os.path.expanduser("~/.hermes/scripts/<tool>")` with an optional `ORG_QUERY_PATH`-style env override for CI. Discovery: CoyDiego, Discord #secondbrain, 2026-05-15.

13. **Skipping MECE checks before AND after creation.** Before creating: run `references/mecE-checklist.md` to check for overlap. After creating: run the post-creation MECE gate (Workflow step 6) — verify the new skill doesn't overlap with existing peers and has clean trigger boundaries. Both checks are mandatory — the pre-check prevents duplication, the post-check catches what pre-check missed.

14. **Creating a skill that covers multiple task classes without splitting it.** Don't use arbitrary character thresholds to decide when to split. Instead, ask: *does this SKILL.md cover multiple distinct task classes that each have their own triggers, workflow, and pitfalls?* If a section could be its own `skill_view()` candidate, it should be in a child skill or `references/*.md` file. A single-parent skill (like `coy-sprint` at ~32k) is fine if it's one coherent system — splitting it would produce non-viable fragments. But a multi-concern blob disguised as one skill is an anti-pattern: the SKILL.md should be the *index*, not the entire knowledge base. Move deep-dive content (recipe tables, error catalogs, verbose configuration examples) into `references/*.md` and replace inlined content with a one-line pointer.

15. **Using `skill_view(file_path=...)` to load reference files instead of `read_file` with an absolute path.** When a reference file lives under the skill's `references/` directory (e.g., `references/deep-dive.md`), load it with `read_file` and an absolute path — not `skill_view(file_path='references/deep-dive.md')`.

    **Rationale:**
    - **Prevents recursive cascade:** `skill_view(file_path=...)` triggers the full skill-loader pipeline, which can itself invoke other `skill_view()` calls, leading to cascading loads and hard-to-trace recursion.
    - **Semantic clarity:** `read_file` signals *I need data from this file* (a read operation), while `skill_view` signals *I need the Hermes Agent skill system* (a meta-load operation). Using the wrong tool obscures intent.
    - **No unnecessary metadata:** `skill_view` wraps the file content with skill frontmatter parsing, metadata extraction, and session registration — all of which are irrelevant for a plain reference document.

    **Before (anti-pattern):**
    ```python
    content = skill_view(file_path='references/provider-quirks.md')
    ```

    **After (correct):**
    ```python
    content = read_file(path='/data/.hermes/skills/software-development/hermes-agent-skill-authoring/references/provider-quirks.md')
    ```

    The absolute path ensures the agent resolves the file correctly regardless of the current working directory.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] **Modularity gate passed: SKILL.md covers one coherent task class (not multiple). If it covers multiple distinct classes, deep-dive content split into references/ or child skills.**
- [ ] **MECE gate passed: no overlapping skills in same category, no duplicate names across categories, clean trigger boundaries documented.**
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch
