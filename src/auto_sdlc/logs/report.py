import json
from datetime import datetime, timezone
from pathlib import Path

from auto_sdlc.logs.parser import parse_session_file, find_session_files
from auto_sdlc.logs.analyzer import (
    extract_token_usage,
    extract_session_metadata,
    aggregate_sessions,
)
from auto_sdlc.logs.scorer import score_session_prompts


def build_report(projects_dir):
    """Parse all session files under projects_dir and return a report dict."""
    projects_dir = Path(projects_dir)
    session_files = find_session_files(projects_dir)

    all_session_events = [parse_session_file(f) for f in session_files]

    sessions = []
    all_prompt_scores = []

    for events in all_session_events:
        token_usage = extract_token_usage(events)
        metadata = extract_session_metadata(events)
        prompt_scores = score_session_prompts(events)
        all_prompt_scores.extend(s["score"] for s in prompt_scores)
        sessions.append({
            "session_id": metadata["session_id"],
            "metadata": metadata,
            "token_usage": token_usage,
            "prompt_scores": prompt_scores,
        })

    aggregate = aggregate_sessions(all_session_events)
    avg_quality = (
        round(sum(all_prompt_scores) / len(all_prompt_scores), 1)
        if all_prompt_scores else None
    )

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "projects_dir": str(projects_dir),
        "summary": {
            **aggregate,
            "avg_prompt_quality_score": avg_quality,
        },
        "sessions": sessions,
    }


def run_logs_report(projects_dir, output_path):
    """Entry point called by CLI. Builds and emits the report."""
    default_dir = Path.home() / ".claude" / "projects"
    resolved_dir = Path(projects_dir) if projects_dir else default_dir

    report = build_report(resolved_dir)
    output = json.dumps(report, indent=2, default=str)

    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
        print(f"Report written to {output_path}")
    else:
        print(output)
