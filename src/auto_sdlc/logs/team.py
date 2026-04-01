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
