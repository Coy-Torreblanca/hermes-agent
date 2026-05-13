"""Signal Detector metrics — usage counters and diagnostic tools.

Tracks:
- Messages seen vs filtered vs classified
- Signal fire rates (READ path hits, WRITE path hits)
- Write-type breakdown (entity, idea, decision, correction, state_change)
- Cost estimates (DeepSeek API calls × ~$0.0001/msg)
- Per-session signal counts

Use `get_metrics().summary()` for a formatted stats block.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Metrics store
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SignalMetrics:
    """Per-session signal counters."""
    session_id: str = ""
    context_signals: int = 0        # READ path hits
    write_signals: int = 0          # WRITE path hits
    write_entity: int = 0
    write_idea: int = 0
    write_decision: int = 0
    write_correction: int = 0
    write_state_change: int = 0
    first_seen: float = field(default_factory=time.monotonic)


@dataclass
class Metrics:
    """Global metrics for the Signal Detector plugin."""

    # ── Message pipeline ──────────────────────────────────────────────
    messages_seen: int = 0          # Total messages processed
    operational_filtered: int = 0   # Skipped (fast-path filter)
    classifications_run: int = 0    # Sent to DeepSeek
    classifications_ok: int = 0     # Successful classifications
    classifications_failed: int = 0 # Failed classifications

    # ── Signal outcomes ───────────────────────────────────────────────
    context_signals_fired: int = 0  # [BRAIN CONTEXT NEEDED] injected
    write_signals_fired: int = 0    # [SIGNAL: write needed] injected
    error_signals_fired: int = 0    # Error escalation signals injected

    # ── Write signal breakdown ────────────────────────────────────────
    write_entity: int = 0
    write_idea: int = 0
    write_decision: int = 0
    write_correction: int = 0
    write_state_change: int = 0
    write_other: int = 0

    # ── Timing ────────────────────────────────────────────────────────
    total_classify_time_ms: float = 0.0
    min_classify_time_ms: float = 0.0
    max_classify_time_ms: float = 0.0

    # ── Startup ───────────────────────────────────────────────────────
    started_at: float = field(default_factory=time.monotonic)
    last_summary_at: float = 0.0

    # Per-session tracking
    sessions: Dict[str, SignalMetrics] = field(default_factory=dict)

    # ── Cost estimate ─────────────────────────────────────────────────
    @property
    def estimated_cost_usd(self) -> float:
        """Rough cost estimate at ~$0.00014/msg (DeepSeek chat input pricing)."""
        return round(self.classifications_run * 0.00014, 4)

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self.started_at

    @property
    def messages_per_minute(self) -> float:
        uptime = self.uptime_seconds
        if uptime < 60:
            return 0.0
        return round(self.messages_seen / (uptime / 60), 1)

    @property
    def classification_rate(self) -> float:
        """Fraction of messages that reach the classifier (excl. filtered)."""
        if self.messages_seen == 0:
            return 0.0
        return round(self.classifications_run / self.messages_seen, 3)

    @property
    def context_hit_rate(self) -> float:
        """Fraction of classified messages that trigger context surfacing."""
        if self.classifications_ok == 0:
            return 0.0
        return round(self.context_signals_fired / self.classifications_ok, 3)

    @property
    def write_hit_rate(self) -> float:
        """Fraction of classified messages that trigger write detection."""
        if self.classifications_ok == 0:
            return 0.0
        return round(self.write_signals_fired / self.classifications_ok, 3)

    # ── Recording helpers ─────────────────────────────────────────────

    def record_message(self) -> None:
        self.messages_seen += 1

    def record_filtered(self) -> None:
        self.operational_filtered += 1

    def record_classification(self, success: bool, elapsed_ms: float = 0.0) -> None:
        self.classifications_run += 1
        if success:
            self.classifications_ok += 1
        else:
            self.classifications_failed += 1
        if elapsed_ms > 0:
            self.total_classify_time_ms += elapsed_ms
            if self.min_classify_time_ms == 0 or elapsed_ms < self.min_classify_time_ms:
                self.min_classify_time_ms = elapsed_ms
            if elapsed_ms > self.max_classify_time_ms:
                self.max_classify_time_ms = elapsed_ms

    def record_signals(
        self,
        session_id: str,
        context: bool = False,
        write: bool = False,
        write_type: str = "",
        error: bool = False,
    ) -> None:
        """Record signal fire events."""
        if context:
            self.context_signals_fired += 1
        if write:
            self.write_signals_fired += 1
            # Break down by type
            wt = (write_type or "").lower()
            if wt == "entity":
                self.write_entity += 1
            elif wt == "idea":
                self.write_idea += 1
            elif wt == "decision":
                self.write_decision += 1
            elif wt == "correction":
                self.write_correction += 1
            elif wt == "state_change":
                self.write_state_change += 1
            else:
                self.write_other += 1
        if error:
            self.error_signals_fired += 1

        # Per-session tracking
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = SignalMetrics(session_id=session_id)
            sm = self.sessions[session_id]
            if context:
                sm.context_signals += 1
            if write:
                sm.write_signals += 1
                wt = (write_type or "").lower()
                if wt == "entity":
                    sm.write_entity += 1
                elif wt == "idea":
                    sm.write_idea += 1
                elif wt == "decision":
                    sm.write_decision += 1
                elif wt == "correction":
                    sm.write_correction += 1
                elif wt == "state_change":
                    sm.write_state_change += 1

    # ── Summary ───────────────────────────────────────────────────────

    def summary(self) -> str:
        """Return a formatted summary of all metrics."""
        uptime = self.uptime_seconds
        uptime_str = f"{uptime:.0f}s" if uptime < 3600 else f"{uptime / 3600:.1f}h"

        lines = [
            "═══ Signal Detector Metrics ═══",
            f"Uptime: {uptime_str}  |  Process: {self.messages_seen} msgs ({self.messages_per_minute}/min)",
            "",
            "─ Pipeline ─",
            f"  Seen:              {self.messages_seen:>6}",
            f"  Filtered (ops):    {self.operational_filtered:>6}  ({self.operational_filtered / max(1, self.messages_seen) * 100:.0f}%)",
            f"  Classified:        {self.classifications_run:>6}  ({self.classification_rate * 100:.0f}%)",
            f"  └─ OK:             {self.classifications_ok:>6}",
            f"  └─ Failed:         {self.classifications_failed:>6}",
            "",
            "─ Signals ─",
            f"  Context (READ):    {self.context_signals_fired:>6}  ({self.context_hit_rate * 100:.0f}% of classified)",
            f"  Write (WRITE):     {self.write_signals_fired:>6}  ({self.write_hit_rate * 100:.0f}% of classified)",
            f"  Errors injected:   {self.error_signals_fired:>6}",
        ]

        # Write breakdown
        if self.write_signals_fired > 0:
            lines.append("")
            lines.append("─ Write Breakdown ─")
            lines.append(f"  entity:           {self.write_entity:>6}")
            lines.append(f"  idea:             {self.write_idea:>6}")
            lines.append(f"  decision:         {self.write_decision:>6}")
            lines.append(f"  correction:       {self.write_correction:>6}")
            lines.append(f"  state_change:     {self.write_state_change:>6}")
            lines.append(f"  other:            {self.write_other:>6}")

        # Timing
        if self.classifications_run > 0:
            avg_ms = self.total_classify_time_ms / self.classifications_run
            lines.append("")
            lines.append("─ Latency ─")
            lines.append(f"  Avg classify:     {avg_ms:.0f}ms")
            lines.append(f"  Min:              {self.min_classify_time_ms:.0f}ms")
            lines.append(f"  Max:              {self.max_classify_time_ms:.0f}ms")

        # Cost
        lines.append("")
        lines.append(f"─ Cost ─")
        lines.append(f"  Est. total:       ${self.estimated_cost_usd:.4f}")
        lines.append(f"  Rate:             ${self.estimated_cost_usd / max(1, uptime) * 3600:.4f}/hr")

        # Sessions
        if self.sessions:
            lines.append("")
            lines.append(f"─ Sessions ({len(self.sessions)}) ─")
            for sid, sm in sorted(self.sessions.items(), key=lambda x: -x[1].first_seen)[:5]:
                lines.append(
                    f"  {sid[-16:]}:  {sm.context_signals}C/{sm.write_signals}W"
                )

        lines.append("")
        lines.append("══════════════════════════════════")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as a dict (for JSON logging or API use)."""
        return {
            "messages_seen": self.messages_seen,
            "operational_filtered": self.operational_filtered,
            "classifications_run": self.classifications_run,
            "classifications_ok": self.classifications_ok,
            "classifications_failed": self.classifications_failed,
            "context_signals_fired": self.context_signals_fired,
            "write_signals_fired": self.write_signals_fired,
            "error_signals_fired": self.error_signals_fired,
            "write_breakdown": {
                "entity": self.write_entity,
                "idea": self.write_idea,
                "decision": self.write_decision,
                "correction": self.write_correction,
                "state_change": self.write_state_change,
                "other": self.write_other,
            },
            "latency": {
                "avg_ms": self.total_classify_time_ms / max(1, self.classifications_run),
                "min_ms": self.min_classify_time_ms,
                "max_ms": self.max_classify_time_ms,
            },
            "estimated_cost_usd": self.estimated_cost_usd,
            "uptime_seconds": self.uptime_seconds,
            "session_count": len(self.sessions),
        }

    def reset(self) -> None:
        """Reset all counters (useful for testing)."""
        self.messages_seen = 0
        self.operational_filtered = 0
        self.classifications_run = 0
        self.classifications_ok = 0
        self.classifications_failed = 0
        self.context_signals_fired = 0
        self.write_signals_fired = 0
        self.error_signals_fired = 0
        self.write_entity = 0
        self.write_idea = 0
        self.write_decision = 0
        self.write_correction = 0
        self.write_state_change = 0
        self.write_other = 0
        self.total_classify_time_ms = 0.0
        self.min_classify_time_ms = 0.0
        self.max_classify_time_ms = 0.0
        self.started_at = time.monotonic()
        self.last_summary_at = 0.0
        self.sessions.clear()


# Module-level singleton
_metrics = Metrics()
_metrics_lock = threading.Lock()


def get_metrics() -> Metrics:
    """Return the global metrics singleton."""
    return _metrics


def get_metrics_lock() -> threading.Lock:
    """Return the global metrics lock."""
    return _metrics_lock
