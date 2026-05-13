"""Tests for the signal-detector plugin.

Covers ``plugins/signal-detector/``:

  * Operational message filtering (fast-path skip)
  * FailureTracker escalation (silent → warning → degraded → broken)
  * Error signal formatting (get_failure_signal)
  * Metrics counters and summary
  * Signal formatting (context + write)
  * classify_message() with mocked DeepSeek API
  * on_pre_llm_call() hook handler integration
  * ApiKeyResolution: _get_api_key() reads from env, config.yaml, and .env
  * Model validation: correct DeepSeek model name in API requests
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_module(name: str, filename: str):
    """Import a plugin module from the repo path.

    Loads classifier.py and metrics.py as submodules of a synthetic
    ``hermes_plugins.signal_detector`` package so relative imports
    (``from .metrics import ...``) resolve correctly.
    """
    import importlib.util
    import types

    repo_root = _repo_root()
    plugin_dir = repo_root / "plugins" / "signal-detector"
    file_path = plugin_dir / filename

    # Ensure the parent namespace exists
    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        ns.__package__ = "hermes_plugins"
        sys.modules["hermes_plugins"] = ns

    # Create the signal_detector package module if it doesn't exist
    pkg_name = "hermes_plugins.signal_detector"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(plugin_dir)]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    # Load the specific file as a submodule
    module_name = f"{pkg_name}.{name}"
    spec = importlib.util.spec_from_file_location(
        module_name, file_path,
        submodule_search_locations=[str(plugin_dir)],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _isolate_hermes_home(tmp_path, monkeypatch):
    """Isolate HERMES_HOME for each test."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home


@pytest.fixture
def classifier():
    """Load the classifier module with a clean failure tracker."""
    mod = _load_module("classifier", "classifier.py")
    mod.reset_tracker()
    return mod


@pytest.fixture
def metrics_mod():
    """Load the metrics module with clean counters."""
    mod = _load_module("metrics", "metrics.py")
    mod.get_metrics().reset()
    return mod


@pytest.fixture
def plugin(classifier, metrics_mod):
    """Load the plugin __init__ module."""
    return _load_module("init", "__init__.py")


# ──────────────────────────────────────────────────────────────────────────────
# Operational filter tests
# ──────────────────────────────────────────────────────────────────────────────

class TestOperationalFilter:
    """Fast-path filter skips short/operational messages."""

    def test_short_messages_filtered(self, classifier):
        assert classifier._is_operational("ok")
        assert classifier._is_operational("hi")
        assert classifier._is_operational("..")

    def test_operational_triggers_filtered(self, classifier):
        for word in ["ok", "okay", "thanks", "thank you", "thx", "got it",
                      "do it", "go ahead", "yes", "no", "yep", "nope",
                      "good", "great", "nice", "perfect", "sure", "done"]:
            assert classifier._is_operational(word), f"'{word}' should be filtered"

    def test_variants_with_punctuation(self, classifier):
        assert classifier._is_operational("ok!")
        assert classifier._is_operational("thanks.")
        assert classifier._is_operational("  sure  ")

    def test_real_messages_not_filtered(self, classifier):
        assert not classifier._is_operational("I met with Sarah about the Q3 roadmap")
        assert not classifier._is_operational("can you check the deployment logs?")
        assert not classifier._is_operational("let's build a new feature for gbrain")

    def test_empty_message_filtered(self, classifier):
        assert classifier._is_operational("")
        assert classifier._is_operational("a")

    def test_set_size(self, classifier):
        """Verify the trigger set has reasonable coverage."""
        triggers = classifier._OPERATIONAL_TRIGGERS
        assert len(triggers) > 15
        assert "ok" in triggers
        assert "thanks" in triggers


# ──────────────────────────────────────────────────────────────────────────────
# FailureTracker tests
# ──────────────────────────────────────────────────────────────────────────────

