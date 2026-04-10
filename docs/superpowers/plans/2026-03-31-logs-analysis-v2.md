# Auto-SDLC Logs Analysis v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the `auto-sdlc logs` command with behavioral metrics, a 5-dimension maturity scorer, LLM qualitative analysis via `claude -p`, individual HTML reports with project breakdowns, team rollup from multiple user reports, and a data export mechanism — replacing stdout-by-default with file-by-default output.

**Architecture:** Each new capability lives in its own module under `src/auto_sdlc/logs/`. The `report.py` orchestrator gains new optional stages (metrics → maturity → qualitative) and assembles them into a richer report struct. `render_html.py` consumes the final report dict; `team.py` consumes multiple report dicts; `export.py` ships the data. The CLI grows `--user-id`, `--html`, `--qualitative` flags on `logs` and a new `team` subcommand.

**Tech Stack:** Python 3.9, Click, pytest, subprocess (for `claude -p`), urllib (no requests), inline HTML/CSS (no JS frameworks).

---

## File Structure

```
src/auto_sdlc/
├── logs/
│   ├── parser.py         ← existing, unchanged
│   ├── analyzer.py       ← existing, unchanged
│   ├── scorer.py         ← existing, unchanged
│   ├── metrics.py        ← NEW: behavioral metrics (skill ratio, tool use, session frequency)
│   ├── maturity.py       ← NEW: 5-dimension maturity scoring (0–4 scale)
│   ├── qualitative.py    ← NEW: LLM analysis via `claude -p` subprocess
│   ├── report.py         ← MODIFY: default file output, user_id, project breakdown, new modules
│   ├── render_html.py    ← NEW: individual HTML report renderer
│   ├── team.py           ← NEW: aggregate multiple user reports into team report + HTML
│   └── export.py         ← NEW: write to dir or POST to URL
├── cli.py                ← MODIFY: --user-id, --html, --qualitative flags; team subcommand
tests/
├── conftest.py           ← existing, unchanged
├── logs/
│   ├── test_metrics.py   ← NEW
│   ├── test_maturity.py  ← NEW
│   ├── test_qualitative.py ← NEW
│   ├── test_team.py      ← NEW
│   ├── test_render_html.py ← NEW
│   ├── test_report.py    ← MODIFY: update for new report structure + file-default behavior
│   ├── test_parser.py    ← existing, unchanged
│   ├── test_analyzer.py  ← existing, unchanged
│   └── test_scorer.py    ← existing, unchanged
└── test_cli.py           ← MODIFY: update for new flags + team subcommand
```

---

## JSONL Schema Reminder

Skill/command invocations appear as `user` events with `isMeta: true`. Tool use appears in assistant content:

```json
{"type": "assistant", "message": {
  "content": [{"type": "tool_use", "name": "Bash", "id": "..."}],
  "usage": {"input_tokens": 500, ...}
}}
```

`turn_duration` system events hold `cwd`, `durationMs`, `messageCount`, `gitBranch`, `slug`.

---

## Task 1: Behavioral Metrics

Extract signals beyond token counts: skill/command ratio, tool usage, message density, session frequency.

**Files:**
- Create: `src/auto_sdlc/logs/metrics.py`
- Create: `tests/logs/test_metrics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_metrics.py
import pytest
from auto_sdlc.logs.metrics import extract_behavioral_metrics, aggregate_behavioral_metrics


@pytest.fixture
def session_with_tools():
    return [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "fix the bug"},
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "<local-command-caveat>/compact</local-command-caveat>"},
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:01.000Z"},
        {"type": "assistant", "isMeta": False,
         "message": {
             "content": [
                 {"type": "tool_use", "name": "Bash", "id": "t1"},
                 {"type": "tool_use", "name": "Read", "id": "t2"},
             ],
             "usage": {"input_tokens": 100, "output_tokens": 50,
                       "cache_read_input_tokens": 200, "cache_creation_input_tokens": 80}
         },
         "sessionId": "s1", "timestamp": "2026-03-01T09:00:10.000Z"},
    ]


def test_extract_counts_user_messages(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["user_messages"] == 1


def test_extract_counts_skill_invocations(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["skill_invocations"] == 1


def test_extract_counts_tool_calls(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert result["tool_calls"] == 2


def test_extract_unique_tools(session_with_tools):
    result = extract_behavioral_metrics(session_with_tools)
    assert set(result["unique_tools"]) == {"Bash", "Read"}


def test_aggregate_skill_ratio():
    # 1 skill invocation, 1 user message → ratio = 0.5
    session = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "hello"},
         "sessionId": "x", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": True,
         "message": {"role": "user", "content": "/compact"},
         "sessionId": "x", "timestamp": "2026-03-01T09:00:01.000Z"},
    ]
    result = aggregate_behavioral_metrics([session, session], total_days_active=2)
    assert result["skill_invocation_ratio"] == 0.5
    assert result["sessions_per_day"] == 1.0


def test_aggregate_avg_messages_per_session():
    session_a = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "a"},
         "sessionId": "a", "timestamp": "2026-03-01T09:00:00.000Z"},
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "b"},
         "sessionId": "a", "timestamp": "2026-03-01T09:00:01.000Z"},
    ]
    session_b = [
        {"type": "user", "isMeta": False,
         "message": {"role": "user", "content": "c"},
         "sessionId": "b", "timestamp": "2026-03-01T09:00:00.000Z"},
    ]
    result = aggregate_behavioral_metrics([session_a, session_b], total_days_active=1)
    assert result["avg_messages_per_session"] == 1.5   # (2+1)/2
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/smannar/auto-sdlc
pytest tests/logs/test_metrics.py -v
```

Expected: All 6 tests FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/auto_sdlc/logs/metrics.py`**

```python
def extract_behavioral_metrics(events):
    """Extract behavioral signals from one session's events."""
    user_messages = 0
    skill_invocations = 0
    tool_calls = 0
    tool_names = set()

    for event in events:
        if event.get("type") == "user":
            if event.get("isMeta"):
                skill_invocations += 1
            else:
                user_messages += 1
        elif event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls += 1
                        tool_names.add(block.get("name", "unknown"))

    return {
        "user_messages": user_messages,
        "skill_invocations": skill_invocations,
        "tool_calls": tool_calls,
        "unique_tools": sorted(tool_names),
    }


