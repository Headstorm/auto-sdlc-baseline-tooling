# Four-Phase Report Generation Implementation

## Overview
Build PDF report generation system that synthesizes logs + configs + capabilities into professional Team AI Maturity Reports and Individual Developer Profiles across 12 sub-dimensions.

Reports map Claude logs to the 4 Capability/Integration/Governance/Execution Ownership dimensions with L1-L4 maturity levels.

## Phase 1: Evidence Extraction from All Three Sources

### Task 1.1: Log Evidence Extractor
- Module: `src/auto_sdlc/reports/evidence_extractor.py`
- Extract behavioral signals from existing logs (reuse parser.py, scorer.py, metrics.py, maturity.py)
- Per-dimension log signals: tool usage %, prompt quality, /command adoption, context loading, MCP invocations, test generation
- Output: `LogEvidence` dataclass with dimension-level metrics and confidence levels
- **Tests**: 4+ test cases covering each dimension

### Task 1.2: Config Evidence Extractor
- Module: `src/auto_sdlc/reports/config_extractor.py`
- Parse CLAUDE.md, AGENTS.md, .rules, settings.json (if present in project)
- Extract documented practices, tool policies, quality standards, security policies
- Map config content to each dimension
- Output: `ConfigEvidence` dataclass with presence/quality/freshness signals
- **Tests**: 3+ test cases for config parsing

### Task 1.3: Capability Evidence Extractor
- Module: `src/auto_sdlc/reports/capability_extractor.py`
- Inventory custom skills (/review, /commit, /plan, etc.)
- Inventory agents (from AGENTS.md or .claude/agents/)
- Inventory MCP integrations (from installed plugins)
- Map capabilities to dimensions
- Output: `CapabilityEvidence` dataclass with capability counts, sophistication signals
- **Tests**: 2+ test cases

### Task 1.4: Evidence Triangulation
- Module: `src/auto_sdlc/reports/evidence.py` — Main evidence class
- `Evidence` class: combines LogEvidence + ConfigEvidence + CapabilityEvidence
- Per-dimension confidence scoring (high/medium/low based on all three sources)
- Output: `Evidence` object ready for synthesis phase
- **Tests**: 3+ test cases

---

## Phase 2: Assessment Questions + Scoring

### Task 2.1: Assessment Questions Engine
- Module: `src/auto_sdlc/reports/assessment.py`
- Load 50 assessment questions organized by 5 sections (from CLAUDE.md Appendix)
- Per-dimension questions (6-8 questions per dimension × 12 = ~50 total)
- Output: `AssessmentQuestion` list with dimension mapping
- **Tests**: Verify all 12 dimensions covered, question count

### Task 2.2: Maturity Scorer
- Module: `src/auto_sdlc/reports/maturity_scorer.py`
- Input: Evidence + Assessment Question Responses
- Per-dimension scoring logic:
  - Evidence signals → preliminary L1-L4 estimate
  - Assessment responses → refine estimate
  - Confidence adjustment based on data availability
- Output: `DimensionScore` per dimension (level, confidence, evidence summary)
- **Tests**: 4+ test cases covering L1-L4 transitions

### Task 2.3: Roadmap Generator
- Module: `src/auto_sdlc/reports/roadmap.py`
- For each dimension: "How to progress from current → next level"
- Include: specific actions, effort estimates (hours + calendar months), dependencies
- Output: `RoadmapItem` per dimension
- **Tests**: 2+ test cases

---

## Phase 3: Report Templates + Schemas

### Task 3.1: Report Data Models
- Module: `src/auto_sdlc/reports/models.py`
- `DimensionReport`: score, evidence summary, gap analysis, roadmap
- `TeamReport`: 12 dimension reports + team aggregates + confidence
- `IndividualReport`: same structure, developer-focused
- **Tests**: Schema validation tests (3+)

### Task 3.2: Report Assembly
- Module: `src/auto_sdlc/reports/report_builder.py`
- `TeamReportBuilder`: assembles team report from evidence + scores + roadmap
- `IndividualReportBuilder`: assembles individual report
- Include narrative context, section headings, key insights
- Output: Report object ready for PDF rendering
- **Tests**: 3+ test cases

