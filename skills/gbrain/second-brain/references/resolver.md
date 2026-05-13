# Second Brain — Hermes Agent Resolver

> **Autoloaded into the Hermes system prompt.** This file answers WHAT gbrain is, WHEN to use it, and WHERE to go next. It does NOT teach HOW — the `second-brain` SKILL.md handles that.

## What gbrain Is

gbrain is your second brain — a knowledge graph of everything you know about people, companies, projects, concepts, meetings, and ideas.

## When to Use gbrain

**Search gbrain BEFORE answering.** Never guess. Never rely on training data alone.

- Someone asks "who is...", "what do I know about...", "tell me about..."
- You're asked about a person, company, project, deal, or past decision
- A concept, idea, or framework comes up that you might have captured before
- Anything you might have written down or encountered previously

**Write to gbrain immediately when:**

- User corrects you about any fact → write the correction NOW
- User shares something worth keeping (idea, decision, observation)
- You conclude something durable (finding, state change, synthesis)
- Any operational skill produces output worth preserving. Perform explicit checkpoint before final response: "Did I learn anything I didn't know before?" - if so, write to gbrain.

## When NOT to Use gbrain

- **Tasks and todos** → org-mode files (`/data/syncthing/Sync/org/`)
- **Live sprint state** → `tasks.org` directly (brain snapshots are stale)
- **Reminders and scheduling** → Hermes cron + Google Tasks
- **Sub-agent orchestration** → Hermes `delegate_task`
- **Journal entries** → `coy-journal` skill
- **Coding, CLI commands, file I/O** → not a brain concern

## How to Proceed

**Load the `second-brain` skill.** It contains conventions, quality rules, filing rules, schema, and dispatches to specialized sub-skills:

```
skill_view(name="second-brain")
```

From there, the skill will route you to the right sub-skill (`gbrain-page-writer`, `gbrain-query`, `gbrain-enrich`, etc.) based on what you're doing.

## Iron Laws

1. **Search before you guess.** The brain has information you don't remember.
2. **Cite everything.** Every fact written to gbrain needs `[Source: ...]`.
3. **Back-link everything.** Every entity mention must link back. An unlinked mention is a broken brain.
4. **Preserve exact phrasing.** The user's language IS the insight. Never paraphrase.
5. **Dedup before create.** Search existing pages before creating new ones.

## Signal Detector Protocol (NON-NEGOTIABLE)

The Signal Detector injects signals into your input — [BRAIN CONTEXT
NEEDED] for reads, [SIGNAL: possible write needed] for writes. Both
are the same contract: see a signal, act on it in the same turn.

Same-turn resolution means exactly one of:

1. ACT — Load the indicated skill and do what the signal asks.
2. EXPLICITLY DECLINE — Name the signal and your reason for not
   acting. "Already written this session," "not notable," "user
   hasn't confirmed." Specific, honest, immediate.
3. BOTH (when both appear) — Read first (get context), then write.

Invalid: silence, "noted," "I'll handle that later," acknowledging
the signal in prose without following through.

An unacknowledged signal is a dropped fact. Every signal resolves
in the same turn.
