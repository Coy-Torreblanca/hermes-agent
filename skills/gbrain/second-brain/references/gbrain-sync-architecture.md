# GBrain Sync Architecture — Real-Time & Batch

> How gbrain stays fresh. Two complementary pipelines: real-time conversation sync and batch file-system sync.

## The Two Pipelines

| Pipeline | Driver | What It Syncs | Latency |
|----------|--------|---------------|---------|
| **Conversational (real-time)** | Agent writes via `mcp_gbrain_put_page` during conversation | Decisions, corrections, state changes, new entities | Same-turn |
| **Batch (scheduled)** | Nightly gbrain sync cron (`cb57bd8b9389`) | Org file diffs, code changes, dream cycle | Up to 24h |

## Current: Conversational Agent Self-Sync

Currently, the conversational agent (me) is responsible for both responding to the user AND writing to gbrain. This works via:

1. The Signal Detector plugin (`pre_llm_call`) injects `[SIGNAL: possible write needed]` when it detects gbrain-worthy content
2. I then load `gbrain-page-writer`, search, dedup, and write
3. This splits my attention between conversation and gbrain maintenance

**Problem:** Every gbrain signal is a context switch. It pulls me out of the conversational flow.

## Proposed: Parallel Sync Agent

An architectural pattern where two LiteLLM agents share identical message history via KV caching:

1. **🗣️ Conversational Agent** — Responds to user, executes tasks (what I am now)
2. **🧠 Sync Agent** — Silent observer, reads every turn, writes to gbrain when warranted

**Key properties:**
- Zero latency impact (sync agent runs after response is delivered)
- Shared KV cache via LiteLLM makes incremental cost near-zero
- No attention split for conversational agent
- Independent of nightly cron — they serve different purposes

### Design Decisions (Confirmed May 18, 2026)

| Decision | Resolution |
|----------|-----------|
| **Write frequency** | On-demand — sync agent judges per turn, no required writes |
| **Sync scope** | Any pertinent information from full turn context (user msg + assistant response + tool results) |
| **Cron relationship** | Independent — real-time sync beside batch cron. May overlap; dedup at gbrain layer (same slug, same content hash = no-op) |
| **Model choice** | Deferred — TBD |
| **Toolset** | gbrain MCP tools only: search, put_page, add_timeline_entry, add_link, add_tag, get_page, resolve_slugs, memory. No terminal, file I/O, web, or delegate_task. |

### Implementation Approach

The recommended approach (Option A, Gateway Post-Turn hook):

```python
# Added to gateway/run.py after _run_agent returns
async def _sync_gbrain_after_turn(self, session_key, session_entry, source, messages):
    from run_agent import AIAgent
    
    sync_agent = AIAgent(
        model="haiku",              # cheaper model — configurable
        **_sync_runtime_kwargs,
        max_iterations=3,
        quiet_mode=True,
        skip_memory=True,
        enabled_toolsets=["gbrain"],  # gbrain MCP tools only
        session_id=session_entry.session_id,
    )
    sync_agent._print_fn = lambda *a, **kw: None
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: sync_agent.run_conversation(
        user_message="Review this conversation turn and update gbrain if needed.",
        conversation_history=messages,
    ))
```

Requires:
1. A `gbrain` toolset in `toolsets.py` (restricted MCP tools)
2. A sync agent system prompt as a skill
3. A `sync_model` config key in `config.yaml`
4. ~20 lines of hook code in `gateway/run.py`

### What the Sync Agent Does

- Detects new entities (people, companies, projects, concepts)
- Captures decisions and commitments
- Records state changes ("Phase 4 is now DONE")
- Persists corrections
- Updates project pages with current status
- Extracts structured facts

### What the Sync Agent Does NOT Do

- Respond to the user
- Execute terminal/file/network tools
- Modify org files or system state
- Run skill workflows

## Existing: Nightly Batch Sync Cron

The nightly cron (`cb57bd8b9389`) handles:
- Full re-sync of org files to gbrain pages
- Dream cycle (pattern detection, graph population)
- Dead link detection and repair
- Cross-reference enrichment

## Relationship

The two pipelines are complementary:

```
Conversational sync (real-time)       Batch sync (nightly)
  ↓                                      ↓
Captures what's happening NOW         Captures persistent STATE
Decisions, corrections, entities      Org file diffs, code changes
  ↓                                      ↓
      gbrain ←←←←←←←←←←←←←←←←← Both write here ←←←←←←←←←←←←
```

Dedup is handled at the gbrain layer: writing to the same slug with the same content hash is a no-op. The nightly cron therefore doesn't duplicate real-time writes, and vice versa.

## See Also

- gbrain `concepts/parallel-gbrain-sync-agent` — full concept page with design rationale
- `coy/coy-sprint/references/org-retro-and-stale.md` — retro/stale commands (sync agent would write retro data)
- `toolsets.py` — where the `gbrain` toolset would be defined
- `gateway/run.py` — where the sync agent hook would be added
