"""Individual HTML report renderer for user analytics."""

from html import escape

_LEVEL_COLORS = {0: "#e74c3c", 1: "#e67e22", 2: "#f1c40f", 3: "#2ecc71", 4: "#27ae60"}


def _fmt_tokens(n):
    if n is None:
        return "—"
    if n >= 1_000_000:
        return "{:.1f}M".format(n / 1_000_000)
    if n >= 1_000:
        return "{:.0f}K".format(n / 1_000)
    return str(n)


def _format_metric_row(name, value, unit):
    """Build an HTML table row for a metric with escaped values.

    Args:
        name: Metric name (will be HTML-escaped)
        value: Metric value (will be HTML-escaped)
        unit: Unit label (will be HTML-escaped)

    Returns:
        HTML table row string
    """
    # Ensure value has a default fallback
    if value is None:
        value = "—"

    return (
        "<tr>"
        "<td style='padding:5px 10px;font-size:12px'>{name}</td>"
        "<td style='padding:5px 10px;font-size:12px;text-align:right;font-weight:500'>{value}</td>"
        "<td style='padding:5px 10px;font-size:11px;color:#777'>{unit}</td>"
        "</tr>"
    ).format(
        name=escape(str(name)),
        value=escape(str(value)),
        unit=escape(str(unit))
    )


def _format_dimension_details(dimension_key, dim_data, report):
    """Generate metrics table HTML for a dimension's collapsible details.

    Args:
        dimension_key: The dimension identifier (e.g., 'prompting_sophistication')
        dim_data: The dimension data dict with label, level, level_label
        report: The full report dict

    Returns:
        HTML string for the metrics table rows
    """
    summary = report.get("summary", {})
    behavioral = report.get("behavioral_metrics", {})

    metrics = []

    if dimension_key == "prompting_sophistication":
        metrics = [
            ("Avg Prompt Quality", summary.get("avg_prompt_quality_score") or "—", "score (0-100)"),
        ]

    elif dimension_key == "tooling_adoption":
        ratio = behavioral.get("skill_invocation_ratio", 0)
        skill_pct = int(ratio * 100) if ratio else 0
        metrics = [
            ("Skill Invocation Ratio", "{}%".format(skill_pct), "% of all tool calls"),
            ("Total Skill Invocations", behavioral.get("total_skill_invocations", 0), "calls"),
            ("Total Tool Calls", behavioral.get("total_tool_calls", 0), "calls"),
            ("Unique Tools Used", len(behavioral.get("unique_tools_used", [])), "tools"),
        ]

    elif dimension_key == "usage_frequency":
        metrics = [
            ("Sessions Per Day", behavioral.get("sessions_per_day") or "—", "sessions/day"),
            ("Total Sessions", summary.get("total_sessions", 0), "sessions"),
        ]

    elif dimension_key == "session_depth":
        metrics = [
            ("Avg Messages Per Session", behavioral.get("avg_messages_per_session") or "—", "messages"),
            ("Avg Session Duration", summary.get("avg_session_duration_ms") or "—", "minutes"),
            ("Total User Messages", behavioral.get("total_user_messages", 0), "messages"),
        ]

    elif dimension_key == "context_efficiency":
        total_tokens = summary.get("total_tokens", 0)
        cache_read = summary.get("total_cache_read_tokens", 0)
        cache_hit = (cache_read / total_tokens * 100) if total_tokens > 0 else 0
        metrics = [
            ("Cache Hit Ratio", "{:.1f}%".format(cache_hit), "% of tokens"),
            ("Cache Read Tokens", _fmt_tokens(cache_read), "tokens"),
            ("Total Tokens", _fmt_tokens(total_tokens), "tokens"),
        ]

    else:
        # Fallback for unrecognized dimensions
        metrics = [
            ("Metrics", "Metrics not available", ""),
        ]

    rows = ""
    for metric_name, metric_value, metric_unit in metrics:
        rows += _format_metric_row(metric_name, metric_value, metric_unit)

    return rows


