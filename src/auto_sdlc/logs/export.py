import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


def export_report_to_dir(report, dest_dir):
    """Write report JSON to dest_dir as <user_id>_<timestamp>.json. Returns path string."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    user_id = report.get("user_id", "unknown")
    safe_user = user_id.replace("@", "_at_").replace("/", "_")
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    filename = "{}_{}.json".format(safe_user, ts)
    path = dest_dir / filename
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return str(path)


def export_report_to_http(report, url, timeout=10):
    """POST report JSON to url. Returns True on success, False on any error."""
    payload = json.dumps(report, default=str).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False
