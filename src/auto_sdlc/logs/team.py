import json
from pathlib import Path
from auto_sdlc.logs.render_html import render_team_html

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


# Note: render_team_html is now imported from render_html.py for consistency with individual reports