class TestFailureTracker:
    """FailureTracker escalation logic."""

    def test_starts_silent(self, classifier):
        assert classifier._tracker.escalation_level == 0
        assert not classifier._tracker.should_signal()

    def test_1_or_2_failures_silent(self, classifier):
        classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        assert classifier._tracker.escalation_level == 0
        classifier._tracker.record_failure(classifier.FailureKind.NETWORK)
        assert classifier._tracker.escalation_level == 0

    def test_3_failures_warning(self, classifier):
        for _ in range(3):
            classifier._tracker.record_failure(classifier.FailureKind.AUTH_ERROR)
        assert classifier._tracker.escalation_level == 1
        assert classifier._tracker.should_signal()

    def test_10_failures_degraded(self, classifier):
        for _ in range(10):
            classifier._tracker.record_failure(classifier.FailureKind.SERVER_ERROR)
        assert classifier._tracker.escalation_level == 2

    def test_50_failures_broken(self, classifier):
        for _ in range(50):
            classifier._tracker.record_failure(classifier.FailureKind.PARSE_ERROR)
        assert classifier._tracker.escalation_level == 3

    def test_success_resets(self, classifier):
        for _ in range(5):
            classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        assert classifier._tracker.escalation_level == 1
        classifier._tracker.record_success()
        assert classifier._tracker.escalation_level == 0
        assert classifier._tracker.consecutive_failures == 0

    def test_signal_only_fires_on_level_change(self, classifier):
        # First time hitting 3 → should signal
        for _ in range(3):
            classifier._tracker.record_failure(classifier.FailureKind.AUTH_ERROR)
        assert classifier._tracker.should_signal()
        # Same level, next turn → no signal
        assert not classifier._tracker.should_signal()
        assert not classifier._tracker.should_signal()

    def test_failure_counts_by_kind(self, classifier):
        classifier._tracker.record_failure(classifier.FailureKind.AUTH_ERROR)
        classifier._tracker.record_failure(classifier.FailureKind.AUTH_ERROR)
        classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        assert classifier._tracker.failure_counts[classifier.FailureKind.AUTH_ERROR] == 2
        assert classifier._tracker.failure_counts[classifier.FailureKind.TIMEOUT] == 1

    def test_diagnostic_text(self, classifier):
        for _ in range(5):
            classifier._tracker.record_failure(
                classifier.FailureKind.NETWORK, "Connection refused"
            )
        text = classifier._tracker.diagnostic_text()
        assert "5" in text
        assert "network_error" in text
        assert "Connection refused" in text

    def test_diagnostic_truncates_long_detail(self, classifier):
        long_detail = "x" * 500
        classifier._tracker.record_failure(
            classifier.FailureKind.UNKNOWN, long_detail
        )
        text = classifier._tracker.diagnostic_text()
        assert "..." in text
        assert len(text) < 600

    def test_reset_tracker(self, classifier):
        for _ in range(10):
            classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        assert classifier._tracker.consecutive_failures == 10
        classifier.reset_tracker()
        assert classifier._tracker.consecutive_failures == 0


# ──────────────────────────────────────────────────────────────────────────────
# Error signal formatting tests
# ──────────────────────────────────────────────────────────────────────────────

class TestFailureSignalFormatting:
    """get_failure_signal() returns correctly formatted blocks."""

    def test_no_signal_when_healthy(self, classifier):
        assert classifier.get_failure_signal() is None

    def test_warning_signal_at_level_1(self, classifier):
        for _ in range(3):
            classifier._tracker.record_failure(
                classifier.FailureKind.AUTH_ERROR, "Invalid API key"
            )
        signal = classifier.get_failure_signal()
        assert signal is not None
        assert "SIGNAL DETECTOR WARNING" in signal
        assert "auth_error" in signal
        assert "Invalid API key" in signal

    def test_degraded_signal_at_level_2(self, classifier):
        for _ in range(10):
            classifier._tracker.record_failure(classifier.FailureKind.SERVER_ERROR)
        signal = classifier.get_failure_signal()
        assert signal is not None
        assert "SIGNAL DETECTOR DEGRADED" in signal
        assert "NOT functioning" in signal

    def test_broken_signal_at_level_3(self, classifier):
        for _ in range(50):
            classifier._tracker.record_failure(classifier.FailureKind.PARSE_ERROR)
        signal = classifier.get_failure_signal()
        assert signal is not None
        assert "SIGNAL DETECTOR BROKEN" in signal
        assert "IMMEDIATE ACTION REQUIRED" in signal
        assert "DEEPSEEK_API_KEY" in signal

    def test_no_duplicate_signal(self, classifier):
        for _ in range(3):
            classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        signal1 = classifier.get_failure_signal()
        assert signal1 is not None
        signal2 = classifier.get_failure_signal()
        assert signal2 is None  # shouldn't re-fire

    def test_signal_clears_after_recovery(self, classifier):
        for _ in range(5):
            classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        assert classifier.get_failure_signal() is not None
        classifier._tracker.record_success()
        assert classifier.get_failure_signal() is None