### Task 3.3: PDF Rendering
- Module: `src/auto_sdlc/reports/pdf_renderer.py`
- Use ReportLab or similar to generate professional PDFs
- Team Report: 8-12 pages (cover, executive summary, 4 dimension sections, appendix)
- Individual Report: 4-6 pages (same structure, developer-focused)
- Output: PDF file to `reports/` directory
- **Tests**: 2+ test cases (verify PDF generation, basic structure)

---

## Phase 4: Integration + CLI

### Task 4.1: Report Generation CLI Command
- Module: `src/auto_sdlc/cli.py` — add `report` command
- `auto-sdlc report --user-id USER --project-path PATH --output-dir DIR`
- Calls: evidence extraction → assessment scoring → report assembly → PDF rendering
- Output: PDF + JSON report to disk
- **Tests**: Integration test (2+)

### Task 4.2: Server Endpoint
- Module: `src/auto_sdlc/server.py` — add `/report` endpoint
- POST /report: accept user_id, project_path → generate + return PDF
- GET /report/:user_id: retrieve cached PDF
- **Tests**: 2+ endpoint tests

### Task 4.3: Documentation + Examples
- Update README with report generation workflow
- Create `docs/REPORT_GENERATION.md` with examples
- Include sample report structure, question walkthrough

---

## Files Created

| Path | Purpose |
|------|---------|
| `src/auto_sdlc/reports/` | New folder for all report-related modules |
| `src/auto_sdlc/reports/__init__.py` | Package init |
| `src/auto_sdlc/reports/evidence_extractor.py` | Log evidence extraction |
| `src/auto_sdlc/reports/config_extractor.py` | Config evidence extraction |
| `src/auto_sdlc/reports/capability_extractor.py` | Capability evidence extraction |
| `src/auto_sdlc/reports/evidence.py` | Evidence triangulation + confidence |
| `src/auto_sdlc/reports/assessment.py` | Assessment questions engine |
| `src/auto_sdlc/reports/maturity_scorer.py` | L1-L4 scoring logic |
| `src/auto_sdlc/reports/roadmap.py` | Roadmap generation |
| `src/auto_sdlc/reports/models.py` | Report data models |
| `src/auto_sdlc/reports/report_builder.py` | Report assembly |
| `src/auto_sdlc/reports/pdf_renderer.py` | PDF generation |
| `tests/reports/` | Test folder for all report modules |

---

## Task Dependency Order

Execute in this order (most tasks independent, some depend on earlier modules):

**Phase 1 (Evidence):**
1. Task 1.1 (Log evidence) — no dependencies, uses existing logs/
2. Task 1.2 (Config evidence) — no dependencies
3. Task 1.3 (Capability evidence) — no dependencies
4. Task 1.4 (Triangulation) — depends on 1.1-1.3

**Phase 2 (Scoring):**
5. Task 2.1 (Assessment questions) — no dependencies
6. Task 2.2 (Maturity scorer) — depends on 1.4 + 2.1
7. Task 2.3 (Roadmap) — no dependencies

**Phase 3 (Reports):**
8. Task 3.1 (Data models) — no dependencies
9. Task 3.2 (Report builder) — depends on 2.2-2.3 + 3.1
10. Task 3.3 (PDF rendering) — depends on 3.1

**Phase 4 (Integration):**
11. Task 4.1 (CLI command) — depends on all Phase 1-3
12. Task 4.2 (Server endpoint) — depends on 4.1
13. Task 4.3 (Documentation) — depends on 4.1-4.2

---

## Execution Model

- **Tasks 1.1-1.3**: Dispatch 3 subagents in parallel (no dependencies)
- **Task 1.4**: After 1.1-1.3 complete
- **Tasks 2.1, 2.3**: Dispatch in parallel after 1.4
- **Task 2.2**: After 2.1 + 1.4 complete
- **Tasks 3.1-3.3**: Sequential (3.2 depends on models, 3.3 depends on models)
- **Tasks 4.1-4.3**: Sequential (4.2 depends on 4.1, 4.3 depends on both)

---

## Success Criteria

- ✅ All 12 sub-dimensions covered in evidence extraction
- ✅ Evidence triangulation produces confidence levels (high/medium/low)
- ✅ L1-L4 scoring logic matches CLAUDE.md rubric + assessment questions
- ✅ Team and Individual reports generated as PDFs
- ✅ All tests passing (20+ tests across all phases)
- ✅ CLI command works end-to-end
- ✅ Code lives in `src/auto_sdlc/reports/` folder, imports from existing `logs/`
