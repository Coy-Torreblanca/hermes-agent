# tasks.org Organization — Bloat Diagnosis & Remediation

When `tasks.org` exceeds ~500 lines, it becomes unwieldy for both Emacs and agent parsing. This documents the diagnostic framework and recommended split pattern.

## Diagnostic Checklist

When Coy says "tasks.org is too large," check:

1. **DONE items with full logs** — Sprint 3 and earlier DONE stories with all timestamp logs and subtask details are dead weight. Keep current sprint DONE items for velocity tracking only.

2. **ICEBOX bloat** — ICEBOX stories don't belong in the active tasks file. They compete for attention and add bulk. Move to `icebox.org`.

3. **Duplicate EPICs** — Check for the same EPIC appearing twice with different scopes (e.g., "My Holy Bible v1" at line 310 and "My Holy Bible v1 [ICEBOX]" at line 543).

4. **Domain mixing** — The file currently mixes Bible site, 30ai, tooling (Emacs/Neovim), Hermes infra, and admin/finance. Active sprint stories get lost in the noise.

5. **Protocol header bloat** — The 90-line Agent Management Protocol comment block is useful but oversized for daily use.

## Recommended Split Pattern

```
tasks.org          → Active sprint + current backlog priorities (~300 lines)
biblesite.org      → EPIC My Holy Bible v1 + BSB + Rich Bible Data
tooling.org        → Emacs v2, Neovim v2, OpenHands, git cleanup
icebox.org         → All ICEBOX stories
tasks_archive.org  → Completed Sprint 1-3 DONE stories with full logs
```

## Remediation Sequence

1. **Archive DONE items first** — fastest win, no decisions needed
2. **Move ICEBOX to icebox.org** — move, don't delete
3. **Split by domain** — proposal requires Coy approval for new file structure
4. **Resolve duplicates** — merge duplicate EPICs, keep the current-scope version
5. **Trim protocol header** — move to `AGENTS.md` reference, keep 10-line summary in tasks.org

## May 8, 2026 Baseline

- File: 1,515 lines, 54KB
- ~150+ tasks across 7+ domains
- Duplicates: My Holy Bible v1 EPIC (lines 310 + 543)
- Active sprint: EPIC 30ai Thin Vertical Slice (lines 1054-1133, 2 DONE, 3 remaining)
- ICEBOX: 30ai [ICEBOX] (55 pts), Emacs v2 [ICEBOX], Bible v1 [ICEBOX] (202 pts)
