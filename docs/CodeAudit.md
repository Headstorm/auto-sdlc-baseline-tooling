# Auto-SDLC Code Audit

Last updated: 2026-04-15. Covers all files under `src/auto_sdlc/`.

## Status Legend
- **USED** — imported and called by live code paths
- **PARTIAL** — module used but some exports are dead/orphaned
- **DEAD** — defined but never reachable from the current CLI or server

---

## Entry Points

| File | Status | Notes |
|------|--------|-------|
| `cli.py` | USED | No `[project.scripts]` in `pyproject.toml` — `auto-sdlc` binary not installed |
| `app.py` | USED | Uvicorn entry point (`auto_sdlc.app:app`) |

**Issue:** `pyproject.toml` has no `[project.scripts]` entry. `pip install auto-sdlc` produces no `auto-sdlc` binary. Users must call `python3 -m auto_sdlc.cli` directly.

---

## Server Module

| File | Status | Notes |
|------|--------|-------|
| `server/__init__.py` | PARTIAL | Re-exports `create_app` but nothing imports from the package level |
| `server/_app.py` | PARTIAL | See issues below |
| `server/extractors.py` | PARTIAL | `merge_project_with_logs` never imported — DEAD |

**`server/_app.py` issues:**
- `_find_projects_dir` duplicated here AND in `server/extractors.py` (slightly different fallback logic)
- `ValidationResponse`, `StatusResponse`, `ErrorResponse` Pydantic models defined but never used as return/response types — DEAD
- `/upload` route uses the **legacy** 5-dimension `build_report()` pipeline; all other routes use the new 12-dimension `ReportService` — architectural inconsistency
- Multiple SSE endpoints with near-identical streaming logic: `/upload-logs`, `/generate-report`, `/generate-individual-report`, `/api/report/generate` — duplication

---

## Logs Module

| File | Status | Notes |
|------|--------|-------|
| `logs/parser.py` | USED | `parse_session_file`, `find_session_files` both called |
| `logs/analyzer.py` | USED | All three functions used |
| `logs/scorer.py` | PARTIAL | `extract_real_prompts` only called internally; `score_prompt` imported in `evidence_extractor.py` but never called |
| `logs/metrics.py` | PARTIAL | `extract_behavioral_metrics` imported in `evidence_extractor.py` but never called |
| `logs/maturity.py` | PARTIAL | `build_maturity_report` and `score_dimension` imported in `evidence_extractor.py` but never called — DEAD imports |
| `logs/report.py` | PARTIAL | `build_report` used by `/upload` route; `run_logs_report` has no caller in current CLI |
| `logs/ingest.py` | PARTIAL | Entire module orphaned from current CLI — only reachable from tests |
| `logs/export.py` | PARTIAL | `export_report_to_http` orphaned; `export_report_to_dir` used by `ingest.py` only |
| `logs/team.py` | USED | Used by `ingest.py` and `server/_app.py` `/team` routes |
| `logs/render_html.py` | USED | Used by `ingest.py` and `server/_app.py` `/dashboard` route |
| `logs/qualitative.py` | PARTIAL | Only triggered by `--qualitative` flag; current CLI has no such flag — unreachable |

---

## Reports Module

| File | Status | Notes |
|------|--------|-------|
| `reports/__init__.py` | PARTIAL | Re-exports never imported at package level |
| `reports/models.py` | USED | `CONFIDENCE_LEVELS`, `MATURITY_LEVELS` unused externally |
| `reports/service.py` | USED | Used by CLI and server |
| `reports/pipeline.py` | USED | Core 4-phase pipeline |
| `reports/evidence_extractor.py` | PARTIAL | 4 dead imports: `score_prompt`, `extract_behavioral_metrics`, `build_maturity_report`, `score_dimension` |
| `reports/evidence.py` | USED | — |
| `reports/config_extractor.py` | USED | — |
| `reports/capability_extractor.py` | USED | — |
| `reports/assessment.py` | PARTIAL | 7 of 8 public methods never called externally |
| `reports/maturity_scorer.py` | USED | — |
| `reports/roadmap.py` | USED | — |
| `reports/report_builder.py` | USED | 4 methods near-identical between `TeamReportBuilder` and `IndividualReportBuilder` |
| `reports/pdf_renderer.py` | USED | — |

---

## Audit / Init Wizard Modules

| File | Status | Notes |
|------|--------|-------|
| `audit/__init__.py` | DEAD | Empty package marker |
| `audit/scanner.py` | DEAD | Stub (`run_audit()` prints "not implemented"); no caller in current CLI |
| `init_wizard/__init__.py` | DEAD | Empty package marker |
| `init_wizard/wizard.py` | DEAD | Stub (`run_wizard()` prints "not implemented"); no caller in current CLI |

---

## Cross-Cutting Issues

### Duplication
1. `_find_projects_dir` — in both `server/_app.py` and `server/extractors.py` with slightly different logic
2. `_LEVEL_LABELS` — in both `logs/maturity.py` and `logs/team.py`
3. `_LEVEL_COLORS` — in both `logs/render_html.py` and `logs/team.py`
4. 4 methods near-identical between `TeamReportBuilder` and `IndividualReportBuilder` in `report_builder.py`

### Two Parallel Maturity Systems
- **Legacy** (`logs/maturity.py`): 5 dimensions, 0–4 scale, Beginner–Expert labels. Used by `/upload` route.
- **New** (`reports/maturity_scorer.py`): 12 dimensions, L1–L4. Used by CLI and `/generate-*` routes.
These produce incompatible report objects.

### Dead Imports in `reports/evidence_extractor.py`
```python
from auto_sdlc.logs.scorer import score_session_prompts, score_prompt   # score_prompt unused
from auto_sdlc.logs.metrics import aggregate_behavioral_metrics, extract_behavioral_metrics  # extract_behavioral_metrics unused
from auto_sdlc.logs.maturity import build_maturity_report, score_dimension  # both unused
```

### Missing CLI Entry Point
`pyproject.toml` has no `[project.scripts]` section. `auto-sdlc` is not a runnable command after `pip install`.
