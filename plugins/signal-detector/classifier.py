"""Signal Detector classifier — DeepSeek Fast classification for Second Brain.

Two responsibilities:
1. CONTEXT SURFACING (Read): classifies whether user message warrants a gbrain query
2. WRITE DETECTION (Write): detects write-worthy content (new entities, decisions, etc.)

Error handling: tracks consecutive failures with escalating signals.
- 1-2 failures: silent (transient)
- 3-9 failures: warning injected into agent context
- 10-49 failures: degraded signal with diagnostics
- 50+ failures: broken — agent should escalate to user

Cost-optimized: uses DeepSeek Fast (~$0.0001/msg) to gate expensive gbrain queries.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx

from .metrics import get_metrics, get_metrics_lock

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Classification prompts
# ──────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a lightweight message classifier for a Second Brain system. Analyze the user message and determine two things:

1. CONTEXT SURFACING (Read): Should we query the knowledge graph (gbrain) for relevant context?
   - YES if the message mentions specific entities (people, companies, projects, tools),
     asks a question, discusses a concept, or references past work/decisions.
   - NO if it's operational ("ok", "thanks", "do it"), a simple greeting, or very short.

2. WRITE DETECTION (Write): Does this message contain information worth writing to the brain?
   - YES for: new entities (people, companies, projects, concepts), original thinking,
     ideas, observations, decisions, commitments, state changes, project descriptions,
     goals, plans, corrections about known entities, new facts.
   - NO for: questions, simple status updates, operational commands, casual chat.

Return JSON only, no other text. Format:
{"query_brain": true/false, "write_signal": true/false, "entities": ["entity1", ...], "write_type": "entity|idea|decision|correction|state_change|null", "write_summary": "one-line summary or null", "reasoning": "brief"}"""

_OPERATIONAL_TRIGGERS = frozenset({
    "ok", "okay", "thanks", "thank you", "thx", "ty", "got it", "gotcha",
    "do it", "go ahead", "proceed", "continue", "yes", "no", "yep", "nope",
    "good", "great", "nice", "cool", "perfect", "sure", "fine", "alright",
    "ack", "acknowledged", "done", "will do", "on it", "roger",
})

# ──────────────────────────────────────────────────────────────────────────────
# Failure tracking
# ──────────────────────────────────────────────────────────────────────────────

class FailureKind(str, Enum):
    """Categorised failure reasons for targeted diagnostics."""
    NO_API_KEY = "no_api_key"
    AUTH_ERROR = "auth_error"          # 401/403 from DeepSeek
    RATE_LIMIT = "rate_limit"          # 429
    SERVER_ERROR = "server_error"      # 5xx
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"        # JSON decode failure
    NETWORK = "network_error"          # ConnectionError, etc.
    UNKNOWN = "unknown"


