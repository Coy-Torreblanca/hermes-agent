# Emacs Configuration Reference

> **Canonical data lives in gbrain.** This file is a thin pointer. Load the gbrain pages below for the actual values before editing org files or relying on value schemas.

## gbrain References

| Page | Slug | What It Contains |
|------|------|------------------|
| Emacs Org-Mode Configuration | [sources/emacs-org-config](gbrain://sources/emacs-org-config) | Full config: file structure, todo keywords, capture templates, refile linter, dashboard, sprint numbers |
| Org-Mode Compliance Requirements | [concepts/org-mode-compliance-requirements](gbrain://concepts/org-mode-compliance-requirements) | VALUE schema, hierarchy rules (STORYs don't need EPICs, TODOs must have STORY parents), orthogonality principle, auto-derivation rules |
| TODO & Sprint Management | [projects/personalai/todo-sprint-management](gbrain://projects/personalai/todo-sprint-management) | Phase 1 script behavior, parameter contract, property order |

## How to Use

1. **Before any org file operation**, load `sources/emacs-org-config` via `mcp_gbrain_get_page(slug="sources/emacs-org-config")` to check canonical values.
2. **Before making a design decision** about org-mode properties (VALUE, GOAL, SPRINT), load `concepts/org-mode-compliance-requirements` for the current rules.
3. **When creating todos**, follow the parameter contract documented in `projects/personalai/todo-sprint-management`.

## Key Rules at a Glance

| Rule | Source |
|------|--------|
| VALUE values: `Essential`, `Important`, `Nice-to-have` | `sources/emacs-org-config` |
| VALUE and priority are orthogonal — never auto-derive | `concepts/org-mode-compliance-requirements` |
| GOAL is refile-only — never auto-derive (unless user explicitly says "infer it") | `concepts/org-mode-compliance-requirements` + SKILL.md pitfalls |
| STORYs don't need EPIC parents | `concepts/org-mode-compliance-requirements` |
| TODOs must have STORY parents | `concepts/org-mode-compliance-requirements` |
| Capture uses `*` (level 1) headings | `common-org-config.el` via `sources/emacs-org-config` |
| SPRINT numbers: backlog / 3 (work) / 4 (personal) | `sources/emacs-org-config` |
