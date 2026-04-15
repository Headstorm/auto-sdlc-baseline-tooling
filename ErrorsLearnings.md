# Errors & Learnings - Auto-SDLC Report Upload UI

This document captures key issues, bugs, and learnings from the implementation of the Report Upload UI feature.

## Critical Errors

### 1. **Python String Escaping in JavaScript** ⚠️ CRITICAL
**Issue:** JavaScript code embedded in Python multi-line strings had escape sequences interpreted by Python instead of being passed through to the browser.

**Symptom:** 
```javascript
// What we wrote:
const parts = buffer.split('\n\n');

// What Python returned to browser:
const parts = buffer.split('
');  // Actual newlines - BROKEN!
```

**Root Cause:** In Python triple-quoted strings `"""..."""`, escape sequences like `\n` are interpreted as actual newlines, breaking the JavaScript syntax.

**Solution:** Escape the backslashes for JavaScript:
```python
# Instead of:
const parts = buffer.split('\n\n');

# Use:
const parts = buffer.split('\\n\\n');
```

**Learning:** When embedding JavaScript (or any language with backslash escapes) in Python strings, double-escape: `\\n` → produces `\n` in output.

**Prevention:** 
- Use raw strings: `r"""..."""` (if no Python escapes needed)
- Or extract large JavaScript blocks to separate files
- Always test by checking actual HTTP response: `curl http://localhost:8000/ | grep "split("`

---

### 2. **Module/Package Namespace Collision** 🔴 CRITICAL
**Issue:** Created `src/auto_sdlc/server/extractors.py` (making `server` a package), but `src/auto_sdlc/server.py` (module) already existed. Python resolved `auto_sdlc.server` to the package, not the module.

**Symptom:**
```
ImportError: cannot import name 'create_app' from 'auto_sdlc.server'
```

The import was looking for `create_app` in `server/__init__.py`, not in `server.py`.

**Root Cause:** When a directory has `__init__.py`, it becomes a package with higher import priority than a same-named `.py` file.

**Solution:** Renamed `server.py` → `server/_app.py` to avoid collision, then re-exported from `server/__init__.py`:
```python
# server/__init__.py
from auto_sdlc.server._app import create_app
__all__ = ["create_app"]
```

**Learning:** Be cautious about creating packages/directories alongside similarly-named modules. Choose clear naming:
- Package pattern: `src/auto_sdlc/handlers/` + `handlers/_app.py`
- Module pattern: `src/auto_sdlc/app.py` (single file, no directory)

**Prevention:** 
- Use `python3 -c "from auto_sdlc.server import create_app"` immediately after making changes
- Organize by responsibility, not by file type

---

### 3. **Uvicorn Entry Point Configuration** 🟡 MEDIUM
**Issue:** Tried to start server with `python -m uvicorn auto_sdlc.server:app` but the `app` instance didn't exist at module level.

**Symptom:**
```
Error loading ASGI app. Attribute "app" not found in module "auto_sdlc.server".
```

**Root Cause:** `create_app()` returns an app instance, but Uvicorn needs a module-level variable named `app`.

**Solution:** Created `src/auto_sdlc/app.py` as the entry point:
```python
# app.py
import os
from pathlib import Path
from auto_sdlc.server import create_app

_reports_dir = os.environ.get("REPORTS_DIR") or str(Path.home() / ".auto-sdlc" / "server" / "reports")
app = create_app(_reports_dir)
```

Then: `python -m uvicorn auto_sdlc.app:app --reload --port 8000`

**Learning:** Uvicorn needs:
- Module path: `auto_sdlc.app`
- Variable name: `app`
- Format: `module:variable`

**Prevention:** Create an explicit entry point module for server startup, don't rely on functions.

---

## Bugs Found During Testing

### 4. **Import Error in pdf_renderer.py** 🐛
**Issue:** Incorrect import path for models.

**What Failed:**
```python
from src.auto_sdlc.reports.models import TeamReport  # ❌ Wrong
```

**Fix:**
```python
from auto_sdlc.reports.models import TeamReport  # ✅ Correct
```

**Learning:** When running from package context, don't include `src/` in imports. Python's import system handles the path mapping.

---

### 5. **Roadmap Generator Missing L4 Dimensions** 🐛
**Issue:** Roadmap generator created placeholder roadmaps only for dimensions with maturity levels < 4, causing "Missing roadmaps" error for L4 dimensions.

**Fix:** Updated roadmap generator to create placeholder roadmaps for all dimension levels, including L4.

**Learning:** When building hierarchical structures, ensure ALL levels are handled, not just the intermediate ones.

---

## Process Learnings

### 6. **Subagent-Driven Development is Effective** ✅
**What Worked:**
- Fresh subagent per task prevented context pollution
- Two-stage review (spec compliance → code quality) caught issues early
- Bugs were discovered and fixed during integration testing
- Clear separation of concerns: implementer, spec reviewer, quality reviewer

**Metrics:**
- 4 tasks completed with full spec + quality approval
- 2 bugs found and fixed during integration testing
- 0 blockers in final implementation

**Learning:** When task specs are clear, subagent-driven development produces high-quality results faster than human manual coding.

---

### 7. **Spec Compliance Review Saves Rework** ✅
**What We Did:** Every completed task went through spec compliance review before code quality review.

