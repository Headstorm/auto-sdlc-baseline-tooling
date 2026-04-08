"""Central collection server for auto-sdlc reports."""
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
except ImportError:
    raise ImportError("Server dependencies not installed. Run: pip install auto-sdlc[server]")

from auto_sdlc.logs.team import build_team_report, render_team_html


def _find_projects_dir(extracted_root):
    """
    Given the root of an extracted ZIP, find the directory that contains .jsonl files.
    Handles three layouts:
      - extracted_root/projects/myapp/*.jsonl   (user zipped ~/.claude/)
      - extracted_root/myapp/*.jsonl            (user zipped ~/.claude/projects/)
      - extracted_root/*.jsonl                  (user zipped contents of projects/)
    Returns the deepest directory that has JSONL files as a descendant.
    """
    # Walk directories breadth-first; return the first ancestor of any .jsonl file
    jsonl_files = list(extracted_root.rglob("*.jsonl"))
    if not jsonl_files:
        return extracted_root

    # Find the common root: the highest directory that still contains all jsonl files
    # Prefer a directory named "projects/" if one exists in the path
    for f in jsonl_files:
        for parent in f.parents:
            if parent.name == "projects" and parent != extracted_root:
                return parent

    # Fall back: return the parent of the first jsonl file's parent (project dir level)
    # e.g. extracted/myapp/session.jsonl -> return extracted/
    first = jsonl_files[0]
    # Go up until we find a dir that is a direct child of extracted_root
    for parent in first.parents:
        if parent.parent == extracted_root:
            return extracted_root

    return extracted_root


