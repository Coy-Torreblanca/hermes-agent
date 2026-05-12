# gbrain Integration — Sprint Planning Reference

> How to plan gbrain-dependent stories. Written May 10, 2026 during
> Second Brain sprint architecture session.

## When a Sprint Story Depends on gbrain

Before committing gbrain-dependent stories to a sprint, verify the
infrastructure is healthy. gbrain silently degrades in ways that make
stories appear feasible when they're blocked.

## Pre-Sprint Checklist

1. Check `mcp_gbrain_get_stats()` — embedded_count must be > 0
2. Check `mcp_gbrain_get_health()` — brain_score, stale_pages, dead_links
3. Check `mcp_gbrain_list_jobs()` — no stuck/cancelled jobs
4. Check cron state — `cronjob list` → gbrain sync cron NOT paused
5. Check Minions worker — `gbrain jobs supervisor` is running
6. Check API keys — `OPENAI_API_KEY` + `ANTHROPIC_API_KEY` in config.yaml

## gbrain Gap Analysis Pattern

When a story requires knowledge storage/retrieval, ask:
1. Does gbrain already ship this? (34 skills — check README)
2. Does gbrain have the pattern but needs wiring? (extend)
3. Is this outside gbrain's domain? (build custom)

See the full gap analysis at gbrain skill `references/ingestion-pipeline.md`.

## Second Brain Architecture (May 2026)

Three-component model emerging from sprint planning:
1. Static Context Plugin — journal + todos, cached with TTL
2. Per-Message Plugin — gbrain hybrid search via pre_llm_call hook
3. Signal Detector Sub-Agent — ambient capture via delegate_task

All three depend on healthy gbrain infrastructure (embeddings, expansion, worker).
Block the sprint stories until infrastructure is unblocked.