def aggregate_behavioral_metrics(all_session_events, total_days_active):
    """Roll up behavioral metrics across all sessions."""
    total_user = 0
    total_skills = 0
    total_tools = 0
    all_tools = set()
    msg_counts = []

    for events in all_session_events:
        m = extract_behavioral_metrics(events)
        total_user += m["user_messages"]
        total_skills += m["skill_invocations"]
        total_tools += m["tool_calls"]
        all_tools.update(m["unique_tools"])
        session_total = m["user_messages"] + m["skill_invocations"]
        if session_total > 0:
            msg_counts.append(session_total)

    total_messages = total_user + total_skills
    skill_ratio = (
        round(total_skills / total_messages, 3) if total_messages > 0 else 0.0
    )
    avg_msgs = (
        round(sum(msg_counts) / len(msg_counts), 1) if msg_counts else 0.0
    )
    sessions_per_day = (
        round(len(all_session_events) / total_days_active, 2)
        if total_days_active > 0 else 0.0
    )

    return {
        "total_user_messages": total_user,
        "total_skill_invocations": total_skills,
        "skill_invocation_ratio": skill_ratio,
        "total_tool_calls": total_tools,
        "unique_tools_used": sorted(all_tools),
        "avg_messages_per_session": avg_msgs,
        "sessions_per_day": sessions_per_day,
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_metrics.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/smannar/auto-sdlc
git add src/auto_sdlc/logs/metrics.py tests/logs/test_metrics.py
git commit -m "feat: add behavioral metrics extractor (skill ratio, tool use, session frequency)"
```

---

## Task 2: Maturity Scoring

Score 5 maturity dimensions on a 0–4 scale. Dimensions: Prompting Sophistication, Tooling Adoption, Usage Frequency, Session Depth, Context Efficiency.

**Files:**
- Create: `src/auto_sdlc/logs/maturity.py`
- Create: `tests/logs/test_maturity.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_maturity.py
from auto_sdlc.logs.maturity import score_dimension, build_maturity_report

LEVEL_LABELS = ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"]


def test_score_dimension_boundaries():
    # prompting_sophistication thresholds: [0, 15, 30, 50, 70]
    assert score_dimension("prompting_sophistication", 0) == 0
    assert score_dimension("prompting_sophistication", 14) == 0
    assert score_dimension("prompting_sophistication", 15) == 1
    assert score_dimension("prompting_sophistication", 50) == 3
    assert score_dimension("prompting_sophistication", 70) == 4


def test_score_dimension_tooling():
    # tooling_adoption thresholds: [0, 0.05, 0.15, 0.30, 0.50]
    assert score_dimension("tooling_adoption", 0.0) == 0
    assert score_dimension("tooling_adoption", 0.05) == 1
    assert score_dimension("tooling_adoption", 0.50) == 4


def test_build_maturity_report_structure():
    behavioral = {
        "skill_invocation_ratio": 0.20,
        "sessions_per_day": 1.5,
        "avg_messages_per_session": 10,
    }
    token_agg = {
        "total_tokens": 1000,
        "total_cache_read_tokens": 800,
    }
    result = build_maturity_report(behavioral, avg_prompt_quality=55, token_usage_agg=token_agg)
    assert "overall_level" in result
    assert "overall_label" in result
    assert "dimensions" in result
    assert len(result["dimensions"]) == 5
    for dim in result["dimensions"].values():
        assert "label" in dim
        assert "level" in dim
        assert "level_label" in dim
        assert dim["level"] in range(5)


def test_build_maturity_report_overall_label():
    behavioral = {
        "skill_invocation_ratio": 0.50,
        "sessions_per_day": 3.0,
        "avg_messages_per_session": 25,
    }
    token_agg = {
        "total_tokens": 1000,
        "total_cache_read_tokens": 960,
    }
    result = build_maturity_report(behavioral, avg_prompt_quality=75, token_usage_agg=token_agg)
    assert result["overall_level"] == 4
    assert result["overall_label"] == "Expert"


def test_build_maturity_report_zero_tokens():
    behavioral = {"skill_invocation_ratio": 0, "sessions_per_day": 0, "avg_messages_per_session": 0}
    token_agg = {"total_tokens": 0, "total_cache_read_tokens": 0}
    result = build_maturity_report(behavioral, avg_prompt_quality=0, token_usage_agg=token_agg)
    assert result["overall_level"] == 0
    assert result["overall_label"] == "Beginner"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_maturity.py -v
```

Expected: All 5 tests FAIL.

- [ ] **Step 3: Write `src/auto_sdlc/logs/maturity.py`**

```python
_LEVEL_LABELS = ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"]

_RUBRIC = {
    "prompting_sophistication": {
        "label": "Prompting Sophistication",
        "description": "Quality and specificity of prompts",
        "thresholds": [0, 15, 30, 50, 70],
    },
    "tooling_adoption": {
        "label": "Tooling Adoption",
        "description": "Ratio of skill/command use to raw prompts",
        "thresholds": [0, 0.05, 0.15, 0.30, 0.50],
    },
    "usage_frequency": {
        "label": "Usage Frequency",
        "description": "Sessions per day across active period",
        "thresholds": [0, 0.14, 0.43, 1.0, 2.14],
    },
    "session_depth": {
        "label": "Session Depth",
        "description": "Average messages per session",
        "thresholds": [0, 3, 6, 12, 20],
    },
    "context_efficiency": {
        "label": "Context Efficiency",
        "description": "Cache read fraction of total tokens",
        "thresholds": [0, 0.50, 0.70, 0.85, 0.95],
    },
}


def score_dimension(dimension_key, value):
    """Return level 0–4 for a named dimension given its raw value."""
    thresholds = _RUBRIC[dimension_key]["thresholds"]
    level = 0
    for i, t in enumerate(thresholds):
        if value >= t:
            level = i
    return level


def build_maturity_report(behavioral, avg_prompt_quality, token_usage_agg):
    """Return maturity dimensions and overall level."""
    total = token_usage_agg.get("total_tokens", 0)
    cache_ratio = (
        token_usage_agg.get("total_cache_read_tokens", 0) / total
        if total > 0 else 0.0
    )

    raw = {
        "prompting_sophistication": avg_prompt_quality or 0,
        "tooling_adoption": behavioral.get("skill_invocation_ratio", 0),
        "usage_frequency": behavioral.get("sessions_per_day", 0),
        "session_depth": behavioral.get("avg_messages_per_session", 0),
        "context_efficiency": cache_ratio,
    }

    dimensions = {}
    for key, value in raw.items():
        rubric = _RUBRIC[key]
        level = score_dimension(key, value)
        dimensions[key] = {
            "label": rubric["label"],
            "description": rubric["description"],
            "raw_value": round(value, 4),
            "level": level,
            "level_label": _LEVEL_LABELS[level],
        }

    levels = [d["level"] for d in dimensions.values()]
    overall = round(sum(levels) / len(levels))

    return {
        "overall_level": overall,
        "overall_label": _LEVEL_LABELS[overall],
        "dimensions": dimensions,
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_maturity.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/auto_sdlc/logs/maturity.py tests/logs/test_maturity.py
git commit -m "feat: add 5-dimension maturity scorer"
```

---

## Task 3: Qualitative Analysis via `claude -p`

Call the `claude` CLI in print mode to get narrative analysis. Tests mock subprocess — no real API calls.

**Files:**
- Create: `src/auto_sdlc/logs/qualitative.py`
- Create: `tests/logs/test_qualitative.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_qualitative.py
import json
from unittest.mock import patch, MagicMock
from auto_sdlc.logs.qualitative import run_llm, analyze_workflow_patterns, analyze_anti_patterns, analyze_maturity_narrative, run_full_qualitative_analysis


def _mock_run(output, returncode=0):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = output
    return m


def test_run_llm_returns_stripped_output():
    with patch("subprocess.run", return_value=_mock_run("  hello world  ")):
        result = run_llm("some prompt")
    assert result == "hello world"


def test_run_llm_returns_none_on_nonzero():
    with patch("subprocess.run", return_value=_mock_run("error", returncode=1)):
        result = run_llm("some prompt")
    assert result is None


def test_run_llm_returns_none_on_file_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = run_llm("some prompt")
    assert result is None


def test_analyze_workflow_patterns_parses_json():
    fake = json.dumps({"workflows": [{"pattern": "Debugging", "evidence": "Many error prompts"}]})
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=fake):
        result = analyze_workflow_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert result["workflows"][0]["pattern"] == "Debugging"


def test_analyze_workflow_patterns_handles_bad_json():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value="not json"):
        result = analyze_workflow_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert "workflows" in result
    assert result["workflows"] == []


def test_analyze_anti_patterns_parses_json():
    fake = json.dumps({"anti_patterns": [{"name": "Vague prompts", "recommendation": "Add file refs"}]})
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=fake):
        result = analyze_anti_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert result["anti_patterns"][0]["name"] == "Vague prompts"


def test_analyze_maturity_narrative_returns_string():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value="Strong usage overall."):
        result = analyze_maturity_narrative({"sessions": [], "summary": {}, "user_id": "test"})
    assert result == "Strong usage overall."


def test_run_full_qualitative_analysis_structure():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=json.dumps({"workflows": [], "anti_patterns": []})):
        result = run_full_qualitative_analysis({"sessions": [], "summary": {}, "user_id": "test"})
    assert "workflow_patterns" in result
    assert "anti_patterns" in result
    assert "narrative" in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_qualitative.py -v