def _format_team_dimension_details(dimension_key, dim_data, team_report, user_reports):
    """Generate metrics table HTML for a team dimension's collapsible details.

    Args:
        dimension_key: The dimension identifier (e.g., 'prompting_sophistication')
        dim_data: The team dimension data dict with label, avg_level, member_levels
        team_report: The team report dict
        user_reports: List of individual user report dicts

    Returns:
        HTML string for the metrics table rows
    """
    metrics = []
    member_levels = dim_data.get("member_levels", [])
    avg_level = dim_data.get("avg_level", 0)

    if dimension_key == "prompting_sophistication":
        # Collect avg prompt quality from all developers
        quality_scores = []
        for report in user_reports:
            score = report.get("summary", {}).get("avg_prompt_quality_score")
            if score is not None:
                quality_scores.append(score)

        avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else None
        level_dist = _get_level_distribution(member_levels, len(user_reports))

        metrics = [
            ("Team Avg Prompt Quality", avg_quality or "—", "score (0-100)"),
            ("Developers at Level 3+", level_dist.get("level_3_plus", 0), "count"),
            ("% at Level 3+", "{}%".format(level_dist.get("pct_3_plus", 0)), "percentage"),
        ]

    elif dimension_key == "tooling_adoption":
        # Collect skill ratios from all developers
        skill_ratios = []
        all_tools = set()
        for report in user_reports:
            ratio = report.get("behavioral_metrics", {}).get("skill_invocation_ratio")
            if ratio is not None:
                skill_ratios.append(ratio)
            tools = report.get("behavioral_metrics", {}).get("unique_tools_used", [])
            all_tools.update(tools)

        avg_ratio = round(sum(skill_ratios) / len(skill_ratios) * 100, 1) if skill_ratios else 0
        developers_with_tools = sum(1 for ratio in skill_ratios if ratio > 0)

        metrics = [
            ("Team Avg Skill Ratio", "{}%".format(avg_ratio), "% of tool calls"),
            ("Developers Using Tools", developers_with_tools, "count"),
            ("Unique Tools Across Team", len(all_tools), "tools"),
        ]

    elif dimension_key == "usage_frequency":
        # Collect sessions per day from all developers
        spd_values = []
        total_team_sessions = 0
        for report in user_reports:
            spd = report.get("behavioral_metrics", {}).get("sessions_per_day")
            if spd is not None:
                spd_values.append(spd)
            total_team_sessions += report.get("summary", {}).get("total_sessions", 0)

        avg_spd = round(sum(spd_values) / len(spd_values), 2) if spd_values else None
        min_spd = round(min(spd_values), 2) if spd_values else None
        max_spd = round(max(spd_values), 2) if spd_values else None

        metrics = [
            ("Team Avg Sessions/Day", avg_spd or "—", "sessions/day"),
            ("Range (Min-Max)", "{}-{}".format(min_spd or "—", max_spd or "—"), "sessions/day"),
            ("Total Team Sessions", total_team_sessions, "sessions"),
        ]

    elif dimension_key == "session_depth":
        # Collect messages per session from all developers
        msg_per_session = []
        for report in user_reports:
            msgs = report.get("behavioral_metrics", {}).get("avg_messages_per_session")
            if msgs is not None:
                msg_per_session.append(msgs)

        avg_msgs = round(sum(msg_per_session) / len(msg_per_session), 1) if msg_per_session else None
        min_msgs = round(min(msg_per_session), 1) if msg_per_session else None
        max_msgs = round(max(msg_per_session), 1) if msg_per_session else None

        metrics = [
            ("Team Avg Messages/Session", avg_msgs or "—", "messages"),
            ("Range (Min-Max)", "{}-{}".format(min_msgs or "—", max_msgs or "—"), "messages"),
        ]

    elif dimension_key == "context_efficiency":
        # Collect cache hit ratios from all developers
        cache_ratios = []
        total_tokens = 0
        total_cache_read = 0
        for report in user_reports:
            total = report.get("summary", {}).get("total_tokens", 0)
            cache_read = report.get("summary", {}).get("total_cache_read_tokens", 0)
            total_tokens += total
            total_cache_read += cache_read
            if total > 0:
                cache_ratios.append(cache_read / total * 100)

        team_cache_hit = (total_cache_read / total_tokens * 100) if total_tokens > 0 else 0
        avg_cache_hit = round(sum(cache_ratios) / len(cache_ratios), 1) if cache_ratios else 0

        metrics = [
            ("Team Cache Hit Ratio", "{:.1f}%".format(team_cache_hit), "% of tokens"),
            ("Avg Individual Hit Ratio", "{:.1f}%".format(avg_cache_hit), "% of tokens"),
            ("Total Cache Read Tokens", _fmt_tokens(total_cache_read), "tokens"),
        ]

    else:
        # Fallback for unrecognized dimensions
        metrics = [
            ("Metrics", "Metrics not available", ""),
        ]

    rows = ""
    for metric_name, metric_value, metric_unit in metrics:
        rows += _format_metric_row(metric_name, metric_value, metric_unit)

    return rows


