# Signal Detector Plugin

Hermes `pre_llm_call` plugin — unified READ + WRITE layer for the Second Brain.

## What It Does

Fires **before every LLM turn** and classifies the user message via DeepSeek Fast:

| Path | What | Cost |
|---|---|---|
| **Fast-path filter** | Skips operational messages ("ok", "thanks", short msgs) | Free |
| **READ: Context Surfacing** | Detects entities, questions, concepts → injects `[BRAIN CONTEXT NEEDED]` | ~$0.0001 |
| **WRITE: Write Detection** | Detects new entities, decisions, ideas → injects `[SIGNAL: write needed — …]` | ~$0.0001 |

The agent then acts on these signals using the **gbrain-query**, **second-brain**, and **gbrain-page-writer** skills.

## Files

```
plugins/signal-detector/
├── plugin.yaml       # manifest (standalone, pre_llm_call hook)
├── __init__.py        # hook handler + signal formatters
├── classifier.py      # DeepSeek classification + FailureTracker + diagnose()
└── metrics.py         # Signal counters + formatted summary
```

## Setup

### 1. Enable the plugin

```bash
hermes plugins enable signal-detector
```

This adds `signal-detector` to `plugins.enabled` in your Hermes config. Verify:

```bash
hermes plugins list
# → signal-detector  standalone  enabled: true

### 2. Set the DeepSeek API key

**Option A — environment variable:**
```bash
export DEEPSEEK_API_KEY="sk-..."
```

**Option B — Hermes providers config** (in `~/.hermes/config.yaml`):
```yaml
providers:
  deepseek:
    api_key: "sk-..."
```

Get a key at https://platform.deepseek.com/api_keys

### 3. Restart Hermes

The plugin is discovered at startup. Restart your Hermes process.

### 4. Verify

Check the logs:
```
signal-detector plugin registered (pre_llm_call hook)
```

Every 50 messages, a metrics summary is logged:
```
═══ Signal Detector Metrics ═══
Uptime: 2.3h  |  Process: 847 msgs (6.1/min)

─ Pipeline ─
  Seen:                 847
  Filtered (ops):       312  (37%)
  Classified:           535  (63%)
  └─ OK:                528
  └─ Failed:              7
─ Signals ─
  Context (READ):       142  (27% of classified)
  Write (WRITE):         38  (7% of classified)
─ Cost ─
  Est. total:        $0.0752
```

**Live Logs** - 
```
# ── LIVE WATCH (most useful) ──
tail -f ~/.hermes/logs/agent.log | grep -i "signal-detector\|classif\|timeout"

# ── CHECK REGISTRATIONS ──
grep "registered.*signal" ~/.hermes/logs/agent.log

# ── CHECK ACTUAL CLASSIFICATIONS ──
grep "classif" ~/.hermes/logs/agent.log

# ── CHECK FAILURES ──
grep -E "timeout|failed|error.*signal|NO_API_KEY" ~/.hermes/logs/agent.log

# ── CHECK MCP ERRORS ──
tail -30 ~/.hermes/logs/mcp-stderr.log

# ── CHECK WHAT PLUGINS ARE ENABLED ──
hermes plugins list | grep signal
```

## Testing / Diagnostics

### Test a specific message

```python
from plugins.signal_detector.classifier import diagnose
print(diagnose("I met with Sarah from Acme Corp about the Q3 roadmap"))
# → query_brain: true, write_signal: true, entities: ["Sarah", "Acme Corp", "Q3 roadmap"]
```

### View live metrics

```python
from plugins.signal_detector.metrics import get_metrics
print(get_metrics().summary())
```

### Monitor error escalation

The plugin tracks consecutive failures:
- **3+ failures**: injects `[SIGNAL DETECTOR WARNING]` into agent context
- **10+ failures**: injects `[SIGNAL DETECTOR DEGRADED]` — agent told to alert user
- **50+ failures**: injects `[SIGNAL DETECTOR BROKEN]` — "IMMEDIATE ACTION REQUIRED"

Any successful classification resets the counter.

## Architecture

```
User message
    │
    ▼
┌─────────────────────────────┐
│ Signal Detector (pre_llm_call)│
│                             │
│ 1. Fast-path filter         │  ← skips "ok", "thanks", <3 chars
│ 2. DeepSeek classify        │  ← ~$0.0001/msg, 5s timeout
│ 3. Inject signals           │  ← text only, silent to user
└─────────────────────────────┘
    │
    ▼
[BRAIN CONTEXT NEEDED]          ← agent loads gbrain-query skill
[SIGNAL: write needed — IDEA]   ← agent loads gbrain-page-writer skill
    │
    ▼
Agent's tool-calling loop handles the rest
```

The plugin never calls MCP tools directly — that's the agent's job.
