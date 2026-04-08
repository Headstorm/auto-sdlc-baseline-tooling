# Phase 2: Server-Side Log Upload & Processing

## Context

**Problem**: The current server (`auto-sdlc serve`) only accepts pre-processed JSON reports — meaning each developer must still run `auto-sdlc logs` locally before the server is useful. The user wants a central application where developers submit their raw Claude Code logs and the server handles all analysis. No CLI usage required from the developer's side.

**Goal**: Developers visit a URL in their browser, upload a ZIP of their `~/.claude/projects/` folder, and immediately see their maturity report. The team dashboard auto-updates.

**What changes**: `server.py` gets 3 new endpoints. Existing endpoints (`POST /reports`, `GET /team`, `GET /team/html`) stay untouched.

---

## User Experience After This Change

```
1. Developer opens browser: http://your-server:8000/
   └─ Sees upload form: "Enter your email" + "Upload your Claude logs (ZIP)"

2. Developer zips their ~/.claude/projects/ folder and uploads it.

3. Server:
   ├─ Extracts ZIP to temp dir
   ├─ Runs build_report() (same pipeline as auto-sdlc logs)
   ├─ Saves resulting JSON report
   └─ Redirects developer to their personal dashboard

4. Developer sees: http://your-server:8000/dashboard/alice_at_company_com
   └─ Their individual HTML report + link to team view

5. Team lead opens: http://your-server:8000/team/html
   └─ All submitted users aggregated into live team dashboard
```

---

## Files Changed

| File | Action |
|------|--------|
| `src/auto_sdlc/server.py` | Add 3 endpoints: `GET /`, `POST /upload`, `GET /dashboard/{user_id}` |
| `pyproject.toml` | Add `python-multipart>=0.0.9` to `[server]` extras |
| `tests/test_server.py` | Add 5 upload/dashboard test cases |

**No changes** to: cli.py, ingest.py, report.py, team.py, or any other analysis modules.

---

## New Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Upload form (HTML page, no CLI needed) |
| `/upload` | POST | Receive ZIP, run analysis server-side, save report, redirect |
| `/dashboard/{user_id}` | GET | Individual HTML report for a user |
| `/reports` | POST | *(existing)* Receive pre-processed JSON report |
| `/reports` | GET | *(existing)* List all reports |
| `/team` | GET | *(existing)* Team JSON |
| `/team/html` | GET | *(existing)* Team HTML dashboard |

---

## Implementation Details

### Step 1: `pyproject.toml` — Add `python-multipart`

FastAPI requires this to handle file uploads (`UploadFile`).

```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "python-multipart>=0.0.9",
]
```

---

### Step 2: `GET /` — Upload Form

Plain HTML page, no framework. Developers see: email field + file picker + submit button.

```python
@app.get("/", response_class=HTMLResponse)
def upload_form():
    return """<!DOCTYPE html>
    <html>
    ...
    <form action="/upload" method="post" enctype="multipart/form-data">
      <input type="email" name="user_id" placeholder="you@company.com" required>
      <input type="file" name="logs_zip" accept=".zip" required>
      <button type="submit">Upload & Analyze</button>
    </form>
    ...
    </html>"""
```

---

### Step 3: `POST /upload` — Core Endpoint

1. Validates file is a ZIP
2. Extracts to temp directory
3. Calls `build_report(extracted_dir, user_id)` from `report.py:65`
4. Saves JSON to `reports_dir`
5. Redirects to `/dashboard/<safe_user_id>`

```python
@app.post("/upload")
async def upload_logs(user_id: str = Form(...), logs_zip: UploadFile = File(...)):
    if not logs_zip.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "upload.zip"
        zip_path.write_bytes(await logs_zip.read())
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmpdir)
        projects_dir = _find_projects_dir(Path(tmpdir))
        report = build_report(projects_dir=projects_dir, user_id=user_id)

    safe_user = user_id.replace("@", "_at_").replace("/", "_")
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    dest = reports_path / "{}_{}.json".format(safe_user, ts)
    dest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return RedirectResponse(url="/dashboard/{}".format(safe_user), status_code=303)
```

**Helper `_find_projects_dir(root)`** — handles 3 zip layouts:
- `zip ~/.claude/` → extracts with `.claude/projects/` subpath
- `zip ~/.claude/projects/` → extracts with `projects/` subpath  
- `zip contents of projects/` → JSONL files directly in extracted root

Finds any directory containing `.jsonl` files (depth-first).

---

### Step 4: `GET /dashboard/{user_id}` — Individual Dashboard

Loads most recent JSON report for the user, renders with existing `render_individual_html()`, injects a team dashboard link.

```python
@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def user_dashboard(user_id: str):
    matches = sorted(reports_path.glob("{}_*.json".format(user_id)))
    if not matches:
        raise HTTPException(status_code=404, detail="No report found for {}".format(user_id))
    report = json.loads(matches[-1].read_text(encoding="utf-8"))
    html = render_individual_html(report)
    return html.replace("<body>", '<body><a href="/team/html">← Team Dashboard</a>')
```

---

## ZIP File Layouts Supported

```bash
# Option 1: Zip .claude/projects/ directly (recommended — clearest)
cd ~/.claude && zip -r ~/projects.zip projects/

# Option 2: Zip from home dir (includes .claude/ prefix)
cd ~ && zip -r ~/projects.zip .claude/projects/

# Option 3: Zip contents of projects/ 
cd ~/.claude/projects && zip -r ~/projects.zip .
```

`_find_projects_dir()` handles all three automatically.

---

## Execution Order

1. Update `pyproject.toml`
2. Add `_find_projects_dir()` helper + 3 endpoints to `server.py`
3. Add 5 tests to `test_server.py`
4. `pytest tests/test_server.py -v`
5. Manual smoke test: zip real logs → upload via browser
6. Commit + push

---

## Verification

```bash
# Install updated deps
pip install -e ".[server]"

# Start server
auto-sdlc serve --port 8000

# Visit upload form in browser
open http://localhost:8000/

# Or via curl
cd ~/.claude && zip -r /tmp/my-logs.zip projects/
curl -X POST http://localhost:8000/upload \
  -F "user_id=you@company.com" \
  -F "logs_zip=@/tmp/my-logs.zip"

# View results
open http://localhost:8000/team/html
```