@dataclass
class FailureTracker:
    """Tracks consecutive classification failures with escalation logic."""

    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_failure_kind: FailureKind = FailureKind.UNKNOWN
    last_failure_detail: str = ""
    last_failure_time: float = 0.0
    # Per-kind counters for diagnostics
    failure_counts: dict[FailureKind, int] = field(default_factory=dict)
    # Track whether we've already injected a signal at each level
    # to avoid re-injecting the same signal on every turn
    _last_signal_level: int = 0

    def record_success(self) -> None:
        """Reset failure counters on successful classification."""
        self.consecutive_failures = 0
        self.total_successes += 1
        self._last_signal_level = 0

    def record_failure(self, kind: FailureKind, detail: str = "") -> None:
        """Record a failure and return the escalation level (0-3)."""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_failure_kind = kind
        self.last_failure_detail = detail
        self.last_failure_time = time.monotonic()
        self.failure_counts[kind] = self.failure_counts.get(kind, 0) + 1

    @property
    def escalation_level(self) -> int:
        """Current escalation level for consecutive failures.

        0 = silent (0-2 failures)
        1 = warning (3-9 failures)
        2 = degraded (10-49 failures)
        3 = broken (50+ failures)
        """
        if self.consecutive_failures < 3:
            return 0
        if self.consecutive_failures < 10:
            return 1
        if self.consecutive_failures < 50:
            return 2
        return 3

    def should_signal(self) -> bool:
        """True if we should inject an error signal this turn.

        Only signals when the escalation level *changes* (up or down),
        to avoid spamming the same warning on every turn.
        """
        level = self.escalation_level
        if level != self._last_signal_level:
            self._last_signal_level = level
            return True
        return False

    def diagnostic_text(self) -> str:
        """Human-readable diagnostics for the current failure streak."""
        parts = [
            f"Consecutive classification failures: {self.consecutive_failures}",
            f"Total failures: {self.total_failures} (successes: {self.total_successes})",
            f"Last failure: {self.last_failure_kind.value}",
        ]
        if self.last_failure_detail:
            # Truncate long details
            detail = self.last_failure_detail
            if len(detail) > 200:
                detail = detail[:197] + "..."
            parts.append(f"Detail: {detail}")
        # Show top failure kinds
        if len(self.failure_counts) > 1:
            top = sorted(self.failure_counts.items(), key=lambda x: -x[1])[:3]
            parts.append("Failure breakdown: " + ", ".join(
                f"{k.value}={v}" for k, v in top
            ))
        return "\n".join(parts)

    def reset(self) -> None:
        """Full reset (e.g., after plugin reload or config change)."""
        self.consecutive_failures = 0
        self.total_failures = 0
        self.total_successes = 0
        self.last_failure_kind = FailureKind.UNKNOWN
        self.last_failure_detail = ""
        self.last_failure_time = 0.0
        self.failure_counts.clear()
        self._last_signal_level = 0


# Module-level tracker (shared across all sessions in the process)
_tracker = FailureTracker()
_tracker_lock = threading.Lock()

# ──────────────────────────────────────────────────────────────────────────────
# Client
# ──────────────────────────────────────────────────────────────────────────────

_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
_REQUEST_TIMEOUT = 5.0  # seconds — must not block the agent


