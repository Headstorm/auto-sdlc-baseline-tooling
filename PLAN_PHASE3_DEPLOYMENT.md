# Phase 3: Railway Deployment + CLI Submit + Auto-Sync Hook

## Context

Phase 2 built the server with a ZIP upload form. After discussion:
- **File upload is deprioritized** — users prefer CLI submit
- **Server UI should recommend the CLI command**, not the upload form
- **Deployment target**: Railway (cheap, simple, HTTPS out of box)
- **Long-term auto-sync**: Claude Code Stop hook (not a background daemon — event-driven)

---

## Part A: Railway Deployment

### What Railway Does
Connects to the GitHub repo, auto-deploys on push, provides HTTPS URL.
No infrastructure management needed.

### Steps

1. **Add `Procfile`** — tells Railway how to start the server:
   ```
   web: auto-sdlc serve --host 0.0.0.0 --port $PORT
   ```

2. **Add `runtime.txt`** (optional, pins Python version):
   ```
   python-3.11.0
   ```

3. **Create `railway.json`** (optional, explicit config):
   ```json
   {
     "build": { "builder": "NIXPACKS" },
     "deploy": { "startCommand": "auto-sdlc serve --host 0.0.0.0 --port $PORT" }
   }
   ```

4. **Deploy**:
   - Go to railway.app → New Project → Deploy from GitHub
   - Select `Headstorm/auto-sdlc-baseline-tooling`
   - Set env var: `REPORTS_DIR=/data/reports` (or use Railway's volume)
   - Done. App lives at `https://auto-sdlc-production.up.railway.app/`

5. **Persistent storage** (important): Railway containers are ephemeral — reports saved
   to disk disappear on redeploy. Options:
   - Add a Railway Volume (persistent disk, ~$0.25/GB/month)
   - Or: store reports in SQLite on volume (future Task 12)

### Files Changed
| File | Action |
|------|--------|
| `Procfile` | New — Railway start command |
| `src/auto_sdlc/cli.py` | Read `$PORT` env var in `serve` command |

---

## Part B: Update Server UI — CLI Over Upload

The landing page (`GET /`) should **recommend the CLI command** as the primary
path, not the ZIP upload. File upload stays as a fallback.

### Updated `GET /` page
- Primary section: "Recommended — run this command:"
  ```bash
  auto-sdlc logs --user-id you@company.com \
                 --export-url https://your-app.railway.app/reports
  ```
- Secondary section: "Or upload manually (advanced)" — collapsed by default

### Files Changed
| File | Action |
|------|--------|
| `src/auto_sdlc/server.py` | Update `GET /` HTML — CLI first, upload secondary |

---

## Part C: Auto-Sync Hook (Zero Ongoing Effort)

### What It Is

Claude Code has a built-in **Stop hook** — a shell command that fires every time
a session ends. We wire `auto-sdlc logs --export-url` into that hook.

Once installed, every Claude session auto-syncs to the server. Developer never
runs another command.

### How It Works

```
Developer finishes a Claude Code session
        ↓
Claude Code reads ~/.claude/settings.json
        ↓
Fires the Stop hook command:
  auto-sdlc logs --user-id alice@company.com
                 --export-url https://app.railway.app/reports
        ↓
Server receives report, dashboard updates
```

### What Gets Written to `~/.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "auto-sdlc logs --user-id alice@company.com --export-url https://app.railway.app/reports 2>/dev/null"
      }]
    }]
  }
}
```

### Developer Setup (One Time Only)

```bash
auto-sdlc install-hook --user-id alice@company.com \
                       --url https://your-app.railway.app/reports
```

That's it. Never run anything again.

### `auto-sdlc install-hook` Implementation

**New file: `src/auto_sdlc/hook.py`**

```python
def read_claude_settings(settings_path=None) -> dict
    # reads ~/.claude/settings.json, returns {} if missing

def write_claude_settings(settings_path, data: dict)
    # writes formatted JSON, creates parent dirs

def is_hook_installed(settings: dict) -> bool
    # True if any Stop hook command contains "auto-sdlc"

def install_hook(user_id, export_url, settings_path=None) -> bool
    # idempotent — adds hook, returns True if newly added

def uninstall_hook(settings_path=None) -> bool
    # removes auto-sdlc entry, returns True if found and removed
```

**New CLI commands in `src/auto_sdlc/cli.py`**:

```bash
# Install
auto-sdlc install-hook --user-id you@company.com \
                       --url https://your-app.railway.app/reports

# Remove
auto-sdlc uninstall-hook

# Check status
auto-sdlc hook-status
```

### Files Changed
| File | Action | ~Lines |
|------|--------|--------|
| `src/auto_sdlc/hook.py` | New — read/write settings.json, install/uninstall | ~80 |
| `src/auto_sdlc/cli.py` | Add install-hook, uninstall-hook, hook-status commands | +40 |
| `tests/test_hook.py` | New — 8 test cases | ~90 |

---

## Complete Developer Journey (After All 3 Parts)

```
1. Admin deploys to Railway (once)
   → https://sdlc.company.railway.app/

2. Each developer runs one command (once):
   auto-sdlc install-hook --user-id you@company.com \
                          --url https://sdlc.company.railway.app/reports

3. From then on: completely automatic
   → Every Claude session ends → logs auto-sync → dashboard updates

4. Team lead checks:
   → https://sdlc.company.railway.app/team/html
```

---

## Implementation Order

| Step | Part | What | Effort |
|------|------|------|--------|
| 1 | A | Add Procfile + deploy to Railway | 30 min |
| 2 | B | Update landing page to show CLI first | 15 min |
| 3 | C | Implement hook.py + CLI commands | ~2 hrs |
| 4 | C | Tests for hook system | ~1 hr |
| 5 | C | Push + verify hook fires correctly | 30 min |

---

## Status

| Part | Status |
|------|--------|
| A: Railway deployment | ❌ Not started |
| B: CLI-first landing page | ❌ Not started |
| C: Auto-sync hook | ❌ Not started |

---

## Future: Persistent Storage (Post-Phase 3)

Railway containers are ephemeral — reports disappear on redeploy unless using a Volume.
SQLite on a Railway Volume would fix this permanently and also enable:
- Historical trending (maturity over time)
- Deduplication (don't re-process same session twice)
- `GET /reports/<user_id>` returning history

This is Task 12 from the original backlog.