**Results:**
- Task 2: User validation was missing → caught early, implementer added it
- Task 3: All requirements met on first try (good spec → good code)

**Learning:** Invest in detailed specs. The spec compliance review caught gaps that would have meant rework later.

---

### 8. **Integration Testing Catches Real Issues** ✅
**Discovery Process:**
1. Created test ZIP file with minimal logs
2. Called `/upload-logs` endpoint
3. Watched SSE progress stream
4. Verified PDF generation
5. **Found:** Import error + roadmap bug in pipeline

**Learning:** Don't skip integration testing, even if unit tests pass. End-to-end testing exercises the entire pipeline and catches integration issues.

---

## Architecture Decisions

### 9. **Service Layer Pattern** ✅
**Decision:** Created `reports/service.py` as a thin wrapper around `ReportGenerationPipeline`.

**Benefit:**
- Decouples server from pipeline internals
- Clean interface for both web and programmatic callers
- Easy to extend (add caching, logging, metrics)

**Pattern:**
```python
# reports/service.py
class ReportService:
    def generate_report(...) -> Tuple[Report, Path]:
        pipeline = ReportGenerationPipeline()
        return pipeline.generate_report(...)
```

**Learning:** Even simple wrappers provide stability and flexibility.

---

### 10. **Tabbed UI for Multiple Workflows** ✅
**Decision:** Single landing page with two tabs instead of separate pages.

**Benefit:**
- Unified look and feel
- Shared progress bars and styling
- Easy to add more upload types (project ZIP, configs, etc.)

**Pattern:**
```html
<div class="tabs">
  <button onclick="switchTab('project')">Project Path</button>
  <button onclick="switchTab('logs')">Upload Logs</button>
</div>

<div id="project" class="tab-content active"><!-- form --></div>
<div id="logs" class="tab-content"><!-- form --></div>

<script>
  function switchTab(tab) {
    // Toggle visibility
    // Reset progress
  }
</script>
```

**Learning:** Tabs reduce page clutter while keeping related functionality together.

---

## Future Improvements

### 11. **Token Efficiency** 🎯
**Current:** Only logs upload implemented (no LLM needed for extraction).

**Next:** Project directory upload requires scanning CLAUDE.md, AGENTS.md, .rules files.
- **Risk:** LLM usage for file scanning could be expensive
- **Solution:** Batch scanning, caching, or smart sampling

**Learning Placeholder:** Document token costs before implementing config scanning.

---

### 12. **Team Batching** 🎯
**Current:** Single user at a time.

**Next:** Aggregate multiple user reports for team analysis.
- **Risk:** Complex aggregation logic, potential for data consistency issues
- **Solution:** Defer until single-user flow is rock solid

**Learning:** Don't build batch features until the single-item flow is proven.

---

## Debugging Techniques That Worked

### Console Logging
```javascript
console.log('Scripts loading...');  // Verify script execution
```

Added before/after key sections to verify script tag was being executed.

### HTML Inspection
```bash
curl -s http://localhost:8000/ | sed -n '360,380p'  # Check specific line ranges
curl -s http://localhost:8000/ | grep "console.log"  # Verify changes were served
```

### Syntax Validation
```bash
python3 -m py_compile server/_app.py  # Verify Python syntax
```

**Learning:** Chain simple tools (curl, grep, sed) for quick debugging before complex analysis.

---

## Conventions & Best Practices

### Always Use `python3` Not `python`
**Standard:** Use `python3` in all scripts, documentation, and examples.

**Why:** 
- `python` may resolve to Python 2 (deprecated) on some systems
- `python3` explicitly requests Python 3.x
- Clearer intent and more portable

**Examples:**
```bash
# ✅ Correct
python3 -m uvicorn auto_sdlc.app:app
python3 -c "from auto_sdlc.server import create_app"
python3 -m py_compile server/_app.py

# ❌ Avoid
python -m uvicorn auto_sdlc.app:app
python -c "from auto_sdlc.server import create_app"
```

---

## Summary Checklist

- ✅ Always use `python3` in scripts and documentation (not `python`)
- ✅ Multi-line Python strings with JavaScript require escape: `\\n` not `\n`
- ✅ Package/module namespace collisions can break imports silently
- ✅ Uvicorn needs module-level `app` variable with specific naming
- ✅ Subagent-driven development + spec compliance works great
- ✅ Integration testing catches real bugs in pipeline
- ✅ Service layer pattern provides clean abstractions
- ✅ Tabbed UI scales well for multiple workflows
- ⚠️ Config scanning needs token efficiency planning
- ⚠️ Team batching deferred until single-user proven
- 🎯 Future: Monitor SSE reliability at scale, add error recovery UI

---

## References

- **File Moved:** `server.py` → `server/_app.py` (namespace collision fix)
- **Entry Point:** `src/auto_sdlc/app.py` (Uvicorn entrypoint)
- **Service Layer:** `src/auto_sdlc/reports/service.py`
- **Landing Page:** `src/auto_sdlc/server/_app.py` lines 107-530 (HTML/JS)
- **Backend Endpoint:** `src/auto_sdlc/server/_app.py` lines 607-683 (`/upload-logs`)

---

**Last Updated:** 2026-04-15  
**Status:** Implementation Complete, Integration Tested, Bugs Fixed