# ──────────────────────────────────────────────────────────────────────────────
# Metrics tests
# ──────────────────────────────────────────────────────────────────────────────

class TestMetrics:
    """Metrics counters and summary."""

    def test_starts_at_zero(self, metrics_mod):
        m = metrics_mod.get_metrics()
        assert m.messages_seen == 0
        assert m.classifications_run == 0
        assert m.context_signals_fired == 0

    def test_record_message(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_message()
        m.record_message()
        assert m.messages_seen == 2

    def test_record_filtered(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_message()
        m.record_filtered()
        m.record_message()
        assert m.messages_seen == 2
        assert m.operational_filtered == 1

    def test_record_classification_success(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_classification(success=True, elapsed_ms=250.0)
        assert m.classifications_run == 1
        assert m.classifications_ok == 1
        assert m.classifications_failed == 0
        assert m.total_classify_time_ms == 250.0
        assert m.min_classify_time_ms == 250.0
        assert m.max_classify_time_ms == 250.0

    def test_record_classification_failure(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_classification(success=False)
        assert m.classifications_run == 1
        assert m.classifications_ok == 0
        assert m.classifications_failed == 1

    def test_record_signals_context(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_signals(session_id="s1", context=True)
        assert m.context_signals_fired == 1
        assert m.write_signals_fired == 0

    def test_record_signals_write(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_signals(session_id="s1", write=True, write_type="entity")
        assert m.write_signals_fired == 1
        assert m.write_entity == 1

    def test_record_signals_write_types(self, metrics_mod):
        m = metrics_mod.get_metrics()
        for wt in ["entity", "idea", "decision", "correction", "state_change"]:
            m.record_signals(session_id="s1", write=True, write_type=wt)
        assert m.write_signals_fired == 5
        assert m.write_entity == 1
        assert m.write_idea == 1
        assert m.write_decision == 1
        assert m.write_correction == 1
        assert m.write_state_change == 1
        assert m.write_other == 0

    def test_record_signals_unknown_type(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_signals(session_id="s1", write=True, write_type="weird_thing")
        assert m.write_other == 1

    def test_per_session_tracking(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_signals(session_id="abc", context=True, write=True, write_type="idea")
        m.record_signals(session_id="abc", context=True)
        m.record_signals(session_id="xyz", write=True, write_type="entity")
        assert len(m.sessions) == 2
        assert m.sessions["abc"].context_signals == 2
        assert m.sessions["abc"].write_signals == 1
        assert m.sessions["xyz"].context_signals == 0

    def test_summary_format(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_message()
        m.record_classification(success=True, elapsed_ms=100.0)
        m.record_signals(session_id="s1", context=True, write=True, write_type="decision")
        summary = m.summary()
        assert "Signal Detector Metrics" in summary
        assert "Pipeline" in summary
        assert "Signals" in summary
        assert "Latency" in summary
        assert "Cost" in summary

    def test_cost_estimate(self, metrics_mod):
        m = metrics_mod.get_metrics()
        for _ in range(100):
            m.record_classification(success=True)
        assert m.estimated_cost_usd == 0.014  # 100 × $0.00014

    def test_classification_rate(self, metrics_mod):
        m = metrics_mod.get_metrics()
        for _ in range(10):
            m.record_message()
        # Simulate 3 filtered, 7 classified
        for _ in range(3):
            m.record_filtered()
        for _ in range(7):
            m.record_classification(success=True)
        assert m.classification_rate == 0.7

    def test_hit_rates(self, metrics_mod):
        m = metrics_mod.get_metrics()
        for _ in range(10):
            m.record_classification(success=True)
        m.record_signals(session_id="s1", context=True)
        m.record_signals(session_id="s1", context=True)
        m.record_signals(session_id="s1", write=True, write_type="idea")
        assert m.context_hit_rate == 0.2
        assert m.write_hit_rate == 0.1

    def test_to_dict(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_message()
        m.record_classification(success=True)
        d = m.to_dict()
        assert d["messages_seen"] == 1
        assert d["classifications_ok"] == 1
        assert "latency" in d

    def test_reset(self, metrics_mod):
        m = metrics_mod.get_metrics()
        m.record_message()
        m.record_classification(success=True)
        m.reset()
        assert m.messages_seen == 0
        assert m.classifications_run == 0


# ──────────────────────────────────────────────────────────────────────────────
# Signal formatting tests
# ──────────────────────────────────────────────────────────────────────────────

class TestSignalFormatting:
    """Context and write signal formatters produce correct output."""

    def test_context_signal_basic(self, plugin):
        classification = {
            "query_brain": True,
            "entities": ["Acme Corp", "Sarah"],
            "reasoning": "User mentions new people and a company",
        }
        signal = plugin._format_context_signal(classification)
        assert "BRAIN CONTEXT NEEDED" in signal
        assert "Acme Corp, Sarah" in signal
        assert "User mentions" in signal
        assert "gbrain-query skill" in signal
        assert "second-brain skill" in signal

    def test_context_signal_no_entities(self, plugin):
        classification = {"query_brain": True, "entities": [], "reasoning": ""}
        signal = plugin._format_context_signal(classification)
        assert "BRAIN CONTEXT NEEDED" in signal
        assert "entities:" not in signal

    def test_context_signal_references_skills_not_inline_logic(self, plugin):
        """Signal should reference skills, not duplicate query logic."""
        classification = {"query_brain": True, "entities": ["test"]}
        signal = plugin._format_context_signal(classification)
        assert "gbrain-query skill" in signal
        assert "mcp_gbrain_search" not in signal

    def test_write_signal_basic(self, plugin):
        classification = {
            "write_signal": True,
            "write_type": "decision",
            "write_summary": "Decided to use Postgres for gbrain",
            "entities": ["gbrain", "Postgres"],
        }
        signal = plugin._format_write_signal(classification)
        assert "SIGNAL: possible write needed" in signal
        assert "DECISION" in signal
        assert "Decided to use Postgres" in signal
        assert "gbrain, Postgres" in signal
        assert "gbrain-page-writer skill" in signal
        assert "Iron Laws" in signal

    def test_write_signal_no_entities(self, plugin):
        classification = {
            "write_signal": True,
            "write_type": "idea",
            "write_summary": "Random shower thought",
            "entities": [],
        }
        signal = plugin._format_write_signal(classification)
        assert "IDEA" in signal
        assert "entities:" not in signal

    def test_write_signal_references_skills_not_inline_logic(self, plugin):
        """Signal should reference skills, not duplicate write logic."""
        classification = {
            "write_signal": True,
            "write_type": "entity",
            "write_summary": "New person",
            "entities": ["Alice"],
        }
        signal = plugin._format_write_signal(classification)
        assert "gbrain-page-writer skill" in signal
        assert "mcp_gbrain_search" not in signal


# ──────────────────────────────────────────────────────────────────────────────
# API key resolution tests
# ──────────────────────────────────────────────────────────────────────────────

class TestApiKeyResolution:
    """_get_api_key() resolution from env, config.yaml, and .env file."""

    def test_reads_from_env_variable(self, classifier):
        """Key in os.environ should be found."""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-env-key"}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-env-key"

    def test_reads_from_config_yaml(self, classifier, _isolate_hermes_home):
        """Key in config.yaml → providers.deepseek.api_key should be found."""
        hermes_home = _isolate_hermes_home
        import yaml
        config = {"providers": {"deepseek": {"api_key": "sk-config-key"}}}
        with open(hermes_home / "config.yaml", "w") as f:
            yaml.dump(config, f)
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-config-key"

    def test_reads_from_env_file(self, classifier, _isolate_hermes_home):
        """Key in .env file should be found when not in env or config."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-dotenv-key\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-dotenv-key"

    def test_env_file_key_with_double_quotes(self, classifier, _isolate_hermes_home):
        """Key in .env with double quotes should be stripped."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY="sk-quoted-key"\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-quoted-key"

    def test_env_file_key_with_single_quotes(self, classifier, _isolate_hermes_home):
        """Key in .env with single quotes should be stripped."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text("DEEPSEEK_API_KEY='sk-single-quoted'\n")
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-single-quoted"

    def test_env_file_key_with_extra_whitespace(self, classifier, _isolate_hermes_home):
        """Key in .env with leading/trailing whitespace around value."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=  sk-spaced-key  \n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-spaced-key"

    def test_env_file_key_empty_value(self, classifier, _isolate_hermes_home):
        """Empty value in .env should return None."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key is None or key == ""

    def test_env_priority_over_config_and_dotenv(self, classifier, _isolate_hermes_home):
        """os.environ should win over both config.yaml and .env."""
        hermes_home = _isolate_hermes_home
        import yaml
        config = {"providers": {"deepseek": {"api_key": "sk-config"}}}
        with open(hermes_home / "config.yaml", "w") as f:
            yaml.dump(config, f)
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-dotenv\n')
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-env-wins", "HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-env-wins"

    def test_config_priority_over_dotenv(self, classifier, _isolate_hermes_home):
        """config.yaml should win over .env when env is not set."""
        hermes_home = _isolate_hermes_home
        import yaml
        config = {"providers": {"deepseek": {"api_key": "sk-config-wins"}}}
        with open(hermes_home / "config.yaml", "w") as f:
            yaml.dump(config, f)
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-dotenv-loses\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-config-wins"

    def test_handles_missing_env_file(self, classifier, _isolate_hermes_home):
        """No .env file should not crash — returns None gracefully."""
        hermes_home = _isolate_hermes_home
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            # No config.yaml, no .env file
            key = classifier._get_api_key()
            assert key is None

    def test_handles_missing_config_file(self, classifier, _isolate_hermes_home):
        """No config.yaml should fall through to .env gracefully."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-only-env\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-only-env"

    def test_env_file_ignored_when_env_is_set(self, classifier, _isolate_hermes_home):
        """.env should NOT be read when os.environ has the key."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-should-be-ignored\n')
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-direct", "HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-direct"

    def test_config_without_deepseek_section(self, classifier, _isolate_hermes_home):
        """config.yaml without providers.deepseek should fall through to .env."""
        hermes_home = _isolate_hermes_home
        import yaml
        config = {"providers": {"openai": {"api_key": "sk-openai"}}}
        with open(hermes_home / "config.yaml", "w") as f:
            yaml.dump(config, f)
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-fallback\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            key = classifier._get_api_key()
            assert key == "sk-fallback"


# ──────────────────────────────────────────────────────────────────────────────
# classify_message tests (with mocked DeepSeek API)
# ──────────────────────────────────────────────────────────────────────────────

class TestClassifyMessage:
    """classify_message() with mocked HTTP calls."""

    def _mock_response(self, status=200, content=None):
        """Create a mock httpx response."""
        if content is None:
            content = '{"query_brain": true, "write_signal": false, "entities": ["test"], "write_type": null, "write_summary": null, "reasoning": "test entity"}'
        mock = MagicMock()
        mock.status_code = status
        mock.text = content if status != 200 else ""
        mock.json.return_value = {
            "choices": [{"message": {"content": content}}]
        }
        return mock

    def test_operational_skipped(self, classifier):
        result = classifier.classify_message("ok")
        assert result is None

    def test_successful_classification(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(
                content='{"query_brain": true, "write_signal": false, "entities": ["TestCorp"], "write_type": null, "write_summary": null, "reasoning": "entity mentioned"}'
            )
            result = classifier.classify_message("I work at TestCorp")
            assert result is not None
            assert result["query_brain"] is True
            assert result["write_signal"] is False
            assert "TestCorp" in result["entities"]

    def test_write_detection(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(
                content='{"query_brain": false, "write_signal": true, "entities": ["Sarah"], "write_type": "entity", "write_summary": "New person Sarah from Acme", "reasoning": "new entity"}'
            )
            result = classifier.classify_message("I met Sarah from Acme today")
            assert result is not None
            assert result["write_signal"] is True
            assert result["write_type"] == "entity"
            assert "Sarah" in result["entities"]

    def test_both_signals(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(
                content='{"query_brain": true, "write_signal": true, "entities": ["Q3 roadmap", "Acme"], "write_type": "decision", "write_summary": "Q3 roadmap discussion with Acme", "reasoning": "decision about roadmap"}'
            )
            result = classifier.classify_message("Decided Q3 roadmap with Acme")
            assert result["query_brain"] is True
            assert result["write_signal"] is True

    def test_neither_signal(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(
                content='{"query_brain": false, "write_signal": false, "entities": [], "write_type": null, "write_summary": null, "reasoning": "casual chat"}'
            )
            result = classifier.classify_message("how's it going?")
            assert result["query_brain"] is False
            assert result["write_signal"] is False

    def test_handles_json_in_code_fence(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock = self._mock_response()
            mock.json.return_value = {
                "choices": [{"message": {
                    "content": '```json\n{"query_brain": true, "write_signal": false, "entities": ["x"], "write_type": null, "write_summary": null, "reasoning": "t"}\n```'
                }}]
            }
            mock_post.return_value = mock
            result = classifier.classify_message("test")
            assert result["query_brain"] is True

    def test_no_api_key_returns_none(self, classifier, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # Also clear any cached key from config
        import os
        monkeypatch.setattr(os, "environ", {})
        # Ensure _get_api_key returns None by patching it
        monkeypatch.setattr(classifier, "_get_api_key", lambda: None)
        result = classifier.classify_message("test entity")
        assert result is None

    def test_http_401_records_auth_failure(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(status=401, content="Unauthorized")
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.consecutive_failures == 1
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.AUTH_ERROR
            # Classification failure should be recorded in metrics
            from hermes_plugins.signal_detector.metrics import get_metrics
            assert get_metrics().classifications_failed >= 1

    def test_http_429_records_rate_limit(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(status=429, content="Too many requests")
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.RATE_LIMIT

    def test_http_500_records_server_error(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(status=500, content="Internal error")
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.SERVER_ERROR

    def test_timeout_records_timeout(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        import httpx
        with patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.TIMEOUT

    def test_network_error(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        import httpx
        with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.NETWORK

    def test_parse_error(self, classifier, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response(
                content="not valid json at all"
            )
            result = classifier.classify_message("test")
            assert result is None
            assert classifier._tracker.last_failure_kind == classifier.FailureKind.PARSE_ERROR

    def test_conversation_history_context(self, classifier, monkeypatch):
        """Verify conversation history is included in the prompt."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response()
            history = [
                {"role": "user", "content": "previous question"},
                {"role": "assistant", "content": "previous answer with enough characters to meet the minimum length threshold for inclusion"},
            ]
            classifier.classify_message("test", conversation_history=history)
            call_args = mock_post.call_args
            messages = call_args[1]["json"]["messages"]
            # Should include the assistant context
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            assert len(assistant_msgs) >= 1

    def test_metrics_recorded_on_classify(self, classifier, monkeypatch):
        """Verify metrics are recorded during classification."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response()
            classifier.classify_message("test entity")
        from hermes_plugins.signal_detector.metrics import get_metrics
        m = get_metrics()
        assert m.messages_seen >= 1
        assert m.classifications_ok >= 1

    def test_classify_with_key_from_env_file_only(self, classifier, _isolate_hermes_home):
        """End-to-end: classification succeeds when key is only in .env file."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-from-dotenv\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            with patch("httpx.post") as mock_post:
                mock_post.return_value = self._mock_response(
                    content='{"query_brain": true, "write_signal": false, "entities": ["TestCorp"], "write_type": null, "write_summary": null, "reasoning": "found via .env"}'
                )
                result = classifier.classify_message("I work at TestCorp")
                assert result is not None
                assert result["query_brain"] is True
                assert result["reasoning"] == "found via .env"

    def test_uses_deepseek_chat_model(self, classifier, monkeypatch):
        """Verify the API request uses 'deepseek-chat' model, not a non-standard name."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = self._mock_response()
            classifier.classify_message("test entity")
            call_kwargs = mock_post.call_args[1]
            json_body = call_kwargs["json"]
            assert json_body["model"] == "deepseek-chat", (
                f"Expected model 'deepseek-chat', got '{json_body['model']}'"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Hook handler integration tests
# ──────────────────────────────────────────────────────────────────────────────

class TestHookHandler:
    """on_pre_llm_call() hook handler."""

    def _mock_hook_call(self, plugin, user_message, **kwargs):
        """Helper to call the hook with defaults."""
        defaults = {
            "session_id": "test-session",
            "user_message": user_message,
            "conversation_history": [],
            "is_first_turn": True,
            "model": "test-model",
            "platform": "discord",
        }
        defaults.update(kwargs)
        return plugin.on_pre_llm_call(**defaults)

    def test_empty_message_returns_none(self, plugin):
        assert self._mock_hook_call(plugin, "") is None
        assert self._mock_hook_call(plugin, "   ") is None

    def test_operational_message_no_signal(self, plugin):
        result = self._mock_hook_call(plugin, "ok")
        assert result is None

    def test_context_signal_injected(self, plugin, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = _make_mock_response(
                query_brain=True, write_signal=False
            )
            result = self._mock_hook_call(plugin, "tell me about the Q3 roadmap")
            assert result is not None
            assert "context" in result
            assert "BRAIN CONTEXT NEEDED" in result["context"]

    def test_write_signal_injected(self, plugin, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = _make_mock_response(
                query_brain=False, write_signal=True,
                write_type="idea", write_summary="Great new feature idea"
            )
            result = self._mock_hook_call(plugin, "what if we added a nudge system?")
            assert result is not None
            assert "SIGNAL: possible write needed" in result["context"]
            assert "IDEA" in result["context"]

    def test_both_signals_injected(self, plugin, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = _make_mock_response(
                query_brain=True, write_signal=True,
                write_type="entity", write_summary="Met Sarah from Acme"
            )
            result = self._mock_hook_call(plugin, "met Sarah from Acme about the Q3 deal")
            assert "BRAIN CONTEXT NEEDED" in result["context"]
            assert "SIGNAL: possible write needed" in result["context"]

    def test_error_signal_before_classification(self, plugin, classifier, monkeypatch):
        """Error escalation signals appear even when classification fails."""
        # Use the same classifier module that the plugin uses
        with classifier._tracker_lock:
            for _ in range(3):
                classifier._tracker.record_failure(classifier.FailureKind.TIMEOUT)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")

        with patch("httpx.post", side_effect=Exception("boom")):
            result = self._mock_hook_call(plugin, "test message")
            assert result is not None
            assert "SIGNAL DETECTOR WARNING" in result["context"]

        # Clean up: reset tracker so other tests aren't contaminated
        classifier.reset_tracker()

    def test_never_raises(self, plugin):
        """Hook should never raise, even on catastrophic input."""
        # The hook handles non-string gracefully by checking .strip()
        result = plugin.on_pre_llm_call(
            session_id="test",
            user_message="",  # empty string — handled
        )
        assert result is None

    def test_returns_context_dict_format(self, plugin, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")
        with patch("httpx.post") as mock_post:
            mock_post.return_value = _make_mock_response(
                query_brain=True, write_signal=False
            )
            result = self._mock_hook_call(plugin, "test entity")
            assert isinstance(result, dict)
            assert "context" in result
            assert isinstance(result["context"], str)

    def test_hook_works_with_key_from_env_file_only(self, plugin, _isolate_hermes_home):
        """Hook handler can classify when DEEPSEEK_API_KEY is only in .env file."""
        hermes_home = _isolate_hermes_home
        (hermes_home / ".env").write_text('DEEPSEEK_API_KEY=sk-hook-dotenv\n')
        with patch.dict("os.environ", {"HERMES_HOME": str(hermes_home)}, clear=True):
            with patch("httpx.post") as mock_post:
                mock_post.return_value = _make_mock_response(
                    query_brain=True, write_signal=False,
                    entities=["TestEntity"], reasoning="hook with .env key works"
                )
                result = self._mock_hook_call(plugin, "tell me about TestEntity")
                assert result is not None
                assert "BRAIN CONTEXT NEEDED" in result["context"]
                assert "TestEntity" in result["context"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers for hook tests
# ──────────────────────────────────────────────────────────────────────────────

def _make_mock_response(query_brain=False, write_signal=False,
                        entities=None, write_type=None, write_summary=None,
                        reasoning=""):
    """Create a mock httpx.Response with classifier JSON."""
    import json as _json
    content = _json.dumps({
        "query_brain": query_brain,
        "write_signal": write_signal,
        "entities": entities or [],
        "write_type": write_type,
        "write_summary": write_summary,
        "reasoning": reasoning,
    })
    mock = MagicMock()
    mock.status_code = 200
    mock.text = ""
    mock.json.return_value = {"choices": [{"message": {"content": content}}]}
    return mock
