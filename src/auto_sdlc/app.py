"""ASGI app entry point for uvicorn."""
import os
from pathlib import Path
from auto_sdlc.server._app import create_app

# Create app instance with default reports directory
_reports_dir = os.environ.get("REPORTS_DIR") or str(Path.home() / ".auto-sdlc" / "server" / "reports")
app = create_app(_reports_dir)