def _get_level_distribution(levels, total_developers):
    """Calculate distribution of developers across maturity levels.

    Args:
        levels: List of maturity levels (0-4)
        total_developers: Total number of developers

    Returns:
        Dict with counts and percentages
    """
    level_counts = {}
    for level in range(5):
        count = levels.count(level)
        level_counts[level] = count

    # Calculate developers at level 3+ (advanced and expert)
    level_3_plus = level_counts.get(3, 0) + level_counts.get(4, 0)
    pct_3_plus = int(level_3_plus / total_developers * 100) if total_developers > 0 else 0

    return {
        "level_counts": level_counts,
        "level_3_plus": level_3_plus,
        "pct_3_plus": pct_3_plus,
    }


def render_individual_html(report):
    """Render a self-contained HTML report for a single user."""
    user_id = report.get("user_id", "unknown")
    generated_at = report.get("generated_at", "")
    summary = report.get("summary", {})
    behavioral = report.get("behavioral_metrics", {})
    maturity = report.get("maturity_scores", {})
    project_breakdown = report.get("project_breakdown") or []
    qualitative_analysis = report.get("qualitative_analysis")

    overall_level = maturity.get("overall_level", 0)
    overall_label = maturity.get("overall_label", "Unknown")
    maturity_color = _LEVEL_COLORS.get(overall_level, "#999")

    # Maturity dimensions bars with collapsible metrics
    dim_rows = ""
    dimensions_dict = maturity.get("dimensions", {})
    for dim_key, dim_data in dimensions_dict.items():
        pct = int(dim_data.get("level", 0) / 4 * 100)
        metrics_rows = _format_dimension_details(dim_key, dim_data, report)
        dim_rows += (
            "<tr>"
            "<td colspan='3' style='padding:0'>"
            "<details class='dimension-details'>"
            "<summary style='padding:6px 10px;cursor:pointer;display:flex;justify-content:space-between;align-items:center'>"
            "<div style='display:flex;flex:1;gap:10px;align-items:center'>"
            "<div style='width:220px'><strong>{label}</strong></div>"
            "<div style='display:flex;align-items:center;gap:10px'>"
            "<div style='background:#eee;border-radius:4px;height:16px;width:200px'>"
            "<div style='background:#4a90d9;border-radius:4px;height:16px;width:{pct}%'></div>"
            "</div>"
            "<div style='color:#555;white-space:nowrap'>{level_label} ({level}/4)</div>"
            "</div>"
            "</div>"
            "<span style='font-size:11px;color:#999;margin-right:8px'>▼</span>"
            "</summary>"
            "<div style='padding:10px;background:#f9f9f9;border-top:1px solid #eee'>"
            "<table style='width:100%;font-size:12px'>"
            "{metrics_rows}"
            "</table>"
            "</div>"
            "</details>"
            "</td>"
            "</tr>"
        ).format(
            label=escape(dim_data.get("label", "")),
            pct=pct,
            level_label=escape(dim_data.get("level_label", "")),
            level=dim_data.get("level", 0),
            metrics_rows=metrics_rows,
        )

    # Project breakdown rows
    proj_rows = ""
    for p in project_breakdown:
        proj_rows += (
            "<tr>"
            "<td style='padding:5px 10px'>{project}</td>"
            "<td style='padding:5px 10px;text-align:right'>{sessions}</td>"
            "<td style='padding:5px 10px;text-align:right'>{tokens}</td>"
            "<td style='padding:5px 10px;text-align:right'>{quality}</td>"
            "</tr>"
        ).format(
            project=escape(p.get("project", "unknown")),
            sessions=p.get("sessions", 0),
            tokens=_fmt_tokens(p.get("total_tokens")),
            quality=escape(str(p.get("avg_prompt_quality") or "—")),
        )

    # Qualitative section
    qual_html = ""
    if qualitative_analysis:
        narrative = qualitative_analysis.get("narrative", "") or ""
        workflows = qualitative_analysis.get("workflow_patterns", {}).get("workflows", [])
        anti_patterns = qualitative_analysis.get("anti_patterns", {}).get("anti_patterns", [])

        wf_items = "".join(
            "<li style='padding:4px 0;border-bottom:1px solid #f0f0f0'>"
            "<strong>{}</strong> — {}</li>".format(
                escape(w.get("pattern", "")), escape(w.get("evidence", ""))
            ) for w in workflows
        )
        ap_items = "".join(
            "<li style='padding:4px 0;border-bottom:1px solid #f0f0f0'>"
            "<strong>{}</strong>: {}</li>".format(
                escape(a.get("name", "")), escape(a.get("recommendation", ""))
            ) for a in anti_patterns
        )

        qual_html = """
  <div class="card">
    <h2>Qualitative Analysis</h2>
    <p style="color:#555;line-height:1.6;margin-bottom:16px">{narrative}</p>
    <div style="display:flex;gap:24px;flex-wrap:wrap">
      <div style="flex:1;min-width:200px">
        <h3 style="font-size:14px;margin-bottom:8px;color:#333">Workflow Patterns</h3>
        <ul style="list-style:none;padding:0">{wf_items}</ul>
      </div>
      <div style="flex:1;min-width:200px">
        <h3 style="font-size:14px;margin-bottom:8px;color:#333">Anti-Patterns</h3>
        <ul style="list-style:none;padding:0">{ap_items}</ul>
      </div>
    </div>
  </div>""".format(narrative=escape(narrative), wf_items=wf_items, ap_items=ap_items)

    skill_pct = int((behavioral.get("skill_invocation_ratio") or 0) * 100)

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Auto-SDLC Report — {user_id}</title>
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
    .dimension-details{{width:100%}}
    .dimension-details summary{{outline:none}}
    .dimension-details summary:hover{{background:#f5f5f5}}
    .dimension-details[open] summary{{background:#f5f5f5}}
  </style>
</head>
<body>
  <h1>Auto-SDLC Developer Report</h1>
  <p style="color:#888;font-size:13px;margin-bottom:20px">{user_id} &middot; {generated_at}</p>

  <div class="metric-row">
    <div class="metric"><div class="value">{total_sessions}</div><div class="label">Total Sessions</div></div>
    <div class="metric"><div class="value">{total_tokens}</div><div class="label">Total Tokens</div></div>
    <div class="metric"><div class="value">{avg_quality}</div><div class="label">Avg Prompt Quality</div></div>
    <div class="metric"><div class="value">{skill_pct}%</div><div class="label">Skill Adoption</div></div>
    <div class="metric"><div class="value">{spd}</div><div class="label">Sessions / Day</div></div>
    <div class="metric"><div class="value" style="color:{maturity_color}">{overall_label}</div><div class="label">Maturity Level</div></div>
  </div>

  <div class="card">
    <h2>Maturity by Dimension</h2>
    <table>
      <tr><th>Dimension</th><th>Score</th><th>Level</th></tr>
      {dim_rows}
    </table>
  </div>

  <div class="card">
    <h2>Project Breakdown</h2>
    <table>
      <tr><th>Project</th><th>Sessions</th><th>Tokens</th><th>Avg Quality</th></tr>
      {proj_rows}
    </table>
  </div>
{qual_html}
</body>
</html>""".format(
        user_id=escape(user_id),
        generated_at=generated_at[:19].replace("T", " ") if generated_at else "",
        total_sessions=summary.get("total_sessions", 0),
        total_tokens=_fmt_tokens(summary.get("total_tokens")),
        avg_quality=escape(str(summary.get("avg_prompt_quality_score") or "—")),
        skill_pct=skill_pct,
        spd=escape(str(behavioral.get("sessions_per_day") or "—")),
        maturity_color=maturity_color,
        overall_label=escape(overall_label),
        dim_rows=dim_rows,
        proj_rows=proj_rows,
        qual_html=qual_html,
    )


def render_team_html(team_report, user_reports=None):
    """Render a self-contained team HTML report with collapsible dimension details.

    Args:
        team_report: The aggregated team report dict
        user_reports: Optional list of individual user report dicts (for detailed metrics)

    Returns:
        HTML string
    """
    if user_reports is None:
        user_reports = []

    team_size = team_report.get("team_size", 0)
    overall_level = team_report.get("overall_maturity_level", 0)
    overall_label = team_report.get("overall_maturity_label", "—")
    maturity_color = _LEVEL_COLORS.get(overall_level, "#999")

    # Maturity dimensions bars with collapsible metrics
    dim_rows = ""
    for dim_key, dim_data in team_report.get("maturity_by_dimension", {}).items():
        pct = int(dim_data.get("avg_level", 0) / 4 * 100)
        metrics_rows = _format_team_dimension_details(dim_key, dim_data, team_report, user_reports)
        dim_rows += (
            "<tr>"
            "<td colspan='3' style='padding:0'>"
            "<details class='dimension-details'>"
            "<summary style='padding:6px 10px;cursor:pointer;display:flex;justify-content:space-between;align-items:center'>"
            "<div style='display:flex;flex:1;gap:10px;align-items:center'>"
            "<div style='width:220px'><strong>{label}</strong></div>"
            "<div style='display:flex;align-items:center;gap:10px'>"
            "<div style='background:#eee;border-radius:4px;height:16px;width:200px'>"
            "<div style='background:#4a90d9;border-radius:4px;height:16px;width:{pct}%'></div>"
            "</div>"
            "<div style='color:#555;white-space:nowrap'>{avg_label} ({avg_level}/4)</div>"
            "</div>"
            "</div>"
            "<span style='font-size:11px;color:#999;margin-right:8px'>▼</span>"
            "</summary>"
            "<div style='padding:10px;background:#f9f9f9;border-top:1px solid #eee'>"
            "<table style='width:100%;font-size:12px'>"
            "{metrics_rows}"
            "</table>"
            "</div>"
            "</details>"
            "</td>"
            "</tr>"
        ).format(
            label=escape(dim_data.get("label", "")),
            pct=pct,
            avg_label=escape(dim_data.get("avg_label", "")),
            avg_level=dim_data.get("avg_level", 0),
            metrics_rows=metrics_rows,
        )

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
            user_id=escape(m.get("user_id", "unknown")),
            sessions=m.get("sessions", 0),
            quality=escape(str(m.get("avg_prompt_quality") or "—")),
            skill_pct=skill_pct,
            color=color,
            label=escape(m.get("overall_maturity_label", "—")),
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
    .dimension-details{{width:100%}}
    .dimension-details summary{{outline:none}}
    .dimension-details summary:hover{{background:#f5f5f5}}
    .dimension-details[open] summary{{background:#f5f5f5}}
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
      <tr><th>Dimension</th><th>Score</th><th>Level</th></tr>
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
        total_tokens=_fmt_tokens(team_report.get("total_tokens")),
        avg_quality=escape(str(team_report.get("avg_prompt_quality") or "—")),
        skill_pct=int((team_report.get("avg_skill_invocation_ratio") or 0) * 100),
        maturity_color=maturity_color,
        overall_label=escape(overall_label),
        dim_rows=dim_rows,
        member_rows=member_rows,
    )
