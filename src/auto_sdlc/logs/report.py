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
        dest = user_dir / "{}.json".format(ts)

    dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("Report saved to {}".format(dest))
    return report
