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

    # Initialize DB at ~/.auto-sdlc/auto_sdlc.db (same as CLI)
    from auto_sdlc.db import Database as _Database
    _db_path = str(Path.home() / ".auto-sdlc" / "auto_sdlc.db")
    _db = _Database(_db_path)
    _db.init()

    app = FastAPI(title="Auto-SDLC Collection Server")

    @app.get("/health")
    def health():
        return {"status": "ok", "reports_dir": str(reports_path)}


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

    @app.post("/uploads/{upload_id}/generate")
    async def generate_from_upload(upload_id: int):
        """Generate a report from a previously uploaded log set."""
        import tempfile
        import shutil

        upload = _db.get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        if upload["status"] == "reported":
            raise HTTPException(status_code=400, detail="Report already generated for this upload")

        logs_path = upload["logs_path"]
        if not Path(logs_path).exists():
            raise HTTPException(status_code=400, detail=f"Logs directory not found: {logs_path}")

        team_name = upload["team_name"]
        user_name = upload["user_name"]
        team_output_dir = reports_path / team_name
        team_output_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary project structure for report generation
        temp_root = Path(tempfile.mkdtemp(prefix="auto_sdlc_generate_"))
        try:
            project_path = str(create_project_structure(Path(logs_path), temp_root))

            service = ReportService()
            report_obj, pdf_path = service.generate_report(
                user_id=user_name,
                project_path=project_path,
                report_type="individual",
                output_dir=str(team_output_dir),
            )
        except Exception as e:
            logger.exception(f"Report generation failed for upload {upload_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Clean up temporary directory
            if temp_root.exists():
                shutil.rmtree(str(temp_root), ignore_errors=True)

        # Record in DB
        maturity = getattr(report_obj, "overall_maturity_level", None)
        _db.insert_report(
            upload_id=upload_id,
            team_name=team_name,
            user_name=user_name,
            report_type="individual",
            pdf_path=str(pdf_path),
            overall_maturity_level=maturity,
        )

        download_path = f"{team_name}/{pdf_path.name}"
        return {"download_url": f"/download-report/{download_path}"}

    return app
