"""Central collection server for auto-sdlc reports."""
import asyncio
import json
import logging
import tempfile
import threading
import zipfile
from urllib.parse import quote
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("Server dependencies not installed. Run: pip install auto-sdlc[server]")

from auto_sdlc.logs.team import build_team_report, render_team_html
from auto_sdlc.reports.service import ReportService
from auto_sdlc.server.extractors import extract_logs_zip, create_project_structure
import shutil

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ReportRequest(BaseModel):
    """Request body for /api/report/generate endpoint."""
    user_id: str = Field(..., min_length=1, description="Team name or user identifier")
    project_path: str = Field(..., description="Path to project directory")
    report_type: str = Field(default="team", description="Report type: 'team' or 'individual'")
    assessment_responses: Optional[str] = Field(default=None, description="Optional path to assessment responses JSON")
    team_baseline: Optional[str] = Field(default=None, description="Optional path to team baseline scores JSON")


class ValidationResponse(BaseModel):
    """Response body for /api/report/validate endpoint."""
    valid: bool
    errors: list = Field(default_factory=list)
    warnings: list = Field(default_factory=list)
    data_sources: Dict[str, bool] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    """Response body for /api/report/status endpoint."""
    status: str = "ready"
    version: str = "1.0"
    capabilities: list = Field(default_factory=lambda: [
        "team_reports", "individual_reports", "assessment_integration"
    ])


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    details: Optional[str] = None


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

    # Initialize DB alongside reports directory
    from auto_sdlc.db import Database as _Database
    _db_path = str(reports_path.parent / "auto-sdlc.db")
    _db = _Database(_db_path)
    _db.init()

    app = FastAPI(title="Auto-SDLC Collection Server")

    @app.get("/health")
    def health():
        return {"status": "ok", "reports_dir": str(reports_path)}

    @app.get("/api/uploads")
    def api_uploads():
        """Return all uploads as JSON."""
        return _db.get_all_uploads()

    @app.get("/", response_class=HTMLResponse)
    def landing_page():
        """Landing page - unified report generation form."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Auto-SDLC &#8212; Generate AI Maturity Report</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f0f2f5;
      color: #222;
      min-height: 100vh;
    }
    header {
      background: #003366;
      color: white;
      padding: 20px 24px;
      text-align: center;
    }
    header h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
    header p { font-size: 13px; color: #a8c4e0; margin-top: 4px; }
    .container {
      max-width: 720px;
      margin: 32px auto;
      padding: 0 16px 48px;
    }
    .card {
      background: white;
      border-radius: 10px;
      padding: 28px 32px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    #form-section, #progress-section { transition: opacity 0.2s; }
    #form-section.hidden, #progress-section.hidden { display: none; }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #444;
      margin: 16px 0 6px;
    }
    input[type=text], input[type=file] {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #d0d5dd;
      border-radius: 6px;
      font-size: 14px;
      color: #222;
      background: #fafafa;
      transition: border-color 0.2s;
      outline: none;
      margin: 0;
      font-family: inherit;
    }
    input[type=text]:focus, input[type=file]:focus {
      border-color: #003366;
      background: white;
    }
    input[type=text].error {
      border-color: #dc2626;
      background: #fef2f2;
    }
    input[type=file] {
      padding: 8px;
    }
    .file-help, .helper-text {
      font-size: 12px;
      color: #666;
      margin-top: 4px;
    }
    .validation-msg {
      font-size: 12px;
      color: #dc2626;
      margin-top: 4px;
      display: none;
    }
    .validation-msg.show {
      display: block;
    }
    #submit-btn {
      margin-top: 22px;
      width: 100%;
      padding: 12px;
      background: #003366;
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    #generate-btn:hover:not(:disabled), #upload-btn:hover:not(:disabled) { background: #00509e; }
    #generate-btn:disabled, #upload-btn:disabled { background: #99aabb; cursor: not-allowed; }
    #progress-section { margin-top: 24px; }
    .phase-block { margin-bottom: 18px; }
    .phase-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .phase-name { font-size: 13px; font-weight: 600; color: #333; }
    .phase-pct { font-size: 12px; color: #666; min-width: 36px; text-align: right; }
    .bar-track {
      width: 100%;
      height: 10px;
      background: #e2e8f0;
      border-radius: 5px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      width: 0%;
      background: #3b82f6;
      border-radius: 5px;
      transition: width 0.35s ease, background-color 0.4s ease;
    }
    .bar-fill.done { background: #22c55e; }
    .bar-fill.active {
      background: linear-gradient(90deg, #3b82f6 60%, #60a5fa 100%);
      animation: pulse-bar 1.4s ease-in-out infinite;
    }
    @keyframes pulse-bar {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.75; }
    }
    #status-msg {
      text-align: center;
      font-size: 13px;
      color: #555;
      margin-top: 12px;
      min-height: 20px;
    }
    #download-section {
      text-align: center;
      margin-top: 28px;
      padding: 24px;
      border-top: 1px solid #e5e7eb;
    }
    #download-section p {
      font-size: 15px;
      font-weight: 600;
      color: #16a34a;
      margin-bottom: 16px;
    }
    #download-link {
      display: inline-block;
      padding: 12px 28px;
      background: #003366;
      color: white;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      transition: background 0.2s;
    }
    #download-link:hover { background: #00509e; }
    #error-section {
      margin-top: 20px;
      padding: 14px 16px;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 6px;
    }
    #error-msg { font-size: 13px; color: #b91c1c; }
    #submit-btn:hover:not(:disabled) { background: #00509e; }
    #submit-btn:disabled { background: #99aabb; cursor: not-allowed; }
  </style>
</head>
<body>
  <header>
    <h1>AI Maturity Assessment Report</h1>
    <p>Generate a professional PDF report measuring your team&#39;s AI maturity across 12 dimensions.</p>
  </header>
  <div class="container">
    <div class="card">
      <h2 style="margin-bottom: 20px; color: #333; font-size: 18px;">Generate a Report via CLI</h2>

      <p style="line-height: 1.6; margin-bottom: 16px; color: #555;">
        Use the <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">auto-sdlc report</code> command to generate an AI maturity assessment report from your Claude Code logs.
      </p>

      <h3 style="margin-top: 24px; margin-bottom: 12px; color: #333; font-size: 14px;">Basic Usage</h3>
      <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; border-left: 3px solid #003366; margin-bottom: 20px;"><code>auto-sdlc report ~/.claude/projects/myapp</code></pre>

      <h3 style="margin-top: 20px; margin-bottom: 12px; color: #333; font-size: 14px;">What to Provide</h3>
      <ul style="margin-left: 20px; margin-bottom: 20px; line-height: 1.8;">
        <li><strong>Logs directory:</strong> Path to a directory containing <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">.jsonl</code> files (e.g., <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">~/.claude/projects/myapp</code>)</li>
        <li><strong>Team name:</strong> Prompted interactively (e.g., <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">platform_team</code>)</li>
        <li><strong>User name:</strong> Prompted interactively (e.g., <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">john.smith</code>)</li>
      </ul>

      <h3 style="margin-top: 20px; margin-bottom: 12px; color: #333; font-size: 14px;">Examples</h3>
      <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; border-left: 3px solid #003366; margin-bottom: 16px;"><code style="font-size: 13px;"># Report from logs directory
auto-sdlc report ~/.claude/projects/myapp

# Report from logs ZIP file
auto-sdlc report ~/logs.zip

# Custom output directory
auto-sdlc report ~/.claude/projects/myapp --output-dir ~/my-reports</code></pre>

      <h3 style="margin-top: 20px; margin-bottom: 12px; color: #333; font-size: 14px;">Output</h3>
      <p style="line-height: 1.6; color: #555;">
        Reports are saved in <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">~/.auto-sdlc/server/reports/{team_name}/</code> and can be downloaded via the web interface.
      </p>
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
        # Extract just the report dicts (second element of tuples) for metrics calculation
        report_dicts = [r for _, r in user_reports]
        return render_team_html(report, report_dicts)

    # ========================================================================
    # SSE REPORT GENERATION ENDPOINTS
    # ========================================================================

    @app.post("/generate-report")
    async def generate_report_stream(request: Request):
        body = await request.json()
        user_id = body.get("user_id", "").strip()
        project_path = body.get("project_path", "").strip()
        report_type = body.get("report_type", "team")

        if not user_id or not project_path:
            raise HTTPException(status_code=400, detail="user_id and project_path required")

        if report_type not in ("team", "individual"):
            raise HTTPException(status_code=400, detail="report_type must be 'team' or 'individual'")

        loop = asyncio.get_event_loop()
        aq = asyncio.Queue()

        def callback(phase, label, pct):
            loop.call_soon_threadsafe(aq.put_nowait, {"phase": phase, "label": label, "pct": pct})

        def run_pipeline():
            try:
                service = ReportService()
                _, pdf_path = service.generate_report(
                    user_id=user_id,
                    project_path=project_path,
                    report_type=report_type,
                    output_dir=str(reports_path),
                    progress_callback=callback,
                )
                loop.call_soon_threadsafe(
                    aq.put_nowait,
                    {"done": True, "download_url": f"/download-report/{pdf_path.name}"}
                )
            except Exception as e:
                logger.exception(f"Report generation error: {e}")
                loop.call_soon_threadsafe(aq.put_nowait, {"error": str(e)})

        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

        async def event_stream():
            while True:
                try:
                    msg = await asyncio.wait_for(aq.get(), timeout=300)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'error': 'Generation timed out'})}\n\n"
                    break
                yield f"data: {json.dumps(msg)}\n\n"
                if "done" in msg or "error" in msg:
                    break

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/download-report/{file_path:path}")
    def download_report(file_path: str):
        """Serve a generated PDF report for download."""
        pdf_path = (reports_path / file_path).resolve()
        if not pdf_path.is_relative_to(reports_path.resolve()):
            raise HTTPException(status_code=400, detail="Invalid file path")
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_path.split('/')[-1])}"},
        )

    @app.post("/upload-logs")
    async def upload_logs(user_id: str = Form(...), logs_zip: UploadFile = File(...)):
        """
        Upload Claude Code logs ZIP and generate report.

        Returns SSE stream with progress updates.
        """
        # Validate user_id
        user_id = user_id.strip()
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")

        if not (logs_zip.filename or "").endswith(".zip"):
            raise HTTPException(status_code=400, detail="File must be a .zip archive")

        # Read ZIP bytes
        zip_bytes = await logs_zip.read()

        # Extract to temp directory
        try:
            temp_root, logs_dir = extract_logs_zip(zip_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"ZIP extraction error: {e}")
            raise HTTPException(status_code=400, detail="Failed to extract logs")

        # Create project structure
        try:
            project_path = create_project_structure(logs_dir, temp_root)
        except Exception as e:
            logger.error(f"Project structure error: {e}")
            shutil.rmtree(temp_root, ignore_errors=True)
            raise HTTPException(status_code=500, detail="Failed to prepare project")

        # Generate report via SSE
        loop = asyncio.get_event_loop()
        aq = asyncio.Queue()

        def callback(phase, label, pct):
            loop.call_soon_threadsafe(aq.put_nowait, {"phase": phase, "label": label, "pct": pct})

        def run_pipeline():
            try:
                service = ReportService()
                _, pdf_path = service.generate_report(
                    user_id=user_id,
                    project_path=str(project_path),
                    report_type="individual",  # Logs upload → individual reports
                    output_dir=str(reports_path),
                    progress_callback=callback,
                )
                loop.call_soon_threadsafe(
                    aq.put_nowait,
                    {"done": True, "download_url": f"/download-report/{pdf_path.name}"}
                )
            except Exception as e:
                logger.exception(f"Report generation error: {e}")
                loop.call_soon_threadsafe(aq.put_nowait, {"error": str(e)})
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_root, ignore_errors=True)

        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

        async def event_stream():
            while True:
                try:
                    msg = await asyncio.wait_for(aq.get(), timeout=600)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'error': 'Generation timed out'})}\n\n"
                    break
                yield f"data: {json.dumps(msg)}\n\n"
                if "done" in msg or "error" in msg:
                    break

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/generate-individual-report")
    async def generate_individual_report(
        team_name: str = Form(...),
        user_name: str = Form(...),
        logs_zip: UploadFile = File(...),
    ):
        """
        Generate an individual report from Claude Code logs ZIP.

        Form fields:
        - team_name: Name of the team (required, used for report organization)
        - user_name: Name of the user being assessed (required)
        - logs_zip: ZIP file of Claude Code logs (required)

        Returns SSE stream with progress updates and final download URL.
        """
        # Validate inputs
        team_name = (team_name or "").strip()
        user_name = (user_name or "").strip()

        if not team_name:
            raise HTTPException(status_code=400, detail="team_name is required")
        if not user_name:
            raise HTTPException(status_code=400, detail="user_name is required")

        if not (logs_zip.filename or "").endswith(".zip"):
            raise HTTPException(status_code=400, detail="File must be a .zip archive")

        # Extract logs and create project structure
        temp_root = None
        project_input_path = None

        try:
            temp_root = Path(tempfile.mkdtemp(prefix="auto_sdlc_logs_"))
            zip_bytes = await logs_zip.read()
            try:
                temp_path, logs_dir = extract_logs_zip(zip_bytes)
                project_input_path = str(create_project_structure(logs_dir, temp_path))
                # Update temp_root to point to the extracted root
                temp_root = temp_path
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Create team-scoped output directory
            team_output_dir = reports_path / team_name
            team_output_dir.mkdir(parents=True, exist_ok=True)

            # Generate report via SSE
            loop = asyncio.get_event_loop()
            aq = asyncio.Queue()

            def callback(phase, label, pct):
                loop.call_soon_threadsafe(aq.put_nowait, {"phase": phase, "label": label, "pct": pct})

            def run_pipeline():
                try:
                    service = ReportService()
                    report_obj, pdf_path = service.generate_report(
                        user_id=user_name,
                        project_path=project_input_path,
                        report_type="individual",
                        output_dir=str(team_output_dir),
                        progress_callback=callback,
                    )
                    # Build download URL with team scope
                    download_path = f"{team_name}/{pdf_path.name}"
                    loop.call_soon_threadsafe(
                        aq.put_nowait,
                        {"done": True, "download_url": f"/download-report/{download_path}"}
                    )
                except Exception as e:
                    logger.exception(f"Report generation error: {e}")
                    loop.call_soon_threadsafe(aq.put_nowait, {"error": str(e)})
                finally:
                    # Clean up temp directory if created
                    if temp_root and temp_root.exists():
                        shutil.rmtree(str(temp_root), ignore_errors=True)

            thread = threading.Thread(target=run_pipeline, daemon=True)
            thread.start()

            async def event_stream():
                while True:
                    try:
                        msg = await asyncio.wait_for(aq.get(), timeout=600)
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'error': 'Generation timed out'})}\n\n"
                        break
                    yield f"data: {json.dumps(msg)}\n\n"
                    if "done" in msg or "error" in msg:
                        break

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        except HTTPException:
            # Clean up on validation error
            if temp_root and temp_root.exists():
                shutil.rmtree(str(temp_root), ignore_errors=True)
            raise
        except Exception as e:
            # Clean up on unexpected error
            if temp_root and temp_root.exists():
                shutil.rmtree(str(temp_root), ignore_errors=True)
            logger.exception(f"Unexpected error in generate_individual_report: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    # ========================================================================
    # REPORT GENERATION API ENDPOINTS
    # ========================================================================

    @app.get("/api/report/status")
    def report_status():
        """
        Check server health and report generation status.

        Returns server version, capabilities, and status information.
        """
        return StatusResponse()

    @app.post("/api/report/validate")
    def validate_report(request: ReportRequest):
        """
        Validate report generation inputs without generating a report.

        Checks project path existence, report type validity, and file readability.

        Returns validation results with data sources found.
        """
        errors = []
        warnings = []
        data_sources = {"logs": False, "configs": False, "capabilities": False}

        # Validate user_id
        if not request.user_id or not request.user_id.strip():
            errors.append("user_id must be a non-empty string")

        # Validate report_type
        if request.report_type not in ("team", "individual"):
            errors.append(f"report_type must be 'team' or 'individual', got '{request.report_type}'")

        # Validate project_path
        project_path = Path(request.project_path)
        if not project_path.exists():
            errors.append(f"project_path does not exist: {request.project_path}")
        elif not project_path.is_dir():
            errors.append(f"project_path must be a directory: {request.project_path}")
        else:
            # Check for data sources
            if (project_path / "logs").exists():
                data_sources["logs"] = True
            if (project_path / "CLAUDE.md").exists() or (project_path / "AGENTS.md").exists():
                data_sources["configs"] = True
            # capabilities check would require more detailed scanning
            data_sources["capabilities"] = False

        # Validate assessment_responses if provided
        if request.assessment_responses:
            resp_path = Path(request.assessment_responses)
            if not resp_path.exists():
                errors.append(f"assessment_responses file not found: {request.assessment_responses}")
            else:
                try:
                    with open(resp_path) as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    errors.append(f"assessment_responses is not valid JSON: {e}")

        # Validate team_baseline if provided
        if request.team_baseline:
            baseline_path = Path(request.team_baseline)
            if not baseline_path.exists():
                errors.append(f"team_baseline file not found: {request.team_baseline}")
            else:
                try:
                    with open(baseline_path) as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    errors.append(f"team_baseline is not valid JSON: {e}")

        # Check if required data sources exist (warning only)
        if not data_sources["logs"] and not data_sources["configs"]:
            warnings.append("No logs or config files found. Report may be incomplete.")

        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_sources=data_sources,
        )

    @app.post("/api/report/generate")
    def generate_report(request: ReportRequest):
        """
        Generate and return a report as PDF.

        Accepts user_id, project_path, report_type, and optional assessment data.
        Returns a PDF file with appropriate headers.

        Raises:
            400: Invalid request (missing fields, invalid path, etc.)
            413: Payload too large (assessment responses > 1MB)
            500: Server error during PDF generation
        """
        try:
            # Validate inputs first
            if not request.user_id or not request.user_id.strip():
                raise HTTPException(
                    status_code=400,
                    detail="user_id is required and must be non-empty"
                )

            if request.report_type not in ("team", "individual"):
                raise HTTPException(
                    status_code=400,
                    detail=f"report_type must be 'team' or 'individual', got '{request.report_type}'"
                )

            project_path = Path(request.project_path)
            if not project_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"project_path does not exist: {request.project_path}"
                )

            if not project_path.is_dir():
                raise HTTPException(
                    status_code=400,
                    detail=f"project_path must be a directory: {request.project_path}"
                )

            # Log the request
            logger.info(
                f"Generating {request.report_type} report for user_id={request.user_id}, "
                f"project_path={request.project_path}"
            )

            # Generate report using service
            service = ReportService()
            report_obj, pdf_path = service.generate_report(
                user_id=request.user_id,
                project_path=str(project_path),
                report_type=request.report_type,
                assessment_responses=request.assessment_responses,
                team_baseline=request.team_baseline,
                output_dir=str(reports_path),
            )

            # Read PDF bytes
            pdf_bytes = pdf_path.read_bytes()

            # Generate filename for response
            safe_user = request.user_id.replace("@", "_at_").replace("/", "_")
            today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            filename = f"{safe_user}_report_{today}.pdf"

            logger.info(f"Report generated successfully: {pdf_path}")

            # Return PDF with appropriate headers
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        except HTTPException:
            raise
        except FileNotFoundError as e:
            logger.error(f"File not found error: {e}")
            raise HTTPException(status_code=400, detail=f"Required file not found: {e}")
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during report generation: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Server error during report generation: {str(e)}"
            )

    @app.get("/uploads", response_class=HTMLResponse)
    def uploads_dashboard():
        """Dashboard showing all uploads grouped by team."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Uploads Dashboard &#8212; Auto-SDLC</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f0f2f5;
      color: #222;
      min-height: 100vh;
    }
    header {
      background: #003366;
      color: white;
      padding: 20px 24px;
      text-align: center;
    }
    header h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
    header p { font-size: 13px; color: #a8c4e0; margin-top: 4px; }
    .container {
      max-width: 1200px;
      margin: 32px auto;
      padding: 0 16px 48px;
    }
    .card {
      background: white;
      border-radius: 10px;
      padding: 28px 32px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 24px;
    }
    h2 {
      font-size: 18px;
      font-weight: 700;
      color: #003366;
      margin-bottom: 20px;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 12px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 16px;
    }
    th {
      background: #f3f4f6;
      padding: 12px;
      text-align: left;
      font-size: 13px;
      font-weight: 600;
      color: #374151;
      border-bottom: 1px solid #d1d5db;
    }
    td {
      padding: 12px;
      border-bottom: 1px solid #e5e7eb;
      font-size: 14px;
    }
    tr:last-child td {
      border-bottom: none;
    }
    tr:hover {
      background: #f9fafb;
    }
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .status-pending {
      background: #fef3c7;
      color: #92400e;
    }
    .status-reported {
      background: #d1fae5;
      color: #065f46;
    }
    .generate-btn {
      background: #059669;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .generate-btn:hover {
      background: #047857;
    }
    .generate-btn:disabled {
      background: #d1d5db;
      cursor: not-allowed;
    }
    .status-msg {
      padding: 12px 16px;
      border-radius: 6px;
      margin-top: 12px;
      font-size: 13px;
      display: none;
    }
    .status-msg.show {
      display: block;
    }
    .status-msg.success {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #6ee7b7;
    }
    .status-msg.error {
      background: #fee2e2;
      color: #7f1d1d;
      border: 1px solid #fca5a5;
    }
    .empty-state {
      text-align: center;
      padding: 48px 24px;
      color: #666;
    }
    .empty-state p {
      margin-bottom: 16px;
      font-size: 15px;
    }
  </style>
</head>
<body>
  <header>
    <h1>Uploads Dashboard</h1>
    <p>Manage and process uploaded log archives by team</p>
  </header>
  <div class="container">
    <div id="uploads-container"></div>
  </div>

  <script>
    async function loadUploads() {
      try {
        const response = await fetch('/api/uploads');
        const uploads = await response.json();

        if (!uploads || uploads.length === 0) {
          displayEmptyState();
          return;
        }

        // Group uploads by team
        const byTeam = {};
        for (const upload of uploads) {
          const team = upload.team_name || 'Unassigned';
          if (!byTeam[team]) {
            byTeam[team] = [];
          }
          byTeam[team].push(upload);
        }

        // Render each team's uploads
        const container = document.getElementById('uploads-container');
        container.innerHTML = '';
        for (const [team, teamUploads] of Object.entries(byTeam)) {
          container.appendChild(createTeamSection(team, teamUploads));
        }
      } catch (error) {
        console.error('Failed to load uploads:', error);
        displayEmptyState('Error loading uploads');
      }
    }

    function createTeamSection(team, uploads) {
      const card = document.createElement('div');
      card.className = 'card';

      const title = document.createElement('h2');
      title.textContent = team;
      card.appendChild(title);

      const table = document.createElement('table');
      const thead = document.createElement('thead');
      thead.innerHTML = `
        <tr>
          <th>User</th>
          <th>Uploaded</th>
          <th>Sessions</th>
          <th>Tokens</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      `;
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      for (const upload of uploads) {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${escapeHtml(upload.user_name || 'Unknown')}</td>
          <td>${formatDate(upload.uploaded_at)}</td>
          <td>${upload.session_count || 0}</td>
          <td>${formatTokens(upload.total_tokens || 0)}</td>
          <td>
            <span class="status-badge status-${upload.status || 'pending'}">
              ${upload.status || 'pending'}
            </span>
          </td>
          <td>
            ${upload.status === 'pending'
              ? `<button class="generate-btn" onclick="generateReport(${upload.id})">Generate Report</button>`
              : '<span style="color: #999; font-size: 12px;">—</span>'
            }
          </td>
        `;
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      card.appendChild(table);

      return card;
    }

    function displayEmptyState(message = 'No uploads yet') {
      const container = document.getElementById('uploads-container');
      container.innerHTML = `
        <div class="card">
          <div class="empty-state">
            <p>${escapeHtml(message)}</p>
            <p style="font-size: 13px; color: #999;">Use the CLI or web interface to upload log archives.</p>
          </div>
        </div>
      `;
    }

    async function generateReport(uploadId) {
      const btn = event.target;
      btn.disabled = true;
      btn.textContent = 'Generating...';

      try {
        const response = await fetch('/api/report/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ upload_id: uploadId })
        });

        if (response.ok) {
          showStatus('Report generated successfully!', 'success');
          setTimeout(() => loadUploads(), 1000);
        } else {
          const error = await response.json();
          showStatus(`Error: ${error.detail || 'Failed to generate report'}`, 'error');
          btn.disabled = false;
          btn.textContent = 'Generate Report';
        }
      } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        btn.disabled = false;
        btn.textContent = 'Generate Report';
      }
    }

    function showStatus(message, type) {
      const container = document.getElementById('uploads-container');
      const msg = document.createElement('div');
      msg.className = `status-msg ${type} show`;
      msg.textContent = message;
      container.insertBefore(msg, container.firstChild);
      setTimeout(() => msg.remove(), 5000);
    }

    function formatDate(isoString) {
      if (!isoString) return '—';
      try {
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      } catch {
        return isoString;
      }
    }

    function formatTokens(tokens) {
      if (tokens < 1000) return tokens.toString();
      if (tokens < 1000000) return (tokens / 1000).toFixed(1) + 'K';
      return (tokens / 1000000).toFixed(1) + 'M';
    }

    function escapeHtml(text) {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Load uploads on page load
    loadUploads();
    // Refresh every 10 seconds
    setInterval(loadUploads, 10000);
  </script>
</body>
</html>"""

    return app
