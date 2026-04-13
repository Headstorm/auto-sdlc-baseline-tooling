"""Central collection server for auto-sdlc reports."""
import json
import logging
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("Server dependencies not installed. Run: pip install auto-sdlc[server]")

from auto_sdlc.logs.team import build_team_report, render_team_html
from auto_sdlc.reports.pipeline import ReportGenerationPipeline

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
    sample_command: str = "auto-sdlc report --user-id test --project-path /path"


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
    def upload_form(request: Request):
        """Landing page — CLI-first, upload as fallback."""
        # Inject the actual server URL into the command
        server_url = "{}://{}".format(request.url.scheme, request.url.netloc)
        export_url = "{}/reports".format(server_url)

        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Auto-SDLC — Developer Log Analysis</title>
  <style>
    *{{margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;color:#222}}
    .container{{max-width:600px;margin:0 auto;padding:40px 24px}}
    h1{{font-size:24px;margin-bottom:8px}}
    .subtitle{{font-size:14px;color:#666;margin-bottom:32px}}
    .section{{background:white;border-radius:8px;padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
    .step{{margin-bottom:16px}}
    .step-num{{display:inline-block;background:#4a90d9;color:white;width:24px;height:24px;border-radius:50%;text-align:center;line-height:24px;margin-right:8px;font-size:13px;font-weight:600}}
    .step-title{{font-weight:600;margin-bottom:8px}}
    .code-block{{background:#f5f5f5;border-left:3px solid #4a90d9;padding:12px;border-radius:4px;font-family:monospace;font-size:12px;overflow-x:auto;margin:8px 0}}
    .code-block code{{color:#333}}
    .copy-btn{{background:#4a90d9;color:white;border:none;padding:6px 12px;border-radius:4px;font-size:12px;cursor:pointer;margin-left:8px}}
    .copy-btn:hover{{background:#357abd}}
    button{{margin-top:12px;padding:10px 16px;background:#4a90d9;color:white;border:none;border-radius:4px;cursor:pointer;font-size:14px}}
    button:hover{{background:#357abd}}
    .advanced{{margin-top:20px;border-top:1px solid #eee;padding-top:20px}}
    .toggle{{cursor:pointer;user-select:none;color:#4a90d9}}
    .toggle:hover{{text-decoration:underline}}
    #upload-form{{display:none;margin-top:16px}}
    label{{display:block;font-size:13px;font-weight:600;color:#444;margin:12px 0 6px 0}}
    input[type=email],input[type=file]{{width:100%;box-sizing:border-box;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:13px}}
    .info{{background:#e8f4f8;border-left:3px solid #4a90d9;padding:12px;border-radius:4px;margin:12px 0;font-size:13px}}
    a{{color:#4a90d9;text-decoration:none}}
    a:hover{{text-decoration:underline}}
  </style>
</head>
<body>
  <div class="container">
    <h1>Auto-SDLC Log Analysis</h1>
    <p class="subtitle">Submit your Claude Code session logs and see your maturity report</p>

    <div class="section">
      <div class="step">
        <span class="step-num">1</span>
        <div class="step-title">Install the CLI (if needed)</div>
        <div class="code-block"><code>pip install auto-sdlc</code></div>
      </div>

      <div class="step">
        <span class="step-num">2</span>
        <div class="step-title">Submit your logs (one-time)</div>
        <div class="code-block"><code>auto-sdlc logs \\<br>&nbsp;&nbsp;--user-id you@company.com \\<br>&nbsp;&nbsp;--export-url {export_url}</code></div>
        <button class="copy-btn" onclick="copyCommand()">Copy Command</button>
        <div class="info">
          This command reads your <code>~/.claude/projects/</code> and sends your session logs to this server.
        </div>
      </div>
    </div>

    <div class="section">
      <div class="advanced">
        <div class="toggle" onclick="toggleUpload()">
          ▶ Advanced: Upload ZIP manually
        </div>
        <form id="upload-form" action="/upload" method="post" enctype="multipart/form-data">
          <label>Your email address</label>
          <input type="email" name="user_id" placeholder="you@company.com" required>
          <label>Claude logs ZIP file</label>
          <input type="file" name="logs_zip" accept=".zip" required>
          <button type="submit">Upload &amp; Analyze</button>
          <div class="info" style="margin-top:12px">
            Create ZIP: <code>cd ~/.claude && zip -r ~/claude-logs.zip projects/</code>
          </div>
        </form>
      </div>
    </div>

    <div class="section" style="text-align:center;background:#f9f9f9">
      <p style="font-size:13px;color:#666">
        After submission, view your report or<br><a href="/team/html">see the team dashboard →</a>
      </p>
    </div>
  </div>

  <script>
    function copyCommand() {{
      const cmd = `auto-sdlc logs --user-id you@company.com --export-url {export_url}`;
      navigator.clipboard.writeText(cmd).then(() => {{
        alert('Command copied to clipboard!');
      }}).catch(() => {{
        alert('Could not copy. Please copy manually.');
      }});
    }}
    function toggleUpload() {{
      const form = document.getElementById('upload-form');
      const toggle = event.target;
      if (form.style.display === 'none') {{
        form.style.display = 'block';
        toggle.textContent = '▼ Advanced: Upload ZIP manually';
      }} else {{
        form.style.display = 'none';
        toggle.textContent = '▶ Advanced: Upload ZIP manually';
      }}
    }}
  </script>
</body>
</html>""".format(export_url=export_url)

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
    # REPORT GENERATION API ENDPOINTS
    # ========================================================================

    @app.get("/api/report/status")
    def report_status():
        """
        Check server health and report generation status.

        Returns capabilities and server version information.
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

            # Generate report using pipeline
            pipeline = ReportGenerationPipeline()
            report_obj, pdf_path = pipeline.generate_report(
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
