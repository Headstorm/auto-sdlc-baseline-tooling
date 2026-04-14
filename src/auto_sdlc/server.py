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

    app = FastAPI(title="Auto-SDLC Collection Server")

    @app.get("/health")
    def health():
        return {"status": "ok", "reports_dir": str(reports_path)}

    @app.get("/", response_class=HTMLResponse)
    def landing_page():
        """Landing page - report generation UI with SSE progress bars."""
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
    .tabs {
      display: flex;
      border-bottom: 2px solid #e5e7eb;
      margin-bottom: 24px;
    }
    .tab-button {
      flex: 1;
      padding: 12px;
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      font-size: 14px;
      font-weight: 600;
      color: #666;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-button.active {
      color: #003366;
      border-bottom-color: #003366;
    }
    .tab-button:hover {
      color: #003366;
    }
    .card {
      background: white;
      border-radius: 10px;
      padding: 28px 32px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #444;
      margin: 16px 0 6px;
    }
    input[type=text], input[type=file], select {
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
    input[type=text]:focus, input[type=file]:focus, select:focus {
      border-color: #003366;
      background: white;
    }
    input[type=file] {
      padding: 8px;
    }
    .file-help {
      font-size: 12px;
      color: #666;
      margin-top: 4px;
    }
    #generate-btn, #upload-btn {
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
    .tab-content { display: none; }
    .tab-content.active { display: block; }
  </style>
</head>
<body>
  <header>
    <h1>AI Maturity Assessment Report</h1>
    <p>Generate a professional PDF report measuring your team&#39;s AI maturity across 12 dimensions.</p>
  </header>
  <div class="container">
    <div class="tabs">
      <button class="tab-button active" onclick="switchTab('project')">Project Path</button>
      <button class="tab-button" onclick="switchTab('logs')">Upload Logs</button>
    </div>

    <div class="card">
      <!-- Project Path Tab -->
      <div id="project" class="tab-content active">
        <div id="form-section">
          <label for="user-id">Team Name</label>
          <input type="text" id="user-id" placeholder="e.g. platform_team">
          <label for="project-path">Project Path</label>
          <input type="text" id="project-path" placeholder="/path/to/your/project">
          <label for="report-type">Report Type</label>
          <select id="report-type">
            <option value="team">Team Report (8&#8211;12 pages)</option>
            <option value="individual">Individual Report (4&#8211;6 pages)</option>
          </select>
          <button id="generate-btn" onclick="startGeneration()">Generate Report</button>
        </div>
      </div>

      <!-- Logs Upload Tab -->
      <div id="logs" class="tab-content">
        <div id="upload-form-section">
          <label for="logs-user-id">Developer Name</label>
          <input type="text" id="logs-user-id" placeholder="e.g. john.smith">
          <label for="logs-zip">Claude Code Logs (ZIP)</label>
          <input type="file" id="logs-zip" accept=".zip" required>
          <p class="file-help">Upload a ZIP of your ~/.claude directory or a project&#39;s logs folder</p>
          <button id="upload-btn" onclick="startLogsUpload()">Upload &amp; Generate Report</button>
        </div>
      </div>

      <!-- Progress Section (shared) -->
      <div id="progress-section" style="display:none">
        <div class="phase-block">
          <div class="phase-header">
            <span class="phase-name" id="phase-label-1">Phase 1: Extracting evidence</span>
            <span class="phase-pct" id="phase-pct-1">0%</span>
          </div>
          <div class="bar-track"><div class="bar-fill" id="bar-1"></div></div>
        </div>
        <div class="phase-block">
          <div class="phase-header">
            <span class="phase-name" id="phase-label-2">Phase 2: Scoring maturity</span>
            <span class="phase-pct" id="phase-pct-2">0%</span>
          </div>
          <div class="bar-track"><div class="bar-fill" id="bar-2"></div></div>
        </div>
        <div class="phase-block">
          <div class="phase-header">
            <span class="phase-name" id="phase-label-3">Phase 3: Building report</span>
            <span class="phase-pct" id="phase-pct-3">0%</span>
          </div>
          <div class="bar-track"><div class="bar-fill" id="bar-3"></div></div>
        </div>
        <div class="phase-block">
          <div class="phase-header">
            <span class="phase-name" id="phase-label-4">Phase 4: Rendering PDF</span>
            <span class="phase-pct" id="phase-pct-4">0%</span>
          </div>
          <div class="bar-track"><div class="bar-fill" id="bar-4"></div></div>
        </div>
        <div id="status-msg">Starting&#8230;</div>
      </div>

      <!-- Download Section (shared) -->
      <div id="download-section" style="display:none">
        <p>Report generated successfully!</p>
        <a id="download-link" href="#" download>Download PDF Report</a>
      </div>

      <!-- Error Section (shared) -->
      <div id="error-section" style="display:none">
        <p id="error-msg"></p>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tab) {
      // Hide all tabs
      document.getElementById('project').classList.remove('active');
      document.getElementById('logs').classList.remove('active');
      // Remove active class from all buttons
      document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
      // Show selected tab and mark button active
      document.getElementById(tab).classList.add('active');
      event.target.classList.add('active');
      // Reset progress
      resetProgress();
    }

    function resetProgress() {
      document.getElementById('progress-section').style.display = 'none';
      document.getElementById('download-section').style.display = 'none';
      document.getElementById('error-section').style.display = 'none';
      for (let i = 1; i <= 4; i++) {
        const bar = document.getElementById('bar-' + i);
        bar.style.width = '0%';
        bar.className = 'bar-fill';
        document.getElementById('phase-pct-' + i).textContent = '0%';
      }
      document.getElementById('status-msg').textContent = 'Starting\u2026';
    }

    async function startGeneration() {
      const userId = document.getElementById('user-id').value.trim();
      const projectPath = document.getElementById('project-path').value.trim();
      const reportType = document.getElementById('report-type').value;
      if (!userId) { alert('Please enter a Team Name.'); return; }
      if (!projectPath) { alert('Please enter a Project Path.'); return; }
      document.getElementById('generate-btn').disabled = true;
      resetProgress();
      document.getElementById('progress-section').style.display = 'block';
      await startSSEStream('/generate-report', {
        user_id: userId,
        project_path: projectPath,
        report_type: reportType
      });
      document.getElementById('generate-btn').disabled = false;
    }

    async function startLogsUpload() {
      const userId = document.getElementById('logs-user-id').value.trim();
      const logsFile = document.getElementById('logs-zip').files[0];
      if (!userId) { alert('Please enter a Developer Name.'); return; }
      if (!logsFile) { alert('Please select a logs ZIP file.'); return; }
      document.getElementById('upload-btn').disabled = true;
      resetProgress();
      document.getElementById('progress-section').style.display = 'block';

      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('logs_zip', logsFile);

      try {
        const resp = await fetch('/upload-logs', {
          method: 'POST',
          body: formData,
        });
        if (!resp.ok) {
          const errText = await resp.text();
          showError('Server error: ' + errText);
          return;
        }
        await handleSSEStream(resp);
      } catch (err) {
        showError('Connection error: ' + err.message);
      }
      document.getElementById('upload-btn').disabled = false;
    }

    async function startSSEStream(endpoint, body) {
      try {
        const resp = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!resp.ok) {
          const errText = await resp.text();
          showError('Server error: ' + errText);
          return;
        }
        await handleSSEStream(resp);
      } catch (err) {
        showError('Connection error: ' + err.message);
      }
    }

    async function handleSSEStream(resp) {
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let activePhase = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;
          const jsonStr = line.slice(5).trim();
          let msg;
          try { msg = JSON.parse(jsonStr); } catch { continue; }
          if (msg.error) { showError(msg.error); return; }
          if (msg.done) {
            for (let i = 1; i <= 4; i++) {
              const bar = document.getElementById('bar-' + i);
              bar.style.width = '100%';
              bar.className = 'bar-fill done';
              document.getElementById('phase-pct-' + i).textContent = '100%';
            }
            document.getElementById('status-msg').textContent = '';
            document.getElementById('download-link').href = msg.download_url;
            document.getElementById('download-section').style.display = 'block';
            return;
          }
          if (msg.phase !== undefined) {
            const phase = msg.phase;
            const pct = Math.round((msg.pct || 0) * 100);
            const bar = document.getElementById('bar-' + phase);
            const pctEl = document.getElementById('phase-pct-' + phase);
            if (msg.label) {
              document.getElementById('phase-label-' + phase).textContent = 'Phase ' + phase + ': ' + msg.label;
            }
            if (phase > activePhase) {
              if (activePhase > 0) {
                const prevBar = document.getElementById('bar-' + activePhase);
                prevBar.style.width = '100%';
                prevBar.className = 'bar-fill done';
                document.getElementById('phase-pct-' + activePhase).textContent = '100%';
              }
              activePhase = phase;
              bar.className = 'bar-fill active';
            }
            bar.style.width = pct + '%';
            pctEl.textContent = pct + '%';
            document.getElementById('status-msg').textContent = 'Phase ' + phase + ': ' + (msg.label || '') + ' \u2014 ' + pct + '%';
          }
        }
      }
    }

    function showError(msg) {
      document.getElementById('error-msg').textContent = msg;
      document.getElementById('error-section').style.display = 'block';
    }
  </script>
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

    @app.get("/download-report/{filename}")
    def download_report(filename: str):
        """Serve a generated PDF report for download."""
        pdf_path = (reports_path / filename).resolve()
        if not pdf_path.is_relative_to(reports_path.resolve()):
            raise HTTPException(status_code=400, detail="Invalid filename")
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
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

    return app
