"""Central collection server for auto-sdlc reports."""
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
except ImportError:
    raise ImportError("Server dependencies not installed. Run: pip install auto-sdlc[server]")

from auto_sdlc.logs.team import build_team_report, render_team_html


def create_app(reports_dir):
    """Create the FastAPI app, storing reports in reports_dir."""
    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Auto-SDLC Collection Server")

    @app.get("/health")
    def health():
        return {"status": "ok", "reports_dir": str(reports_path)}

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
