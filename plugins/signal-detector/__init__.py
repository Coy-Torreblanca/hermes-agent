"""Signal Detector Plugin — READ + WRITE unified layer for Second Brain.

Hermes pre_llm_call plugin that fires before every LLM turn. Two responsibilities:

1. CONTEXT SURFACING (Read): Classifies whether the user message warrants a
   gbrain query. Injects a [BRAIN CONTEXT NEEDED] directive that prompts the
   agent to use the gbrain-query and second-brain skills.

2. WRITE DETECTION (Write): Detects write-worthy content — new entities,
   decisions, corrections, ideas. Injects a [SIGNAL] block that prompts the
   agent to search gbrain and consider writing via gbrain-page-writer.

3. ERROR ESCALATION: Tracks consecutive classification failures and injects
   escalating error signals (warning → degraded → broken) so the agent
   knows when the pipeline is unhealthy.

4. METRICS: Counts every message, signal fire, and classification outcome.
   Logs a summary every 50 messages or when the agent requests it.

Architecture:
- DeepSeek Fast (`deepseek-chat`, ~$0.0001/msg) for classification
- Filters operational messages (fast-path, no API call)
- Plugin only injects TEXT SIGNALS — the agent handles all tool calls
  (gbrain queries, writes) during its normal tool-calling loop
- Silent to user — signals are for the agent only
- NEVER blocks the agent — all failures are caught and logged
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .classifier import classify_message, diagnose, get_failure_signal
from .metrics import get_metrics, get_metrics_lock

logger = logging.getLogger(__name__)

# Log summary every N messages
_SUMMARY_INTERVAL = 50


# ──────────────────────────────────────────────────────────────────────────────
# Signal formatters
# ──────────────────────────────────────────────────────────────────────────────

def _format_context_signal(classification: dict) -> str:
    """Format a context-surfacing directive for the agent."""
    entities = classification.get("entities", [])
    reasoning = classification.get("reasoning", "")

    parts = ["\n[BRAIN CONTEXT NEEDED]"]
    if reasoning:
        parts.append(f"reason: {reasoning}")
    if entities:
        parts.append(f"entities: {', '.join(map(str, entities))}")

    parts.extend([
        "→ Load the gbrain-query skill and follow its lookup chain.",
        "→ Load the second-brain skill.",
        "[/BRAIN CONTEXT NEEDED]\n"
    ])
    return "\n".join(parts)


def _format_write_signal(classification: dict) -> str:
    """Format a write-detection signal for the agent."""
    write_type = classification.get("write_type", "unknown")
    summary = classification.get("write_summary", "content worth capturing")
    entities = classification.get("entities", [])

    signal = "\n[SIGNAL: possible write needed — {}]\n".format(write_type.upper())
    signal += f"summary: {summary}\n"
    if entities:
        signal += f"entities: {', '.join(entities)}\n"
    signal += "→ Load the gbrain-page-writer skill and follow its write workflow.\n"
    signal += "→ Load the second-brain skill and follow its Iron Laws (search before create, cite, back-link).\n"
    signal += "[/SIGNAL]\n"
    return signal


def _maybe_log_summary() -> None:
    """Log metrics summary periodically (every _SUMMARY_INTERVAL messages)."""
    metrics = get_metrics()
    if metrics.messages_seen > 0 and metrics.messages_seen % _SUMMARY_INTERVAL == 0:
        logger.info("signal-detector periodic summary:\n%s", metrics.summary())


# ──────────────────────────────────────────────────────────────────────────────
# Main hook handler
# ──────────────────────────────────────────────────────────────────────────────

def on_pre_llm_call(
    session_id: str,
    user_message: str,
    conversation_history: Optional[list] = None,
    is_first_turn: bool = False,
    model: str = "",
    platform: str = "",
    **kwargs: Any,
) -> Optional[dict]:
    """pre_llm_call hook — runs before every LLM turn.

    Classification → Signal Injection + Error Escalation → Agent acts on signals.

    Returns dict with "context" key on success, None otherwise.
    Never raises — all failures are caught and logged.
    """
    if not user_message or not user_message.strip():
        return None

    try:
        parts = []
        context_signal = False
        write_signal = False
        write_type = ""
        error_signal = False

        # ── Step 0: Check for error escalation signals FIRST ─────────
        error_text = get_failure_signal()
        if error_text:
            parts.append(error_text)
            error_signal = True

        # ── Step 1: Classify the message via DeepSeek Fast ──────────
        classification = classify_message(user_message, conversation_history or [])
        if classification is None:
            # Recording handled by classifier, but error signal may be pending
            if error_signal:
                with get_metrics_lock():
                    get_metrics().record_signals(
                        session_id=session_id, error=True
                    )
                _maybe_log_summary()
            if parts:
                return {"context": "\n".join(parts)}
            return None

        # ── Step 2: Context Surfacing (READ path) ───────────────────
        if classification.get("query_brain"):
            parts.append(_format_context_signal(classification))
            context_signal = True

        # ── Step 3: Write Detection (WRITE path) ────────────────────
        if classification.get("write_signal"):
            parts.append(_format_write_signal(classification))
            write_signal = True
            write_type = classification.get("write_type", "")

        # ── Record signal metrics ───────────────────────────────────
        if context_signal or write_signal or error_signal:
            with get_metrics_lock():
                get_metrics().record_signals(
                    session_id=session_id,
                    context=context_signal,
                    write=write_signal,
                    write_type=write_type,
                    error=error_signal,
                )

        _maybe_log_summary()

        if not parts:
            return None

        context = "\n".join(parts)
        logger.debug(
            "signal-detector: injecting for session=%s (len=%d, query_brain=%s, write_signal=%s)",
            session_id,
            len(context),
            classification.get("query_brain"),
            classification.get("write_signal"),
        )
        return {"context": context}

    except Exception:
        logger.debug("signal-detector: hook handler failed", exc_info=True)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Plugin registration
# ──────────────────────────────────────────────────────────────────────────────

def register(ctx: Any) -> None:
    """Register the pre_llm_call hook with Hermes."""
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    logger.info("signal-detector plugin registered (pre_llm_call hook)")
