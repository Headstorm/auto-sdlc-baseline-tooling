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
        "  user_id: {}".format(report.get("user_id", "unknown")),
        "  total_sessions: {}".format(summary.get("total_sessions")),
        "  avg_prompt_quality: {}".format(summary.get("avg_prompt_quality_score")),
        "  maturity_level: {} ({}/4)".format(
            maturity.get("overall_label", "Unknown"),
            maturity.get("overall_level", "?"),
        ),
        "  skill_invocation_ratio: {}".format(behavioral.get("skill_invocation_ratio")),
        "  avg_messages_per_session: {}".format(behavioral.get("avg_messages_per_session")),
        "  sessions_per_day: {}".format(behavioral.get("sessions_per_day")),
        "",
        "Sample prompts (up to 15):",
    ] + ["  - {}".format(p) for p in sample_prompts[:15]]

    return "\n".join(lines)


def analyze_workflow_patterns(report):
    """Identify dominant workflows. Returns dict with 'workflows' list."""
    context = _context_summary(report)
    prompt = (
        "You are analyzing a developer's Claude Code usage data. "
        "Based on the following metrics and sample prompts, identify 2-3 dominant workflow patterns "
        "(e.g. 'primarily debugging', 'heavy refactoring', 'new feature development').\n\n"
        "{}\n\n"
        "Respond with ONLY a JSON object: "
        '{{"workflows": [{{"pattern": "short name", "evidence": "one sentence"}}]}}. '
        "No prose outside the JSON."
    ).format(context)
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
        "{}\n\n"
        "Respond with ONLY a JSON object: "
        '{{"anti_patterns": [{{"name": "short label", "recommendation": "one actionable sentence"}}]}}. '
        "No prose outside the JSON."
    ).format(context)
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
        "{}\n\n"
        "Respond with plain text only. 2-3 sentences."
    ).format(context)
    return run_llm(prompt) or "Qualitative analysis unavailable."


def run_full_qualitative_analysis(report):
    """Run all three analyses and return combined dict."""
    return {
        "workflow_patterns": analyze_workflow_patterns(report),
        "anti_patterns": analyze_anti_patterns(report),
        "narrative": analyze_maturity_narrative(report),
    }
