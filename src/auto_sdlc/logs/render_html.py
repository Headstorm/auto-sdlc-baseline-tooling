"""Individual HTML report renderer for user analytics."""

_LEVEL_COLORS = {0: "#e74c3c", 1: "#e67e22", 2: "#f1c40f", 3: "#2ecc71", 4: "#27ae60"}


def _fmt_tokens(n):
    if n is None:
        return "—"
    if n >= 1_000_000:
        return "{:.1f}M".format(n / 1_000_000)
    if n >= 1_000:
        return "{:.0f}K".format(n / 1_000)
    return str(n)


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

    # Maturity dimensions bars
    dim_rows = ""
    for dim_data in maturity.get("dimensions", {}).values():
        pct = int(dim_data.get("level", 0) / 4 * 100)
        dim_rows += (
            "<tr>"
            "<td style='padding:6px 10px;width:220px'>{label}</td>"
            "<td style='padding:6px 10px'>"
            "<div style='background:#eee;border-radius:4px;height:16px;width:200px'>"
            "<div style='background:#4a90d9;border-radius:4px;height:16px;width:{pct}%'></div>"
            "</div></td>"
            "<td style='padding:6px 10px;color:#555'>{level_label} ({level}/4)</td>"
            "</tr>"
        ).format(
            label=dim_data.get("label", ""),
            pct=pct,
            level_label=dim_data.get("level_label", ""),
            level=dim_data.get("level", 0),
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
            project=p.get("project", "unknown"),
            sessions=p.get("sessions", 0),
            tokens=_fmt_tokens(p.get("total_tokens")),
            quality=p.get("avg_prompt_quality") if p.get("avg_prompt_quality") is not None else "—",
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
                w.get("pattern", ""), w.get("evidence", "")
            ) for w in workflows
        )
        ap_items = "".join(
            "<li style='padding:4px 0;border-bottom:1px solid #f0f0f0'>"
            "<strong>{}</strong>: {}</li>".format(
                a.get("name", ""), a.get("recommendation", "")
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
  </div>""".format(narrative=narrative, wf_items=wf_items, ap_items=ap_items)

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
        user_id=user_id,
        generated_at=generated_at[:19].replace("T", " ") if generated_at else "",
        total_sessions=summary.get("total_sessions", 0),
        total_tokens=_fmt_tokens(summary.get("total_tokens")),
        avg_quality=summary.get("avg_prompt_quality_score") or "—",
        skill_pct=skill_pct,
        spd=behavioral.get("sessions_per_day") or "—",
        maturity_color=maturity_color,
        overall_label=overall_label,
        dim_rows=dim_rows,
        proj_rows=proj_rows,
        qual_html=qual_html,
    )