def _get_api_key() -> Optional[str]:
    """Read DeepSeek API key from environment or Hermes config."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key

    # Try Hermes config
    try:
        from hermes_constants import get_hermes_home
        import yaml

        config_path = get_hermes_home() / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            providers = config.get("providers", {})
            deepseek = providers.get("deepseek", {})
            key = deepseek.get("api_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    except Exception:
        pass

    return key or None


def _is_operational(message: str) -> bool:
    """Fast path: skip classification for obvious operational messages."""
    cleaned = message.strip().lower().rstrip(".!? ")
    if len(cleaned) <= 3:
        return True
    if cleaned in _OPERATIONAL_TRIGGERS:
        return True
    return False


def _classify(
    user_message: str,
    conversation_history: Optional[list] = None,
    api_key: Optional[str] = None,
) -> Optional[dict]:
    """Send user message to DeepSeek for classification.

    Returns parsed JSON dict on success, None on failure.
    Updates the module-level FailureTracker on both paths.
    """
    if not api_key:
        api_key = _get_api_key()
    if not api_key:
        with _tracker_lock:
            _tracker.record_failure(
                FailureKind.NO_API_KEY,
                "DEEPSEEK_API_KEY not set in environment or Hermes config",
            )
        logger.warning("signal-detector: no DeepSeek API key found (failure #%d)",
                       _tracker.consecutive_failures)
        with get_metrics_lock():
            get_metrics().record_classification(success=False)
        return None

    # Build messages: system prompt + optional conversation context
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    # Include last assistant response for context if available
    if conversation_history:
        last_assistant = None
        for msg in reversed(conversation_history):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                content = msg.get("content", "")
                if content and len(content) > 10:
                    last_assistant = content[:500]
                    break
        if last_assistant:
            messages.append({"role": "assistant", "content": f"[Previous response]: {last_assistant}"})

    messages.append({"role": "user", "content": user_message})

    try:
        start = time.monotonic()
        resp = httpx.post(
            _DEEPSEEK_URL,
            json={
                "model": "deepseek-v4-pro",
                "messages": messages,
                "max_tokens": 256,
                "temperature": 0.0,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=_REQUEST_TIMEOUT,
        )
        elapsed = time.monotonic() - start
        logger.debug("signal-detector: DeepSeek classify took %.2fs, status=%d", elapsed, resp.status_code)

        # ── HTTP error handling ──────────────────────────────────────────
        if resp.status_code == 401 or resp.status_code == 403:
            detail = resp.text[:200] if resp.text else "No response body"
            with _tracker_lock:
                _tracker.record_failure(FailureKind.AUTH_ERROR, detail)
            logger.warning("signal-detector: DeepSeek auth error %d: %s", resp.status_code, detail)
            with get_metrics_lock():
                get_metrics().record_classification(success=False)
            return None

        if resp.status_code == 429:
            detail = resp.text[:200] if resp.text else "Rate limited"
            with _tracker_lock:
                _tracker.record_failure(FailureKind.RATE_LIMIT, detail)
            logger.warning("signal-detector: DeepSeek rate limited: %s", detail)
            with get_metrics_lock():
                get_metrics().record_classification(success=False)
            return None

        if resp.status_code >= 500:
            detail = f"HTTP {resp.status_code}: {resp.text[:200] if resp.text else 'No body'}"
            with _tracker_lock:
                _tracker.record_failure(FailureKind.SERVER_ERROR, detail)
            logger.warning("signal-detector: DeepSeek server error %d", resp.status_code)
            with get_metrics_lock():
                get_metrics().record_classification(success=False)
            return None

        if resp.status_code != 200:
            detail = f"HTTP {resp.status_code}: {resp.text[:200] if resp.text else 'No body'}"
            with _tracker_lock:
                _tracker.record_failure(FailureKind.UNKNOWN, detail)
            logger.debug("signal-detector: DeepSeek unexpected status %d", resp.status_code)
            with get_metrics_lock():
                get_metrics().record_classification(success=False)
            return None

        # ── Successful response ──────────────────────────────────────────
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response
        content = content.strip()
        # Handle markdown code fences
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        result = json.loads(content)
        logger.debug("signal-detector: classification = %s", result)

        with _tracker_lock:
            _tracker.record_success()

        elapsed_ms = (time.monotonic() - start) * 1000
        with get_metrics_lock():
            get_metrics().record_classification(success=True, elapsed_ms=elapsed_ms)

        return result

    except json.JSONDecodeError:
        with _tracker_lock:
            _tracker.record_failure(
                FailureKind.PARSE_ERROR,
                f"Failed to parse: {content[:200]}",
            )
        logger.debug("signal-detector: JSON parse failure (consecutive=%d)", _tracker.consecutive_failures)
        with get_metrics_lock():
            get_metrics().record_classification(success=False)
        return None

    except httpx.TimeoutException:
        with _tracker_lock:
            _tracker.record_failure(
                FailureKind.TIMEOUT,
                f"Request timed out after {_REQUEST_TIMEOUT}s",
            )
        logger.debug("signal-detector: timeout (consecutive=%d)", _tracker.consecutive_failures)
        with get_metrics_lock():
            get_metrics().record_classification(success=False)
        return None

    except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError, OSError) as e:
        with _tracker_lock:
            _tracker.record_failure(FailureKind.NETWORK, str(e)[:200])
        logger.debug("signal-detector: network error (consecutive=%d): %s",
                     _tracker.consecutive_failures, e)
        with get_metrics_lock():
            get_metrics().record_classification(success=False)
        return None

    except Exception as e:
        with _tracker_lock:
            _tracker.record_failure(FailureKind.UNKNOWN, str(e)[:200])
        logger.debug("signal-detector: unexpected error (consecutive=%d)", _tracker.consecutive_failures, exc_info=True)
        with get_metrics_lock():
            get_metrics().record_classification(success=False)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def classify_message(
    user_message: str,
    conversation_history: Optional[list] = None,
) -> Optional[dict]:
    """Public entry point: classify a user message.

    Returns None if classification should be skipped (operational message,
    API key missing, or classification failed).
    """
    with get_metrics_lock():
        get_metrics().record_message()

    if _is_operational(user_message):
        with get_metrics_lock():
            get_metrics().record_filtered()
        return None
    return _classify(user_message, conversation_history)


def diagnose(message: str) -> str:
    """Diagnostic: classify a message and return the raw result + metrics.

    Use this to test what the classifier would do with a specific message
    without waiting for it to appear in a real conversation.

    Returns a formatted string with classification result and current metrics.
    """
    from .metrics import get_metrics

    result = classify_message(message)
    metrics = get_metrics()

    lines = [
        "═══ Signal Detector Diagnosis ═══",
        f"Message: {message[:200]}",
        "",
    ]

    if result is None:
        lines.append("Classification: SKIPPED (operational message or failed)")
    else:
        lines.append(f"Classification: SUCCESS")
        lines.append(f"  query_brain:   {result.get('query_brain')}")
        lines.append(f"  write_signal:  {result.get('write_signal')}")
        lines.append(f"  write_type:    {result.get('write_type')}")
        lines.append(f"  write_summary: {result.get('write_summary')}")
        lines.append(f"  entities:      {result.get('entities')}")
        lines.append(f"  reasoning:     {result.get('reasoning')}")

    lines.append("")
    lines.append(metrics.summary())
    return "\n".join(lines)


def get_failure_signal() -> Optional[str]:
    """Return an error signal if the failure tracker has escalated.

    Returns formatted [SIGNAL DETECTOR …] context block, or None if
    no signal is needed (either healthy or not enough failures yet).
    Uses should_signal() to avoid re-injecting on every turn — only
    fires when the escalation level changes.
    """
    with _tracker_lock:
        if not _tracker.should_signal():
            return None

        level = _tracker.escalation_level
        diag = _tracker.diagnostic_text()

    if level == 0:
        return None  # Recovered — no signal needed

    if level == 1:
        # Warning: 3-9 consecutive failures
        return (
            "\n[SIGNAL DETECTOR WARNING — degraded]\n"
            f"{diag}\n"
            "The signal detector is experiencing persistent failures. "
            "Check the DeepSeek API key and network connectivity. "
            "The agent will continue without brain context surfacing until this is resolved.\n"
            "[/SIGNAL DETECTOR WARNING]\n"
        )

    if level == 2:
        # Degraded: 10-49 consecutive failures
        return (
            "\n[SIGNAL DETECTOR DEGRADED — significant outage]\n"
            f"{diag}\n"
            "The signal detector has failed on the last 10+ messages. "
            "Brain context surfacing and write detection are NOT functioning. "
            "Agent should alert the user: 'Signal Detector has been down for "
            f"{_tracker.consecutive_failures} consecutive messages. "
            "Check DEEPSEEK_API_KEY and network.'\n"
            "[/SIGNAL DETECTOR DEGRADED]\n"
        )

    # level == 3 — Broken: 50+ consecutive failures
    return (
        "\n[SIGNAL DETECTOR BROKEN — CRITICAL]\n"
        f"{diag}\n"
        "The signal detector has been non-functional for 50+ consecutive messages. "
        "NO brain context surfacing or write detection is happening. "
        "IMMEDIATE ACTION REQUIRED: tell the user the Signal Detector plugin "
        "appears broken and needs investigation. Check:\n"
        "1. DEEPSEEK_API_KEY is valid and not expired\n"
        "2. api.deepseek.com is reachable from this host\n"
        "3. Plugin logs at ~/.hermes/logs/agent.log\n"
        "[/SIGNAL DETECTOR BROKEN]\n"
    )


def reset_tracker() -> None:
    """Reset the failure tracker (e.g., after fixing configuration)."""
    with _tracker_lock:
        _tracker.reset()
    logger.info("signal-detector: failure tracker reset")