```

Expected: All 8 tests FAIL.

- [ ] **Step 3: Write `src/auto_sdlc/logs/qualitative.py`**

```python
import json
import subprocess


def run_llm(prompt_text, timeout=60):
    """Invoke `claude -p <prompt>` and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt_text],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _context_summary(report):
    """Build a compact text summary of the report for LLM input."""
    summary = report.get("summary", {})
    maturity = report.get("maturity_scores", {})
    behavioral = report.get("behavioral_metrics", {})

    sample_prompts = []
    for session in report.get("sessions", [])[:20]:
        for ps in session.get("prompt_scores", [])[:2]:
            sample_prompts.append(ps.get("prompt_preview", ""))

    lines = [
        "Developer AI usage data:",
        f"  user_id: {report.get('user_id', 'unknown')}",
        f"  total_sessions: {summary.get('total_sessions')}",
        f"  avg_prompt_quality: {summary.get('avg_prompt_quality_score')}",
        f"  maturity_level: {maturity.get('overall_label', 'Unknown')} ({maturity.get('overall_level', '?')}/4)",
        f"  skill_invocation_ratio: {behavioral.get('skill_invocation_ratio')}",
        f"  avg_messages_per_session: {behavioral.get('avg_messages_per_session')}",
        f"  sessions_per_day: {behavioral.get('sessions_per_day')}",
        "",
        "Sample prompts (up to 15):",
    ] + [f"  - {p}" for p in sample_prompts[:15]]

    return "\n".join(lines)


def analyze_workflow_patterns(report):
    """Identify dominant workflows. Returns dict with 'workflows' list."""
    context = _context_summary(report)
    prompt = (
        "You are analyzing a developer's Claude Code usage data. "
        "Based on the following metrics and sample prompts, identify 2-3 dominant workflow patterns "
        "(e.g. 'primarily debugging', 'heavy refactoring', 'new feature development').\n\n"
        f"{context}\n\n"
        "Respond with ONLY a JSON object: "
        '{"workflows": [{"pattern": "short name", "evidence": "one sentence"}]}. '
        "No prose outside the JSON."
    )
    response = run_llm(prompt)
    if not response:
        return {"workflows": []}
    try:
        parsed = json.loads(response)
        return {"workflows": parsed.get("workflows", [])}
    except (json.JSONDecodeError, ValueError):
        return {"workflows": [], "raw": response}


def analyze_anti_patterns(report):
    """Identify anti-patterns. Returns dict with 'anti_patterns' list."""
    context = _context_summary(report)
    prompt = (
        "You are analyzing a developer's Claude Code usage data. "
        "Identify 1-3 anti-patterns or inefficiencies in how this developer uses AI.\n\n"
        f"{context}\n\n"
        "Respond with ONLY a JSON object: "
        '{"anti_patterns": [{"name": "short label", "recommendation": "one actionable sentence"}]}. '
        "No prose outside the JSON."
    )
    response = run_llm(prompt)
    if not response:
        return {"anti_patterns": []}
    try:
        parsed = json.loads(response)
        return {"anti_patterns": parsed.get("anti_patterns", [])}
    except (json.JSONDecodeError, ValueError):
        return {"anti_patterns": [], "raw": response}


def analyze_maturity_narrative(report):
    """Return a 2-3 sentence executive summary of maturity."""
    context = _context_summary(report)
    prompt = (
        "You are an AI-assisted development consultant. "
        "Write a 2-3 sentence executive summary of this developer's AI usage maturity, "
        "suitable for a team lead. Be specific and constructive.\n\n"
        f"{context}\n\n"
        "Respond with plain text only. 2-3 sentences."
    )
    return run_llm(prompt) or "Qualitative analysis unavailable."


def run_full_qualitative_analysis(report):
    """Run all three analyses and return combined dict."""
    return {
        "workflow_patterns": analyze_workflow_patterns(report),
        "anti_patterns": analyze_anti_patterns(report),
        "narrative": analyze_maturity_narrative(report),
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_qualitative.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/auto_sdlc/logs/qualitative.py tests/logs/test_qualitative.py
git commit -m "feat: add LLM qualitative analysis via claude -p subprocess"
```

---

## Task 4: Wire New Modules into Report + Default File Output

Extend `report.py` to include behavioral metrics, maturity scores, project breakdown, user_id, and save to `~/.auto-sdlc/reports/{user_id}/{date}.json` by default.

**Files:**
- Modify: `src/auto_sdlc/logs/report.py`
- Modify: `tests/logs/test_report.py`

**Understanding the date range for `sessions_per_day`:** Compute `total_days_active` as `(max_date - min_date).days + 1` from all session start timestamps, minimum 1.

- [ ] **Step 1: Update `tests/logs/test_report.py`**

Replace the entire file:

```python
# tests/logs/test_report.py
import json
import pytest
from pathlib import Path
from auto_sdlc.logs.report import build_report, run_logs_report


def test_build_report_includes_user_id(sample_projects_dir):
    report = build_report(sample_projects_dir, user_id="alice@example.com")
    assert report["user_id"] == "alice@example.com"


def test_build_report_defaults_user_id(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert report["user_id"] is not None


def test_build_report_includes_behavioral_metrics(sample_projects_dir):
    report = build_report(sample_projects_dir)
    bm = report["behavioral_metrics"]
    assert "skill_invocation_ratio" in bm
    assert "sessions_per_day" in bm
    assert "avg_messages_per_session" in bm


def test_build_report_includes_maturity_scores(sample_projects_dir):
    report = build_report(sample_projects_dir)
    ms = report["maturity_scores"]
    assert "overall_level" in ms
    assert "overall_label" in ms
    assert len(ms["dimensions"]) == 5


def test_build_report_includes_project_breakdown(sample_projects_dir):
    report = build_report(sample_projects_dir)
    pb = report["project_breakdown"]
    assert isinstance(pb, list)
    assert len(pb) >= 1
    assert "project" in pb[0]
    assert "sessions" in pb[0]
    assert "total_tokens" in pb[0]


def test_build_report_no_qualitative_by_default(sample_projects_dir):
    report = build_report(sample_projects_dir)
    assert "qualitative_analysis" not in report


def test_run_logs_report_saves_to_default_path(sample_projects_dir, tmp_path):
    default_dir = tmp_path / "reports"
    report = run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=None,
        user_id="test_user",
        _default_reports_dir=str(default_dir),
    )
    files = list((default_dir / "test_user").glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["user_id"] == "test_user"


def test_run_logs_report_output_path_overrides_default(sample_projects_dir, tmp_path):
    custom_path = tmp_path / "custom.json"
    run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=str(custom_path),
        user_id="test_user",
    )
    assert custom_path.exists()
    data = json.loads(custom_path.read_text())
    assert "summary" in data


def test_run_logs_report_returns_report_dict(sample_projects_dir, tmp_path):
    result = run_logs_report(
        projects_dir=str(sample_projects_dir),
        output_path=str(tmp_path / "r.json"),
        user_id="u1",
    )
    assert result["summary"]["total_sessions"] == 1
```

- [ ] **Step 2: Run updated tests to see which fail**

```bash
pytest tests/logs/test_report.py -v
```

Expected: Most tests FAIL — build_report doesn't have user_id yet.

- [ ] **Step 3: Rewrite `src/auto_sdlc/logs/report.py`**

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from auto_sdlc.logs.parser import parse_session_file, find_session_files
from auto_sdlc.logs.analyzer import (
    extract_token_usage,
    extract_session_metadata,
    aggregate_sessions,
)
from auto_sdlc.logs.scorer import score_session_prompts
from auto_sdlc.logs.metrics import aggregate_behavioral_metrics
from auto_sdlc.logs.maturity import build_maturity_report


def _infer_user_id():
    """Fall back to $USER env var."""
    return os.environ.get("USER", "unknown")


def _compute_days_active(sessions):
    """Return number of unique calendar days across all session start timestamps."""
    dates = set()
    for s in sessions:
        ts = s.get("metadata", {}).get("start_timestamp")
        if ts:
            dates.add(ts[:10])
    return max(len(dates), 1)


def _build_project_breakdown(sessions):
    """Group session stats by project (last 2 cwd segments)."""
    projects = {}
    for session in sessions:
        cwd = session.get("metadata", {}).get("cwd") or "unknown"
        parts = cwd.rstrip("/").split("/")
        project_name = "/".join(parts[-2:]) if len(parts) >= 2 else cwd

        if project_name not in projects:
            projects[project_name] = {
                "project": project_name,
                "cwd": cwd,
                "sessions": 0,
                "total_tokens": 0,
                "_scores": [],
            }
        p = projects[project_name]
        p["sessions"] += 1
        p["total_tokens"] += session.get("token_usage", {}).get("total_tokens", 0)
        for ps in session.get("prompt_scores", []):
            p["_scores"].append(ps["score"])

    result = []
    for p in projects.values():
        scores = p.pop("_scores")
        p["avg_prompt_quality"] = (
            round(sum(scores) / len(scores), 1) if scores else None
        )
        result.append(p)

    return sorted(result, key=lambda x: x["total_tokens"], reverse=True)


def build_report(projects_dir, user_id=None, project_filter=None, since=None):
    """Parse all sessions and return a rich report dict (no qualitative analysis)."""
    projects_dir = Path(projects_dir)
    session_files = find_session_files(projects_dir)

    all_events = []
    sessions = []
    all_prompt_scores = []

    for f in session_files:
        events = parse_session_file(f)
        metadata = extract_session_metadata(events)

        if project_filter and metadata.get("cwd"):
            if project_filter.lower() not in metadata["cwd"].lower():
                continue
        if since and metadata.get("start_timestamp"):
            if metadata["start_timestamp"][:10] < since:
                continue

        all_events.append(events)
        token_usage = extract_token_usage(events)
        prompt_scores = score_session_prompts(events)
        all_prompt_scores.extend(s["score"] for s in prompt_scores)
        sessions.append({
            "session_id": metadata["session_id"],
            "metadata": metadata,
            "token_usage": token_usage,
            "prompt_scores": prompt_scores,
        })

    aggregate = aggregate_sessions(all_events)
    avg_quality = (
        round(sum(all_prompt_scores) / len(all_prompt_scores), 1)
        if all_prompt_scores else None
    )

    days_active = _compute_days_active(sessions)
    behavioral = aggregate_behavioral_metrics(all_events, total_days_active=days_active)
    maturity = build_maturity_report(behavioral, avg_quality, aggregate)

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "user_id": user_id or _infer_user_id(),
        "projects_dir": str(projects_dir),
        "filters": {"project": project_filter, "since": since},
        "summary": {
            **aggregate,
            "avg_prompt_quality_score": avg_quality,
        },
        "behavioral_metrics": behavioral,
        "maturity_scores": maturity,
        "project_breakdown": _build_project_breakdown(sessions),
        "sessions": sessions,
    }


def run_logs_report(
    projects_dir,
    output_path,
    user_id=None,
    project_filter=None,
    since=None,
    summary_only=False,
    run_qualitative=False,
    _default_reports_dir=None,
):
    """Build the report, optionally run qualitative analysis, save to file."""
    default_dir = Path(_default_reports_dir) if _default_reports_dir else (
        Path.home() / ".auto-sdlc" / "reports"
    )
    resolved_dir = Path(projects_dir) if projects_dir else (Path.home() / ".claude" / "projects")
    effective_user = user_id or _infer_user_id()

    report = build_report(
        resolved_dir,
        user_id=effective_user,
        project_filter=project_filter,
        since=since,
    )

    if run_qualitative:
        from auto_sdlc.logs.qualitative import run_full_qualitative_analysis
        report["qualitative_analysis"] = run_full_qualitative_analysis(report)

    if summary_only:
        out = {
            "generated_at": report["generated_at"],
            "user_id": report["user_id"],
            "filters": report["filters"],
            "summary": report["summary"],
            "behavioral_metrics": report["behavioral_metrics"],
            "maturity_scores": {
                "overall_level": report["maturity_scores"]["overall_level"],
                "overall_label": report["maturity_scores"]["overall_label"],
            },
        }
        print(json.dumps(out, indent=2, default=str))
        return report

    if output_path:
        dest = Path(output_path)
    else:
        user_dir = default_dir / effective_user.replace("@", "_at_").replace("/", "_")
        user_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        dest = user_dir / f"{ts}.json"

    dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report saved to {dest}")
    return report
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_report.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
pytest -v
```

Expected: All tests PASS (may need to check `test_cli.py` — `run_logs_report` signature changed).

- [ ] **Step 6: Fix `tests/test_cli.py` if needed**

The CLI tests that call `run_logs_report` indirectly via Click should still pass. If `test_logs_command_with_custom_dir` fails because output now writes to a file instead of stdout, update the test:

```python
def test_logs_command_with_custom_dir(sample_projects_dir, tmp_path):
    output_file = tmp_path / "out.json"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "logs",
        "--projects-dir", str(sample_projects_dir),
        "--output", str(output_file),
    ])
    assert result.exit_code == 0
    data = json.loads(output_file.read_text())
    assert data["summary"]["total_sessions"] == 1
```

- [ ] **Step 7: Run full suite again**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/auto_sdlc/logs/report.py tests/logs/test_report.py tests/test_cli.py
git commit -m "feat: extend report with behavioral metrics, maturity scores, project breakdown; default file output"
```

---

## Task 5: CLI Wiring (`--user-id`, `--qualitative`, `--html`)

Add new flags to `logs` subcommand and wire them to the updated `run_logs_report`.

**Files:**
- Modify: `src/auto_sdlc/cli.py`

- [ ] **Step 1: Read current `cli.py`**

File path: `src/auto_sdlc/cli.py` (already read at plan time — 43 lines, has `--projects-dir`, `--output`, `--project`, `--since`, `--summary-only`)

- [ ] **Step 2: Rewrite `src/auto_sdlc/cli.py`**

```python
import click
from auto_sdlc.logs.report import run_logs_report
from auto_sdlc.init_wizard.wizard import run_wizard
from auto_sdlc.audit.scanner import run_audit


@click.group()
def cli():
    """Auto-SDLC Baseline Tooling."""


@cli.command()
@click.option("--projects-dir", default=None,
              help="Path to Claude Code projects dir. Defaults to ~/.claude/projects/")
@click.option("--output", default=None,
              help="Write JSON report to this file. Defaults to ~/.auto-sdlc/reports/<user>/<timestamp>.json")
@click.option("--project", default=None,
              help="Filter sessions by project name (matches against working directory).")
@click.option("--since", default=None, metavar="YYYY-MM-DD",
              help="Only include sessions on or after this date.")
@click.option("--summary-only", is_flag=True, default=False,
              help="Print summary + maturity scores to stdout instead of saving full report.")
@click.option("--user-id", default=None,
              help="Developer identifier (email or name) for report attribution.")
@click.option("--qualitative", is_flag=True, default=False,
              help="Run LLM qualitative analysis via 'claude -p' (slow, requires claude CLI).")
@click.option("--html", is_flag=True, default=False,
              help="Also render an HTML report alongside the JSON.")
def logs(projects_dir, output, project, since, summary_only, user_id, qualitative, html):
    """Analyze Claude Code session logs."""
    report = run_logs_report(
        projects_dir=projects_dir,
        output_path=output,
        user_id=user_id,
        project_filter=project,
        since=since,
        summary_only=summary_only,
        run_qualitative=qualitative,
    )
    if html and not summary_only:
        from auto_sdlc.logs.render_html import render_individual_html
        from pathlib import Path
        import json
        html_content = render_individual_html(report)
        if output:
            html_path = Path(output).with_suffix(".html")
        else:
            from datetime import datetime, timezone
            from auto_sdlc.logs.report import _infer_user_id
            effective_user = (user_id or _infer_user_id()).replace("@", "_at_").replace("/", "_")
            user_dir = Path.home() / ".auto-sdlc" / "reports" / effective_user
            user_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
            html_path = user_dir / f"{ts}.html"
        html_path.write_text(html_content, encoding="utf-8")
        click.echo(f"HTML report saved to {html_path}")


@cli.command()
@click.option("--reports-dir", required=True,
              help="Directory containing individual user JSON report files.")
@click.option("--output", default=None,
              help="Write team JSON report to this file.")
@click.option("--html", is_flag=True, default=False,
              help="Also render team HTML report.")
def team(reports_dir, output, html):
    """Aggregate individual user reports into a team maturity report."""
    from auto_sdlc.logs.team import build_team_report_from_dir, render_team_html
    from datetime import datetime, timezone
    from pathlib import Path
    import json

    team_report = build_team_report_from_dir(reports_dir)
    team_report["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

    dest = Path(output) if output else Path(reports_dir) / "team_report.json"
    dest.write_text(json.dumps(team_report, indent=2, default=str), encoding="utf-8")
    click.echo(f"Team report saved to {dest}")

    if html:
        html_content = render_team_html(team_report)
        html_path = dest.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        click.echo(f"Team HTML report saved to {html_path}")


@cli.command(name="init")
def init_cmd():
    """Interactive wizard to generate SDLC config files."""
    run_wizard()


@cli.command()
def audit():
    """Audit installed capabilities against baseline."""
    run_audit()
```

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 4: Smoke test the new flags**

```bash
auto-sdlc logs --help
```

Expected output includes `--user-id`, `--qualitative`, `--html`.

- [ ] **Step 5: Commit**

```bash
git add src/auto_sdlc/cli.py
git commit -m "feat: add --user-id, --qualitative, --html flags to logs; add team subcommand"
```

---

## Task 6: Individual HTML Report Renderer

Generate a self-contained, offline-viewable HTML file with metric cards, maturity bars, project table, and optional qualitative findings.

**Files:**
- Create: `src/auto_sdlc/logs/render_html.py`
- Create: `tests/logs/test_render_html.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_render_html.py
from auto_sdlc.logs.render_html import render_individual_html


def _sample_report():
    return {
        "user_id": "alice@example.com",
        "generated_at": "2026-03-31T10:00:00+00:00",
        "summary": {
            "total_sessions": 10,
            "total_tokens": 500000,
            "avg_prompt_quality_score": 55,
        },
        "behavioral_metrics": {
            "skill_invocation_ratio": 0.20,
            "sessions_per_day": 1.4,
            "avg_messages_per_session": 8.5,
        },
        "maturity_scores": {
            "overall_level": 2,
            "overall_label": "Intermediate",
            "dimensions": {
                "prompting_sophistication": {
                    "label": "Prompting Sophistication",
                    "description": "Quality of prompts",
                    "raw_value": 55,
                    "level": 3,
                    "level_label": "Advanced",
                },
                "tooling_adoption": {
                    "label": "Tooling Adoption",
                    "description": "Skill usage ratio",
                    "raw_value": 0.20,
                    "level": 2,
                    "level_label": "Intermediate",
                },
            },
        },
        "project_breakdown": [
            {"project": "myapp/src", "cwd": "/Users/alice/myapp/src", "sessions": 7, "total_tokens": 350000, "avg_prompt_quality": 58},
            {"project": "utils/lib", "cwd": "/Users/alice/utils/lib", "sessions": 3, "total_tokens": 150000, "avg_prompt_quality": 47},
        ],
        "sessions": [],
    }


def test_render_returns_string():
    html = render_individual_html(_sample_report())
    assert isinstance(html, str)


def test_render_contains_user_id():
    html = render_individual_html(_sample_report())
    assert "alice@example.com" in html


def test_render_contains_maturity_label():
    html = render_individual_html(_sample_report())
    assert "Intermediate" in html


def test_render_contains_project_names():
    html = render_individual_html(_sample_report())
    assert "myapp/src" in html
    assert "utils/lib" in html


def test_render_contains_dimension_labels():
    html = render_individual_html(_sample_report())
    assert "Prompting Sophistication" in html
    assert "Tooling Adoption" in html


def test_render_is_valid_html_skeleton():
    html = render_individual_html(_sample_report())
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_render_qualitative_section_when_present():
    report = _sample_report()
    report["qualitative_analysis"] = {
        "narrative": "Strong AI usage overall.",
        "workflow_patterns": {"workflows": [{"pattern": "Debugging", "evidence": "Many error prompts"}]},
        "anti_patterns": {"anti_patterns": [{"name": "Vague prompts", "recommendation": "Add file refs"}]},
    }
    html = render_individual_html(report)
    assert "Strong AI usage overall." in html
    assert "Debugging" in html
    assert "Vague prompts" in html


def test_render_no_qualitative_section_when_absent():
    html = render_individual_html(_sample_report())
    assert "Qualitative Findings" not in html
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_render_html.py -v
```

Expected: All 8 tests FAIL.

- [ ] **Step 3: Write `src/auto_sdlc/logs/render_html.py`**

```python
def render_individual_html(report):
    """Render a self-contained HTML report for one developer."""
    user_id = report.get("user_id", "unknown")
    generated_at = (report.get("generated_at") or "")[:10]
    summary = report.get("summary", {})
    behavioral = report.get("behavioral_metrics", {})
    maturity = report.get("maturity_scores", {})
    projects = report.get("project_breakdown", [])
    qualitative = report.get("qualitative_analysis")

    def fmt_tokens(n):
        if n is None:
            return "—"
        if n >= 1_000_000:
            return "{:.1f}M".format(n / 1_000_000)
        if n >= 1_000:
            return "{:.0f}K".format(n / 1_000)
        return str(n)

    _level_colors = {0: "#e74c3c", 1: "#e67e22", 2: "#f1c40f", 3: "#2ecc71", 4: "#27ae60"}
    overall_level = maturity.get("overall_level", 0)
    maturity_color = _level_colors.get(overall_level, "#999")

    dimensions_rows = ""
    for dim in maturity.get("dimensions", {}).values():
        pct = int(dim["level"] / 4 * 100)
        dimensions_rows += (
            "<tr>"
            "<td style='padding:6px 10px;width:220px'>{label}</td>"
            "<td style='padding:6px 10px'>"
            "<div style='background:#eee;border-radius:4px;height:16px;width:200px'>"
            "<div style='background:#4a90d9;border-radius:4px;height:16px;width:{pct}%'></div>"
            "</div></td>"
            "<td style='padding:6px 10px;color:#555'>{lvl_label} ({level}/4)</td>"
            "<td style='padding:6px 10px;color:#888;font-size:12px'>{desc}</td>"
            "</tr>"
        ).format(
            label=dim["label"],
            pct=pct,
            lvl_label=dim["level_label"],
            level=dim["level"],
            desc=dim["description"],
        )

    project_rows = ""
    for p in projects[:10]:
        q = p.get("avg_prompt_quality")
        q_str = "{:.0f}".format(q) if q is not None else "—"
        project_rows += (
            "<tr>"
            "<td style='padding:5px 10px'>{project}</td>"
            "<td style='padding:5px 10px;text-align:right'>{sessions}</td>"
            "<td style='padding:5px 10px;text-align:right'>{tokens}</td>"
            "<td style='padding:5px 10px;text-align:right'>{quality}</td>"
            "</tr>"
        ).format(
            project=p["project"],
            sessions=p["sessions"],
            tokens=fmt_tokens(p["total_tokens"]),
            quality=q_str,
        )

    qualitative_html = ""
    if qualitative:
        narrative = qualitative.get("narrative", "")
        workflows = qualitative.get("workflow_patterns", {}).get("workflows", [])
        anti_patterns = qualitative.get("anti_patterns", {}).get("anti_patterns", [])

        wf_items = "".join(
            "<li><b>{}</b> — {}</li>".format(w["pattern"], w["evidence"])
            for w in workflows
        )
        ap_items = "".join(
            "<li><b>{}</b>: {}</li>".format(a["name"], a["recommendation"])
            for a in anti_patterns
        )

        qualitative_html = (
            "<div style='background:white;border-radius:8px;padding:20px 24px;"
            "box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:20px'>"
            "<h2 style='margin:0 0 16px 0;font-size:16px;color:#333;"
            "border-bottom:2px solid #4a90d9;padding-bottom:8px'>Qualitative Findings</h2>"
            + ("<p style='color:#444;line-height:1.6'>{}</p>".format(narrative) if narrative else "")
            + ("<h3 style='color:#555;font-size:14px'>Workflow Patterns</h3><ul>{}</ul>".format(wf_items) if workflows else "")
            + ("<h3 style='color:#555;font-size:14px'>Anti-patterns &amp; Recommendations</h3><ul>{}</ul>".format(ap_items) if anti_patterns else "")
            + "</div>"
        )

    skill_pct = int((behavioral.get("skill_invocation_ratio") or 0) * 100)

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Auto-SDLC Report \u2014 {user_id}</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;margin:0;padding:24px;color:#222}}
    .metric-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px}}
    .metric{{background:white;border-radius:8px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,.1);flex:1;min-width:130px}}
    .metric .value{{font-size:26px;font-weight:700;color:#4a90d9}}
    .metric .label{{font-size:12px;color:#888;margin-top:4px}}
    .card{{background:white;border-radius:8px;padding:20px 24px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:20px}}
    h1{{margin:0 0 4px 0;font-size:22px}}
    h2{{margin:0 0 16px 0;font-size:16px;color:#333;border-bottom:2px solid #4a90d9;padding-bottom:8px}}
    table{{border-collapse:collapse;width:100%}}
    th{{text-align:left;padding:6px 10px;border-bottom:2px solid #eee;color:#555;font-size:13px}}
    tr:nth-child(even){{background:#f9f9f9}}
    .subtitle{{color:#888;font-size:13px;margin-bottom:20px}}
  </style>
</head>
<body>
  <h1>Auto-SDLC Individual Report</h1>
  <p class="subtitle">{user_id} &nbsp;&middot;&nbsp; Generated {date} &nbsp;&middot;&nbsp; {sessions} sessions</p>

  <div class="metric-row">
    <div class="metric"><div class="value">{total_tokens}</div><div class="label">Total Tokens</div></div>
    <div class="metric"><div class="value">{avg_quality}</div><div class="label">Avg Prompt Quality</div></div>
    <div class="metric"><div class="value">{skill_pct}%</div><div class="label">Skill Adoption</div></div>
    <div class="metric"><div class="value" style="color:{maturity_color}">{maturity_label}</div><div class="label">Maturity Level</div></div>
    <div class="metric"><div class="value">{spd}</div><div class="label">Sessions / Day</div></div>
  </div>

  <div class="card">
    <h2>Maturity Dimensions</h2>
    <table>
      <tr><th>Dimension</th><th>Score</th><th>Level</th><th>What it measures</th></tr>
      {dimensions_rows}
    </table>
  </div>

  <div class="card">
    <h2>Project Breakdown</h2>
    <table>
      <tr><th>Project</th><th>Sessions</th><th>Tokens</th><th>Avg Quality</th></tr>
      {project_rows}
    </table>
  </div>

  {qualitative_html}
</body>
</html>""".format(
        user_id=user_id,
        date=generated_at,
        sessions=summary.get("total_sessions", 0),
        total_tokens=fmt_tokens(summary.get("total_tokens")),
        avg_quality=summary.get("avg_prompt_quality_score") or "—",
        skill_pct=skill_pct,
        maturity_color=maturity_color,
        maturity_label=maturity.get("overall_label", "—"),
        spd=behavioral.get("sessions_per_day") or "—",
        dimensions_rows=dimensions_rows,
        project_rows=project_rows,
        qualitative_html=qualitative_html,
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_render_html.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/auto_sdlc/logs/render_html.py tests/logs/test_render_html.py
git commit -m "feat: add self-contained individual HTML report renderer"
```

---

## Task 7: Team Rollup

Aggregate multiple individual user JSON report files into a team-level maturity report with per-dimension breakdowns and optional HTML.

**Files:**
- Create: `src/auto_sdlc/logs/team.py`
- Create: `tests/logs/test_team.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_team.py
import json
import pytest
from pathlib import Path
from auto_sdlc.logs.team import build_team_report, build_team_report_from_dir, render_team_html


def _user_report(user_id, overall_level, sessions=5, tokens=100000):
    return {
        "user_id": user_id,
        "summary": {
            "total_sessions": sessions,
            "total_tokens": tokens,
            "avg_prompt_quality_score": 50,
        },
        "behavioral_metrics": {
            "skill_invocation_ratio": 0.20,
            "sessions_per_day": 1.0,
            "avg_messages_per_session": 8.0,
        },
        "maturity_scores": {
            "overall_level": overall_level,
            "overall_label": ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"][overall_level],
            "dimensions": {
                "prompting_sophistication": {
                    "label": "Prompting Sophistication",
                    "description": "Quality of prompts",
                    "raw_value": 50,
                    "level": 3,
                    "level_label": "Advanced",
                },
                "tooling_adoption": {
                    "label": "Tooling Adoption",
                    "description": "Skill usage ratio",
                    "raw_value": 0.20,
                    "level": 2,
                    "level_label": "Intermediate",
                },
            },
        },
        "project_breakdown": [
            {"project": "myapp/src", "sessions": sessions, "total_tokens": tokens, "avg_prompt_quality": 50}
        ],
        "sessions": [],
    }


def test_build_team_report_structure():
    reports = [("alice", _user_report("alice", 2)), ("bob", _user_report("bob", 3))]
    result = build_team_report(reports)
    assert result["team_size"] == 2
    assert "overall_maturity_level" in result
    assert "overall_maturity_label" in result
    assert "members" in result
    assert "maturity_by_dimension" in result


def test_build_team_report_overall_is_avg():
    reports = [("a", _user_report("a", 2)), ("b", _user_report("b", 4))]
    result = build_team_report(reports)
    assert result["overall_maturity_level"] == 3  # round((2+4)/2)


def test_build_team_report_member_summary():
    reports = [("alice", _user_report("alice", 2))]
    result = build_team_report(reports)
    alice = result["members"][0]
    assert alice["user_id"] == "alice"
    assert alice["overall_maturity_level"] == 2
    assert alice["sessions"] == 5


def test_build_team_report_token_totals():
    reports = [
        ("a", _user_report("a", 2, tokens=100000)),
        ("b", _user_report("b", 2, tokens=200000)),
    ]
    result = build_team_report(reports)
    assert result["total_tokens"] == 300000


def test_build_team_report_from_dir(tmp_path):
    r1 = _user_report("alice", 2)
    r2 = _user_report("bob", 3)
    (tmp_path / "alice_2026.json").write_text(json.dumps(r1), encoding="utf-8")
    (tmp_path / "bob_2026.json").write_text(json.dumps(r2), encoding="utf-8")
    result = build_team_report_from_dir(str(tmp_path))
    assert result["team_size"] == 2


def test_render_team_html_returns_string():
    reports = [("alice", _user_report("alice", 2))]
    team_report = build_team_report(reports)
    html = render_team_html(team_report)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "alice" in html
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_team.py -v
```

Expected: All 6 tests FAIL.

- [ ] **Step 3: Write `src/auto_sdlc/logs/team.py`**

```python
import json
from pathlib import Path

_LEVEL_LABELS = ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"]
_LEVEL_COLORS = {0: "#e74c3c", 1: "#e67e22", 2: "#f1c40f", 3: "#2ecc71", 4: "#27ae60"}


def build_team_report(user_reports):
    """Aggregate individual user reports into a team report.

    user_reports: list of (user_id, report_dict) tuples.
    """
    team_dim_levels = {}
    total_sessions = 0
    total_tokens = 0
    quality_scores = []
    skill_ratios = []
    spd_values = []
    all_projects = set()
    members = []

    for user_id, report in user_reports:
        summary = report.get("summary", {})
        behavioral = report.get("behavioral_metrics", {})
        maturity = report.get("maturity_scores", {})

        total_sessions += summary.get("total_sessions", 0)
        total_tokens += summary.get("total_tokens", 0)

        if summary.get("avg_prompt_quality_score") is not None:
            quality_scores.append(summary["avg_prompt_quality_score"])
        if behavioral.get("skill_invocation_ratio") is not None:
            skill_ratios.append(behavioral["skill_invocation_ratio"])
        if behavioral.get("sessions_per_day") is not None:
            spd_values.append(behavioral["sessions_per_day"])

        for proj in report.get("project_breakdown", []):
            all_projects.add(proj.get("project", "unknown"))

        for dim_key, dim_data in maturity.get("dimensions", {}).items():
            if dim_key not in team_dim_levels:
                team_dim_levels[dim_key] = {"label": dim_data["label"], "levels": []}
            team_dim_levels[dim_key]["levels"].append(dim_data["level"])

        members.append({
            "user_id": user_id,
            "sessions": summary.get("total_sessions", 0),
            "avg_prompt_quality": summary.get("avg_prompt_quality_score"),
            "overall_maturity_level": maturity.get("overall_level"),
            "overall_maturity_label": maturity.get("overall_label"),
            "skill_invocation_ratio": behavioral.get("skill_invocation_ratio"),
        })

    def _avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else None

    maturity_by_dimension = {}
    for key, data in team_dim_levels.items():
        levels = data["levels"]
        avg_level = round(sum(levels) / len(levels)) if levels else 0
        maturity_by_dimension[key] = {
            "label": data["label"],
            "avg_level": avg_level,
            "avg_label": _LEVEL_LABELS[avg_level],
            "member_levels": levels,
        }

    all_overall = [m["overall_maturity_level"] for m in members if m["overall_maturity_level"] is not None]
    team_overall = round(sum(all_overall) / len(all_overall)) if all_overall else 0

    return {
        "team_size": len(user_reports),
        "overall_maturity_level": team_overall,
        "overall_maturity_label": _LEVEL_LABELS[team_overall],
        "total_sessions": total_sessions,
        "total_tokens": total_tokens,
        "avg_prompt_quality": _avg(quality_scores),
        "avg_skill_invocation_ratio": _avg(skill_ratios),
        "avg_sessions_per_day": _avg(spd_values),
        "unique_projects": sorted(all_projects),
        "maturity_by_dimension": maturity_by_dimension,
        "members": members,
    }


def build_team_report_from_dir(reports_dir):
    """Load all *.json files (excluding team_report.json) from a dir and aggregate."""
    reports_path = Path(reports_dir)
    user_reports = []
    for f in sorted(reports_path.glob("*.json")):
        if f.name == "team_report.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            user_id = data.get("user_id", f.stem)
            user_reports.append((user_id, data))
        except (json.JSONDecodeError, OSError):
            continue
    return build_team_report(user_reports)


def render_team_html(team_report):
    """Render a self-contained team HTML report."""
    team_size = team_report.get("team_size", 0)
    overall_level = team_report.get("overall_maturity_level", 0)
    overall_label = team_report.get("overall_maturity_label", "—")
    maturity_color = _LEVEL_COLORS.get(overall_level, "#999")

    def fmt_tokens(n):
        if n is None:
            return "—"
        if n >= 1_000_000:
            return "{:.1f}M".format(n / 1_000_000)
        if n >= 1_000:
            return "{:.0f}K".format(n / 1_000)
        return str(n)

    dim_rows = ""
    for dim in team_report.get("maturity_by_dimension", {}).values():
        pct = int(dim["avg_level"] / 4 * 100)
        dim_rows += (
            "<tr>"
            "<td style='padding:6px 10px;width:220px'>{label}</td>"
            "<td style='padding:6px 10px'>"
            "<div style='background:#eee;border-radius:4px;height:16px;width:200px'>"
            "<div style='background:#4a90d9;border-radius:4px;height:16px;width:{pct}%'></div>"
            "</div></td>"
            "<td style='padding:6px 10px;color:#555'>{avg_label} ({avg_level}/4)</td>"
            "</tr>"
        ).format(label=dim["label"], pct=pct, avg_label=dim["avg_label"], avg_level=dim["avg_level"])

    member_rows = ""
    for m in team_report.get("members", []):
        ml = m.get("overall_maturity_level", 0)
        color = _LEVEL_COLORS.get(ml, "#999")
        skill_pct = int((m.get("skill_invocation_ratio") or 0) * 100)
        member_rows += (
            "<tr>"
            "<td style='padding:5px 10px'>{user_id}</td>"
            "<td style='padding:5px 10px;text-align:right'>{sessions}</td>"
            "<td style='padding:5px 10px;text-align:right'>{quality}</td>"
            "<td style='padding:5px 10px;text-align:right'>{skill_pct}%</td>"
            "<td style='padding:5px 10px;text-align:center;color:{color};font-weight:600'>{label}</td>"
            "</tr>"
        ).format(
            user_id=m["user_id"],
            sessions=m.get("sessions", 0),
            quality=m.get("avg_prompt_quality") or "—",
            skill_pct=skill_pct,
            color=color,
            label=m.get("overall_maturity_label", "—"),
        )

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Auto-SDLC Team Report</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;margin:0;padding:24px;color:#222}}
    .metric-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px}}
    .metric{{background:white;border-radius:8px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,.1);flex:1;min-width:130px}}
    .metric .value{{font-size:26px;font-weight:700;color:#4a90d9}}
    .metric .label{{font-size:12px;color:#888;margin-top:4px}}
    .card{{background:white;border-radius:8px;padding:20px 24px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:20px}}
    h1{{margin:0 0 4px 0;font-size:22px}}
    h2{{margin:0 0 16px 0;font-size:16px;color:#333;border-bottom:2px solid #4a90d9;padding-bottom:8px}}
    table{{border-collapse:collapse;width:100%}}
    th{{text-align:left;padding:6px 10px;border-bottom:2px solid #eee;color:#555;font-size:13px}}
    tr:nth-child(even){{background:#f9f9f9}}
  </style>
</head>
<body>
  <h1>Auto-SDLC Team Report</h1>
  <p style="color:#888;font-size:13px;margin-bottom:20px">{team_size} team members</p>

  <div class="metric-row">
    <div class="metric"><div class="value">{total_sessions}</div><div class="label">Total Sessions</div></div>
    <div class="metric"><div class="value">{total_tokens}</div><div class="label">Total Tokens</div></div>
    <div class="metric"><div class="value">{avg_quality}</div><div class="label">Avg Prompt Quality</div></div>
    <div class="metric"><div class="value">{skill_pct}%</div><div class="label">Avg Skill Adoption</div></div>
    <div class="metric"><div class="value" style="color:{maturity_color}">{overall_label}</div><div class="label">Team Maturity</div></div>
  </div>

  <div class="card">
    <h2>Maturity by Dimension (Team Average)</h2>
    <table>
      <tr><th>Dimension</th><th>Score</th><th>Avg Level</th></tr>
      {dim_rows}
    </table>
  </div>

  <div class="card">
    <h2>Individual Members</h2>
    <table>
      <tr><th>Developer</th><th>Sessions</th><th>Avg Quality</th><th>Skill Adoption</th><th>Maturity</th></tr>
      {member_rows}
    </table>
  </div>
</body>
</html>""".format(
        team_size=team_size,
        total_sessions=team_report.get("total_sessions", 0),
        total_tokens=fmt_tokens(team_report.get("total_tokens")),
        avg_quality=team_report.get("avg_prompt_quality") or "—",
        skill_pct=int((team_report.get("avg_skill_invocation_ratio") or 0) * 100),
        maturity_color=maturity_color,
        overall_label=overall_label,
        dim_rows=dim_rows,
        member_rows=member_rows,
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_team.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/auto_sdlc/logs/team.py tests/logs/test_team.py
git commit -m "feat: add team rollup builder and HTML renderer"
```

---

## Task 8: Data Export

Write report data to a local directory (for simulated aggregation) and optionally POST to an HTTP endpoint.

**Files:**
- Create: `src/auto_sdlc/logs/export.py`
- Create: `tests/logs/test_export.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/logs/test_export.py
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from auto_sdlc.logs.export import export_report_to_dir, export_report_to_http


def _sample():
    return {"user_id": "alice@example.com", "summary": {"total_sessions": 5}}


def test_export_to_dir_creates_file(tmp_path):
    path = export_report_to_dir(_sample(), tmp_path)
    assert Path(path).exists()


def test_export_to_dir_valid_json(tmp_path):
    path = export_report_to_dir(_sample(), tmp_path)
    data = json.loads(Path(path).read_text())
    assert data["user_id"] == "alice@example.com"


def test_export_to_dir_filename_contains_user_id(tmp_path):
    path = export_report_to_dir(_sample(), tmp_path)
    assert "alice_at_example.com" in Path(path).name


def test_export_to_dir_creates_parent_dirs(tmp_path):
    dest = tmp_path / "deep" / "nested"
    export_report_to_dir(_sample(), dest)
    assert dest.exists()


def test_export_to_http_returns_true_on_200():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = export_report_to_http(_sample(), "http://localhost:9999/ingest")
    assert result is True


def test_export_to_http_returns_false_on_connection_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = export_report_to_http(_sample(), "http://localhost:9999/ingest")
    assert result is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/logs/test_export.py -v
```

Expected: All 6 tests FAIL.

- [ ] **Step 3: Write `src/auto_sdlc/logs/export.py`**

```python
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


def export_report_to_dir(report, dest_dir):
    """Write report as a dated JSON file. Returns the path written."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    user_id = report.get("user_id", "unknown")
    safe_user = user_id.replace("@", "_at_").replace("/", "_").replace("\\", "_")
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    dest = dest_dir / "{}_{}.json".format(safe_user, ts)
    dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return str(dest)


def export_report_to_http(report, url, timeout=10):
    """POST report JSON to a URL. Returns True on HTTP success (<400)."""
    payload = json.dumps(report, default=str).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except urllib.error.URLError:
        return False
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/logs/test_export.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Add `--export-dir` and `--export-url` flags to `logs` command in `cli.py`**

Add these two options to the `logs` command in `src/auto_sdlc/cli.py` (inside the `@cli.command()` block):

```python
@click.option("--export-dir", default=None,
              help="Also write report to this dir (for team aggregation).")
@click.option("--export-url", default=None,
              help="Also POST report to this URL.")
```

And add handling at the end of the `logs` function body (after the `if html` block):

```python
    if export_dir and not summary_only:
        from auto_sdlc.logs.export import export_report_to_dir
        path = export_report_to_dir(report, export_dir)
        click.echo(f"Report exported to {path}")

    if export_url and not summary_only:
        from auto_sdlc.logs.export import export_report_to_http
        ok = export_report_to_http(report, export_url)
        if ok:
            click.echo(f"Report POSTed to {export_url}")
        else:
            click.echo(f"Warning: failed to POST report to {export_url}", err=True)
```

Update the function signature to include the new params:

```python
def logs(projects_dir, output, project, since, summary_only, user_id, qualitative, html, export_dir, export_url):
```

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/auto_sdlc/logs/export.py tests/logs/test_export.py src/auto_sdlc/cli.py
git commit -m "feat: add export module and --export-dir/--export-url CLI flags"
```

---

## Task 9: End-to-End Smoke Test

Verify the full pipeline works against real local session data.

- [ ] **Step 1: Run full test suite one final time**

```bash
cd /Users/smannar/auto-sdlc
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 2: Generate a real individual report**

```bash
auto-sdlc logs --user-id "srivaths@headstorm.com" --summary-only
```

Expected: JSON printed to stdout with `behavioral_metrics`, `maturity_scores`.

- [ ] **Step 3: Generate full report + HTML**

```bash
auto-sdlc logs --user-id "srivaths@headstorm.com" --html
```

Expected: Two lines printed:
```
Report saved to ~/.auto-sdlc/reports/srivaths_at_headstorm.com/2026-03-31_HHMMSS.json
HTML report saved to ~/.auto-sdlc/reports/srivaths_at_headstorm.com/2026-03-31_HHMMSS.html
```

- [ ] **Step 4: Open the HTML report**

```bash
open $(ls -t ~/.auto-sdlc/reports/srivaths_at_headstorm.com/*.html | head -1)
```

Expected: Browser opens showing metric cards, maturity bars, project breakdown.

- [ ] **Step 5: Mock team rollup**

```bash
# Copy the real report to a team dir twice with different user names (to simulate team)
mkdir -p /tmp/team-demo
cp $(ls -t ~/.auto-sdlc/reports/srivaths_at_headstorm.com/*.json | head -1) /tmp/team-demo/dev1.json
cp $(ls -t ~/.auto-sdlc/reports/srivaths_at_headstorm.com/*.json | head -1) /tmp/team-demo/dev2.json

# Edit dev2.json to change user_id (simulate second team member)
python3 -c "
import json, pathlib
p = pathlib.Path('/tmp/team-demo/dev2.json')
d = json.loads(p.read_text())
d['user_id'] = 'dev2@headstorm.com'
p.write_text(json.dumps(d, indent=2))
"

auto-sdlc team --reports-dir /tmp/team-demo --html
open /tmp/team-demo/team_report.html
```

Expected: Team HTML report opens showing both members with maturity breakdown.

- [ ] **Step 6: Final commit**

```bash
cd /Users/smannar/auto-sdlc
git add .
git commit -m "feat: complete logs v2 — behavioral metrics, maturity scoring, HTML reports, team rollup, export"
```

---

## Self-Review

**Spec coverage:**
- ✅ Default save to JSON file (Task 4 — `run_logs_report` defaults to `~/.auto-sdlc/reports/`)
- ✅ Individual visualization (Task 6 — HTML with metric cards, maturity bars, project breakdown)
- ✅ Project breakdown (Task 4 — `_build_project_breakdown` groups by cwd)
- ✅ Team rollup mock (Task 7 — `build_team_report` + team HTML)
- ✅ Data exfil (Task 8 — `export_to_dir` + `export_to_http`)
- ✅ LLM qualitative analysis via `claude -p` (Task 3)
- ✅ Quantitative metrics (Task 1 — skill ratio, tool use; Task 2 — maturity dimensions)

**Placeholder scan:** None found. All code blocks are complete.

**Type consistency:**
- `aggregate_behavioral_metrics(all_session_events, total_days_active)` used in Task 1 tests and called in Task 4 `report.py` ✅
- `build_maturity_report(behavioral, avg_prompt_quality, token_usage_agg)` used in Tasks 2, 4 ✅
- `run_logs_report(...)` returns `report` dict — used in Task 9 smoke test ✅
- `build_team_report(user_reports)` takes list of `(str, dict)` tuples — consistent in Tasks 7, 9 ✅