def create_app(reports_dir):
    """Create the FastAPI app, storing reports in reports_dir."""
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Auto-SDLC Collection Server")

    @app.get("/health")
    def health():
        return {"status": "ok", "reports_dir": str(reports_path)}

    @app.get("/", response_class=HTMLResponse)
    def upload_form():
        """Self-contained upload form — no CLI needed for developers."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Auto-SDLC — Submit Your Logs</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh;color:#222}
    .card{background:white;border-radius:10px;padding:40px 48px;box-shadow:0 2px 12px rgba(0,0,0,.1);max-width:480px;width:100%}
    h1{margin:0 0 6px 0;font-size:22px}
    p{color:#666;font-size:14px;margin:0 0 28px 0}
    label{display:block;font-size:13px;font-weight:600;color:#444;margin-bottom:6px}
    input[type=email],input[type=file]{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:18px}
    input[type=file]{padding:8px 10px;color:#555}
    button{width:100%;padding:12px;background:#4a90d9;color:white;border:none;border-radius:6px;font-size:15px;font-weight:600;cursor:pointer}
    button:hover{background:#357abd}
    .hint{font-size:12px;color:#999;margin-top:20px;line-height:1.6}
    code{background:#f0f0f0;padding:2px 5px;border-radius:3px;font-size:11px}
  </style>
</head>
<body>
  <div class="card">
    <h1>Auto-SDLC Log Analysis</h1>
    <p>Upload your Claude Code session logs to generate your maturity report.</p>
    <form action="/upload" method="post" enctype="multipart/form-data">
      <label>Your email address</label>
      <input type="email" name="user_id" placeholder="you@company.com" required>
      <label>Claude logs ZIP file</label>
      <input type="file" name="logs_zip" accept=".zip" required>
      <button type="submit">Upload &amp; Analyze</button>
    </form>
    <div class="hint">
      <strong>How to create the ZIP:</strong><br>
      <code>cd ~/.claude && zip -r ~/claude-logs.zip projects/</code><br><br>
      Then upload the <code>claude-logs.zip</code> file above.
    </div>
  </div>
</body>
</html>"""

    @app.post("/upload")
    async def upload_logs(user_id: str = Form(...), logs_zip: UploadFile = File(...)):
        """Receive a ZIP of raw Claude Code logs, run analysis server-side, redirect to dashboard."""
        if not (logs_zip.filename or "").endswith(".zip"):
            raise HTTPException(status_code=400, detail="File must be a .zip archive")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write and extract the ZIP
            zip_path = tmp_path / "upload.zip"
            zip_path.write_bytes(await logs_zip.read())

            try:
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(tmp_path)
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="Invalid ZIP file")

            # Detect where the .jsonl files live inside the extracted content
            projects_dir = _find_projects_dir(tmp_path)

            # Run the full analysis pipeline (same as auto-sdlc logs)
            from auto_sdlc.logs.report import build_report
            report = build_report(projects_dir=projects_dir, user_id=user_id)

        # Save report to reports_dir
        safe_user = user_id.replace("@", "_at_").replace("/", "_")
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        dest = reports_path / "{}_{}.json".format(safe_user, ts)
        dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

        return RedirectResponse(url="/dashboard/{}".format(safe_user), status_code=303)

    @app.get("/dashboard/{user_id}", response_class=HTMLResponse)
    def user_dashboard(user_id: str):
        """Render the individual HTML report for a user."""
        matches = sorted(reports_path.glob("{}_*.json".format(user_id)))
        if not matches:
            raise HTTPException(status_code=404, detail="No report found for '{}'".format(user_id))

        report = json.loads(matches[-1].read_text(encoding="utf-8"))

        from auto_sdlc.logs.render_html import render_individual_html
        html = render_individual_html(report)
        # Inject a team dashboard link just after <body>
        nav = (
            '<div style="padding:10px 24px;background:#4a90d9">'
            '<a href="/team/html" style="color:white;text-decoration:none;font-size:13px">'
            '&larr; Team Dashboard</a></div>'
        )
        return html.replace("<body>", "<body>" + nav)

    @app.post("/reports")
    async def receive_report(request: Request):
        """Accept a JSON report POSTed by `auto-sdlc logs --export-url`."""
        try:
            report = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        user_id = report.get("user_id", "unknown")
        safe_user = user_id.replace("@", "_at_").replace("/", "_")
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        filename = "{}_{}.json".format(safe_user, ts)
        dest = reports_path / filename
        dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        return {"saved": filename, "user_id": user_id}

    @app.get("/reports")
    def list_reports():
        """List all stored individual reports."""
        files = sorted(reports_path.glob("*.json"))
        reports = []
        for f in files:
            if f.name == "team_report.json":
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                reports.append({
                    "filename": f.name,
                    "user_id": data.get("user_id", f.stem),
                    "generated_at": data.get("generated_at"),
                    "total_sessions": data.get("summary", {}).get("total_sessions"),
                    "overall_maturity": data.get("maturity_scores", {}).get("overall_label"),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return {"count": len(reports), "reports": reports}

    @app.get("/team")
    def team_json():
        """Return the aggregated team report as JSON."""
        files = [f for f in sorted(reports_path.glob("*.json")) if f.name != "team_report.json"]
        if not files:
            raise HTTPException(status_code=404, detail="No reports found in reports_dir")
        user_reports = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                user_reports.append((data.get("user_id", f.stem), data))
            except (json.JSONDecodeError, OSError):
                continue
        report = build_team_report(user_reports)
        report["generated_at"] = datetime.now(tz=timezone.utc).isoformat()
        return JSONResponse(content=report)

    @app.get("/team/html", response_class=HTMLResponse)
    def team_html():
        """Return the aggregated team report as a rendered HTML page."""
        files = [f for f in sorted(reports_path.glob("*.json")) if f.name != "team_report.json"]
        if not files:
            raise HTTPException(status_code=404, detail="No reports found in reports_dir")
        user_reports = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                user_reports.append((data.get("user_id", f.stem), data))
            except (json.JSONDecodeError, OSError):
                continue
        report = build_team_report(user_reports)
        report["generated_at"] = datetime.now(tz=timezone.utc).isoformat()
        return render_team_html(report)

    return app
