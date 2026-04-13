# AI Maturity Assessment Reports

Complete guide to generating and understanding professional AI maturity reports for your team.

---

## Section 1: Overview

### What Are AI Maturity Reports?

AI Maturity Reports are professional PDF assessments that measure your team's capability to effectively use AI tools and integrate them into your development workflow. Rather than a simple adoption metric, maturity reflects how well AI is **governed, integrated, and owned** by your organization.

The reports are built on the **Ideal Development Team framework**, which defines what world-class AI-augmented development looks like across 4 strategic dimensions and 12 operational sub-dimensions.

### Why Assess AI Maturity?

- **Strategic Planning** — Understand where your team stands relative to industry baselines
- **Investment Prioritization** — Identify which AI capabilities create the most value
- **Risk Management** — Surface governance and security gaps early
- **Team Development** — Create personalized growth paths for developers
- **Competitive Positioning** — Demonstrate AI capability to stakeholders

### The 4 Dimensions & 12 Sub-Dimensions

| # | Dimension | Sub-Dimension | What It Measures |
|---|-----------|---|---|
| **1** | **Capability** | AI Tool Adoption | Are tools standardized or scattered across the team? |
| **2** | | Prompt & Context Engineering | Do developers share context or rebuild from scratch each session? |
| **3** | | Agent Configuration | Are custom agents configured or using out-of-the-box tools? |
| **4** | **Integration** | CI/CD Integration | Is AI integrated into the build and deployment pipeline? |
| **5** | | Ticketing & Planning | Is AI used to validate work before starting development? |
| **6** | | Cross-System Connectivity | Can AI access repos, documentation, JIRA, Slack, and other systems? |
| **7** | **Governance** | Quality Controls | Are AI outputs held to the same code quality standards? |
| **8** | | Security & Compliance | Is AI usage governed, auditable, and compliant? |
| **9** | | Measurement & KPIs | Are metrics tracked to demonstrate AI impact? |
| **10** | **Execution Ownership** | Ways of Working | Are AI workflows documented and shared across the team? |
| **11** | | Accountability & Ownership | Is AI adoption owned by a specific person or team? |
| **12** | | Scalability & Knowledge Transfer | Can new developers become productive with AI quickly? |

### The 4 Maturity Levels

Reports use a 4-level maturity scale, similar to CMMI and ITIL frameworks:

| Level | Name | Characteristics |
|-------|------|---|
| **L1** | **Assisted** | Early adoption, tool exploration, limited standardization. Teams are learning AI and experimenting with use cases. |
| **L2** | **Integrated** | Documented practices, emerging tooling standards, consistent usage patterns. Teams have standardized on tools and documented basic workflows. |
| **L3** | **Agentic** | Multi-tool ecosystem, automation frameworks, governance in place. Teams have built custom agents and automated significant workflows. |
| **L4** | **Autonomous** | Self-improving practices, proactive integration, full optimization. Teams continuously improve AI usage and have deep integration across all systems. |

---

## Section 2: Report Types

### Team Reports (8-12 Pages)

**Audience:** Leadership, team leads, engineering directors

**Scope:** Entire team or organization

**Content:**
- Executive summary with overall team maturity level
- Breakdown by each dimension (current state, strengths, gaps)
- Team-wide benchmarking against industry baselines
- Identified bottlenecks preventing progression
- Strategic roadmap with effort and timeline estimates
- Recommendations prioritized by impact and effort

**Use Cases:**
- Quarterly or annual team assessments
- Demonstrating AI capability to stakeholders
- Budget planning for tools and training
- Identifying team-wide capability gaps

**Example Output:**
```
Executive Summary
─────────────────
Your team is L2 (Integrated) in AI Maturity

Strengths:
  • 85% Claude Code adoption across the team
  • Documented CLAUDE.md in 8/9 repositories
  • /review skill adopted by 70% of developers

Gaps:
  • Limited CI/CD integration (only 2/8 pipelines use /review)
  • No formal governance policy
  • Assessment evidence incomplete

Roadmap to L3:
  • Implement automated testing in CI/CD (2-4 weeks)
  • Document governance policy (1 week)
  • Deploy custom agents for code review (3-4 weeks)
```

### Individual Reports (4-6 Pages)

**Audience:** Individual developers, their managers, AI champions

**Scope:** Single developer's usage patterns and capabilities

**Content:**
- Personal AI maturity profile
- How the developer compares to team baseline
- Strengths and areas for growth
- Personalized learning path
- Specific tool and skill recommendations

**Use Cases:**
- One-on-one development conversations
- Identifying high performers vs. struggling developers
- Tailored training and mentorship
- Career development planning

**Example Output:**
```
Developer Profile: Alice Chen
─────────────────────────────

Your Maturity: L2.5 (Above team average of L2.0)

Strengths:
  • High prompt quality score (82/100)
  • Consistent daily usage (0.8 sessions/day)
  • Strong context engineering skills

Growth Areas:
  • Limited tool diversity (2/5 available tools)
  • Occasional context switching issues
  • Not using /review skill yet

Next Steps:
  • Try the /review skill on your next PR
  • Experiment with MCP integrations for your workflow
  • Share your context engineering approach with the team
```

---

## Section 3: Data Sources & Confidence

Report confidence depends on the quality and completeness of available data. The assessment uses **three independent sources** to triangulate maturity:

### The Three Sources

| Source | What It Captures | Example |
|--------|---|---|
| **Logs** | Actual usage patterns from Claude Code sessions | 85% adoption rate, average prompt quality 72/100, 0.6 sessions/day |
| **Configs** | Documented practices and standards | CLAUDE.md present, governance policy in place, .rules file enforced |
| **Capabilities** | Installed tools, skills, and integrations | /review skill deployed, 3 custom agents, MCP integrations active |

### Confidence Levels

```
┌─────────────────────────────────────────┐
│ Available Data      │ Confidence Level   │
├─────────────────────────────────────────┤
│ All three sources   │ HIGH              │
│ Two sources         │ MEDIUM            │
│ One source only     │ LOW               │
│ Estimated from gaps │ VERY LOW          │
└─────────────────────────────────────────┘
```

### What High, Medium, and Low Confidence Mean

**HIGH Confidence:** Logs + Configs + Capabilities all available
- Assessment reflects reality
- Roadmap is specific and actionable
- Suitable for leadership decisions

**MEDIUM Confidence:** Logs + one of (Configs or Capabilities)
- Assessment is directionally correct but may miss details
- Roadmap needs validation during implementation
- Suitable for team-level planning

**LOW Confidence:** Logs only, or incomplete data
- Assessment is indicative but not definitive
- Roadmap requires significant refinement
- Flag as "needs validation" to team

**Example Data Report:**

```
ASSESSMENT DATA SOURCES
───────────────────────
Logs:         ✅ 8 weeks of session data from 12 developers
Configs:      ⚠️  CLAUDE.md found in 6/9 repos; .rules missing
Capabilities: ❌ Not collected (pending inventory)

CONFIDENCE BY DIMENSION
───────────────────────
✅ HIGH:   Prompting Sophistication, Tool Adoption, Usage Frequency
⚠️  MEDIUM: Quality Controls, CI/CD Integration, Agent Configuration
❌ LOW:    Governance, Accountability, Knowledge Transfer

RECOMMENDATION
───────────────
Schedule 30-min discovery call to collect:
  1. All AGENTS.md and .rules files
  2. Inventory of custom skills and MCP integrations
  3. Brief interview on governance practices
```

---

## Section 4: Generation Workflows

### Workflow A: CLI (Single Command)

**Best for:** Local analysis, CI/CD pipelines, scripted automation

**Requirements:**
- Auto-SDLC CLI installed: `pip install auto-sdlc`
- Project logs available at `~/.claude/projects/` (or specify with `--projects-dir`)

**Command:**

```bash
auto-sdlc report \
  --user-id platform_team \
  --project-path /path/to/project \
  --output-dir ./reports
```

**Output:**

```
✓ Extracting evidence from logs...
✓ Parsing configurations (CLAUDE.md, AGENTS.md)...
✓ Scanning capabilities...
✓ Triangulating evidence sources...
✓ Scoring maturity levels...
✓ Generating roadmaps...
✓ Building report...
✓ Rendering PDF...

Report saved to: ./reports/platform_team_report_2026-04-13.pdf
```

**CLI Options:**

```bash
auto-sdlc report \
  --user-id STRING                    # Team or developer identifier
  --project-path PATH                 # Path to project directory
  [--projects-dir PATH]               # Override ~/.claude/projects/
  [--output-dir PATH]                 # Save PDF here (default: ./reports)
  [--report-type team|individual]     # Default: team
  [--assessment-responses FILE]       # JSON with assessment answers
  [--since DATE]                      # Filter logs from DATE (YYYY-MM-DD)
  [--include-benchmark]               # Compare against industry baseline
```

### Workflow B: HTTP Server Endpoint

**Best for:** Web UI, team dashboards, no local CLI installation

**Requirements:**
- Auto-SDLC server running: `auto-sdlc serve --port 8000`
- HTTP client (curl, Postman, browser)

**Endpoint:**

```
POST /api/report/generate
Content-Type: application/json
```

**Request Payload:**

```json
{
  "user_id": "platform_team",
  "project_path": "/path/to/project",
  "report_type": "team",
  "output_dir": "./reports",
  "include_benchmark": true
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "platform_team",
    "project_path": "/path/to/project",
    "report_type": "team"
  }' \
  -o team_report.pdf
```

**Response:** PDF file stream (HTTP 200 with Content-Type: application/pdf)

**Error Responses:**

- `400 Bad Request` — Missing or invalid parameters
- `404 Not Found` — Project path does not exist
- `500 Internal Server Error` — Report generation failed

### Workflow C: With Assessment Responses

**Best for:** High-confidence reports, governance assessment, formal audits

**Requirements:**
- CLI or server endpoint (from Workflows A or B)
- Assessment responses JSON file

**Step 1: Collect Assessment Responses**

The assessment consists of 50 questions organized by dimension. Example questions:

```json
{
  "capability_tool_adoption_1": {
    "question": "Who decides which AI tool to use?",
    "answer": "Team lead approves all new tools; standardized on Claude"
  },
  "capability_context_engineering_1": {
    "question": "Does every repository have CLAUDE.md?",
    "answer": "Yes, all production repos have updated CLAUDE.md"
  },
  "governance_quality_controls_1": {
    "question": "Are AI outputs held to code quality standards?",
    "answer": "All /review outputs must pass 3-person sign-off"
  }
}
```

**Step 2: Generate Report with Assessment Data**

```bash
auto-sdlc report \
  --user-id platform_team \
  --project-path /path/to/project \
  --assessment-responses responses.json \
  --output-dir ./reports
```

**Output:**

```
✓ Extracting evidence from logs...
✓ Parsing configurations (CLAUDE.md, AGENTS.md)...
✓ Scanning capabilities...
✓ Processing assessment responses (50 answers)...
✓ Triangulating evidence sources...
✓ Scoring maturity levels...
✓ Flagging discrepancies (2 found)...
✓ Generating roadmaps...
✓ Building report...
✓ Rendering PDF...

Report saved to: ./reports/platform_team_report_2026-04-13.pdf

DISCREPANCIES FOUND:
  ⚠️  Logs show high /review adoption but assessment says "not yet rolled out"
     → Investigate: Is adoption greater than perceived?
  ⚠️  Configs show AI Tool Adoption is standardized, but logs show 3 different tools
     → Investigate: Have practices changed since config was written?
```

**Assessment responses increase:**
- Report confidence from LOW to MEDIUM/HIGH
- Ability to assess dimensions invisible to logs (governance, ownership)
- Quality of roadmap recommendations

---

## Section 5: Report Structure

All reports follow a consistent, professional structure:

### Cover Page

```
┌─────────────────────────────────┐
│                                 │
│   AI MATURITY ASSESSMENT REPORT │
│                                 │
│   Platform Team                 │
│   Assessment Period: Q1 2026    │
│   Report Date: April 13, 2026   │
│                                 │
│   Overall Maturity: L2          │
│   (Integrated)                  │
│                                 │
└─────────────────────────────────┘
```

### Executive Summary (1 Page)

- **Key Finding:** Overall maturity level with one-sentence rationale
- **Assessment Highlights:** 2-3 top strengths
- **Critical Gaps:** 2-3 top gaps preventing progression
- **Strategic Recommendations:** Top 3 actions to prioritize
- **Next Review:** Recommended timing for next assessment

### Methodology (1 Page)

Explains:
- The 4 dimensions and 12 sub-dimensions
- L1-L4 maturity levels
- How data was collected (logs, configs, capabilities, assessment responses)
- Confidence levels by dimension
- How to interpret the results

### Dimension Deep-Dives (1-2 Pages Per Dimension)

For each of the 4 dimensions:

**Current State**
- Maturity level (L1-L4)
- Confidence level and supporting evidence
- Key metrics from logs

**What's Working Well**
- 2-3 strengths to build on
- Evidence and examples
- Team/developer commendations where applicable

**What Needs Improvement**
- 2-3 gaps blocking progression
- Evidence and impact assessment
- Comparison to industry baseline if available

**Roadmap to Next Level**
- Specific, actionable steps (5-10 items)
- Effort estimate per step (hours/weeks)
- Timeline for completion
- Dependencies or prerequisites
- Success criteria

**Example:**

```
DIMENSION: Quality Controls (Governance)
─────────────────────────────────────────

Current State: L1 (Assisted)
Confidence: MEDIUM (logs + partial configs)

What's Working Well:
  ✓ /review skill is deployed and available (100% of developers have access)
  ✓ 65% of PRs use /review before merge
  ✓ /review outputs reduce average review cycle time by 2 days

What Needs Improvement:
  ✗ No formal policy on which outputs require sign-off
  ✗ Limited integration with CI/CD pipeline (manual invocation only)
  ✗ No metrics tracking /review impact or effectiveness

Roadmap to L2 (2-4 weeks effort):
  1. Document /review policy in CLAUDE.md (4 hours)
     - Define which PRs must use /review
     - Specify sign-off requirements
  2. Implement CI/CD hook to auto-invoke /review (1 week)
     - Integrate with GitHub Actions / GitLab CI
     - Fail pipeline if quality score below threshold
  3. Add metrics collection (3 days)
     - Track /review adoption rate
     - Measure defect reduction
  4. Train team on new policy (2 hours)
     - Present changes in standup
     - Walk through example workflow
```

### Strategic Recommendations (1 Page)

High-level priorities for next 3-6 months:

```
PRIORITY 1: CI/CD Integration (High Impact, Medium Effort)
────────────────────────────────────────────────────────────
Blocks progression in: Quality Controls, CI/CD Integration
Recommended timeline: Weeks 1-4
Expected impact: Shift Quality Controls from L1 to L2

PRIORITY 2: Governance Documentation (High Impact, Low Effort)
──────────────────────────────────────────────────────────────
Blocks progression in: Governance, Execution Ownership
Recommended timeline: Weeks 1-2
Expected impact: Shift Governance from L1 to L2

PRIORITY 3: Agent Standardization (Medium Impact, Medium Effort)
────────────────────────────────────────────────────────────────
Blocks progression in: Agent Configuration, Tool Adoption
Recommended timeline: Weeks 5-8
Expected impact: Shift Capability from L1.5 to L2
```

### Appendix

- **Raw Metrics Table** — All quantitative data used in scoring
- **Full Assessment Questions & Answers** — If assessment responses were collected
- **Benchmark Comparison** — How team compares to industry, if available
- **Glossary** — Terms and definitions

---

## Section 6: Assessment Questions

The report can be enhanced significantly by collecting team responses to 50 structured questions across the dimensions.

### Question Structure

Questions are organized by dimension and sub-dimension:

```
CAPABILITY DIMENSION
├── AI Tool Adoption (4 questions)
├── Prompt & Context Engineering (5 questions)
└── Agent Configuration (4 questions)

INTEGRATION DIMENSION
├── CI/CD Integration (4 questions)
├── Ticketing & Planning (4 questions)
└── Cross-System Connectivity (4 questions)

GOVERNANCE DIMENSION
├── Quality Controls (5 questions)
├── Security & Compliance (4 questions)
└── Measurement & KPIs (4 questions)

EXECUTION OWNERSHIP DIMENSION
├── Ways of Working (4 questions)
├── Accountability & Ownership (5 questions)
└── Scalability & Knowledge Transfer (4 questions)
```

### Example Questions

```
CAPABILITY DIMENSION
─────────────────────

AI Tool Adoption:
  Q1. Who decides which AI tool to use? By choice or enforcement?
  Q2. Are licenses managed centrally? How?
  Q3. Does the team standardize on 1-2 tools or pick individually?
  Q4. How do you handle license renewals and tool switching?

Prompt & Context Engineering:
  Q1. Does every repo have CLAUDE.md? What does it cover?
  Q2. Are prompt templates shared? How often are they reused?
  Q3. How do developers load context at session start?
  Q4. Do developers reference documentation, code, or both?
  Q5. How often do prompt improvements get shared across the team?

Agent Configuration:
  Q1. How many custom slash commands exist? (/review, /commit, /plan, etc.?)
  Q2. Are agents multi-step or single-function?
  Q3. How are agents versioned and updated?
  Q4. How do developers discover and learn new agents?

GOVERNANCE DIMENSION
─────────────────────

Quality Controls:
  Q1. Are AI outputs held to code quality standards?
  Q2. How are AI-generated tests validated?
  Q3. Is there a sign-off process for AI code?
  Q4. How do you detect and handle hallucinations?
  Q5. What's the rollback process if AI output is problematic?
```

### Collecting Responses

Assessment responses should be collected from:
- **Team Lead** — Overall governance, policies, standards
- **AI Champion** — Tool selection, agent configuration, training
- **Technical Lead** — Integration points, CI/CD practices
- **Security/Compliance** — Governance, audit, data handling

**Suggested Format:** JSON file with one entry per question

```json
{
  "respondent": "Alice Chen, Team Lead",
  "date": "2026-04-13",
  "questions": {
    "capability_tool_adoption_1": {
      "question": "Who decides which AI tool to use? By choice or enforcement?",
      "answer": "Team lead approves all new tools. Currently standardized on Claude."
    },
    "capability_context_engineering_1": {
      "question": "Does every repo have CLAUDE.md?",
      "answer": "Yes, all production repos have CLAUDE.md. Updated quarterly."
    }
  }
}
```

---

## Section 7: Understanding Your Results

### Reading the Maturity Levels

Each dimension is assessed on the L1-L4 scale:

**L1 (Assisted)**
- Early adoption phase
- Tool exploration underway
- Limited standardization
- Individual contributors figuring out AI workflow
- Documentation sparse or informal
- Governance ad-hoc or missing

Example: "We installed Claude Code 2 months ago. Some people use /review, others don't know about it yet."

**L2 (Integrated)**
- Documented practices established
- Tooling standards emerging
- Consistent usage patterns
- Formal documentation (CLAUDE.md, agent libraries)
- Basic governance in place
- Adoption trending upward across team

Example: "All devs have Claude Code. We documented /review skill in CLAUDE.md. 70% use it on PRs."

**L3 (Agentic)**
- Multi-tool ecosystem deployed
- Custom agents built and maintained
- Automation frameworks in place
- Governance enforced via CI/CD
- Measurement and KPIs tracked
- Ownership clear; champions in place

Example: "We built 3 custom agents (/review, /commit, /plan). /review runs automatically in CI. We measure effectiveness with metrics."

**L4 (Autonomous)**
- Self-improving practices
- Continuous integration of AI across all systems
- Full optimization and feedback loops
- Deep governance and compliance
- Knowledge transfer automated
- Industry-leading adoption and effectiveness

Example: "AI integration is automatic across all systems. We measure and improve continuously. New devs are productive with AI on day 1."

### Interpreting Your Report

**Example: Quality Controls Dimension**

```
Your team is L2 (Integrated) in Quality Controls:

Evidence:
  ✓ /review skill deployed (100% team access)
  ✓ 70% of PRs use /review before merge
  ✓ Documented in CLAUDE.md
  ✗ Limited CI/CD integration (manual invocation)
  ✗ No formal approval process
  ✗ No effectiveness metrics

Interpretation:
  Your team is using AI for code review consistently, but it's not yet
  integrated into your formal process. Next step: automate /review in CI/CD
  and establish sign-off criteria.

Next Step:
  Implement /review as mandatory CI check — L2 to L3 (2-4 weeks)
```

### Comparing to Baselines

If your report includes benchmark data, it will show how you compare:

```
Industry Baseline (Q1 2026):
  Quality Controls: L1.8 (median)
  Your team:       L2.0 (above average)

Interpretation:
  You're ahead of the median on Quality Controls. This is a competitive advantage.
  Focus on maintaining leadership while closing gaps in other dimensions.
```

---

## Section 8: Common Questions

### How often should we generate reports?

**Recommended:** Quarterly (every 3 months)

- **Quarterly:** Standard for team reviews, investment decisions, roadmap planning
- **Bi-annually:** Minimal tracking, reduced overhead
- **Annually:** Strategic reviews only
- **Ad-hoc:** After major changes (new tools, team growth, process updates)

### What if we're missing data sources?

The report will note low confidence areas, but you can:

1. **Collect missing data** before generating the report
   - Logs: Let sessions accumulate (2+ weeks recommended)
   - Configs: Export CLAUDE.md, AGENTS.md, .rules files
   - Capabilities: Run `auto-sdlc audit` to inventory tools

2. **Generate with low confidence** and flag for follow-up
   ```
   ⚠️ LOW CONFIDENCE: Governance dimension
      Reason: Configs and capabilities not available
      Recommended: Collect AGENTS.md and tool inventory before next review
   ```

3. **Plan data collection** for next report
   - Share this report with team
   - Identify missing pieces
   - Schedule follow-up assessment in 4 weeks with complete data

### Can we include assessment responses?

Yes! Assessment responses significantly improve report quality:

```bash
auto-sdlc report \
  --user-id my_team \
  --project-path /path \
  --assessment-responses responses.json
```

Assessment responses:
- Increase confidence from LOW to MEDIUM/HIGH
- Enable assessment of governance and ownership dimensions
- Help identify blind spots (log evidence vs. team perception)
- Create accountability through written answers

### How long does report generation take?

Typical timings:

| Data Size | Log Processing | Report Generation | Total |
|-----------|---|---|---|
| 1 person, 2 weeks | <1 second | 5-10 sec | ~10 sec |
| 5 people, 2 weeks | <2 sec | 10-15 sec | ~20 sec |
| 12 people, 8 weeks | 5-10 sec | 20-30 sec | ~40 sec |
| 50 people, 12 weeks | 30-60 sec | 40-60 sec | ~2 min |

With assessment responses (+10-15 sec processing) and benchmark comparison (+5 sec).

### What if the report doesn't match our perception?

This is valuable! It usually means:

1. **Logs show hidden patterns** — Usage you didn't realize existed
2. **Perception vs. reality** — Team thinks adoption is higher/lower than it is
3. **Blind spots** — Gaps you're not aware of
4. **Improvement opportunity** — Data to drive informed decisions

**Next steps:**
- Review the report with the team in a meeting
- Discuss discrepancies: "We thought adoption was 90%, but logs show 60%"
- Investigate root causes: Is adoption lower than perceived? Should we invest in training?
- Update roadmap based on insights

### Can I customize the report?

Future versions will support:

- Custom branding and logo
- Subset of dimensions to assess
- Custom benchmark groups
- Private vs. public sections

For now, reports are generated with standard structure and branding.

### How do we track improvement over time?

Generate quarterly reports and:

1. **Compare maturity levels** across quarters
   ```
   Q4 2025: L1.8
   Q1 2026: L2.0
   Progress: +0.2 levels in Quality Controls
   ```

2. **Track specific metrics**
   ```
   /review adoption: 40% — 65% — 78%
   Avg prompt quality: 62 — 68 — 72
   ```

3. **Review roadmap** against actual progress
   ```
   Q4 Roadmap item: "Implement /review in CI" — Status: DONE
   Q4 Roadmap item: "Document governance" — Status: PARTIAL (60%)
   ```

---

## Section 9: Troubleshooting

### Report Generation Fails

**Error:** `No logs found at ~/.claude/projects/`

*Solution:* Run `auto-sdlc logs --html` first to generate local reports, then `auto-sdlc report`.

**Error:** `Project path does not exist`

*Solution:* Verify the `--project-path` argument points to a valid directory with a git repo or Claude Code project.

**Error:** `Permission denied writing to output-dir`

*Solution:* Check permissions on output directory. Run `chmod u+w ./reports` to fix.

### Low Confidence Results

**Problem:** Report shows "LOW confidence" on most dimensions.

**Causes:**
- Only logs available; configs and capabilities missing
- Insufficient log history (< 1 week of data)
- Team just started using Claude Code

**Solutions:**
1. Collect config files: CLAUDE.md, AGENTS.md, .rules
2. Let logs accumulate (2+ weeks minimum)
3. Collect assessment responses from team
4. Run `auto-sdlc audit` to inventory capabilities

### Discrepancies Between Logs and Assessment

**Problem:** Logs show high /review adoption (70%), but assessment says "not yet rolled out"

**Likely cause:** Assessment was answered by someone not involved in daily development, or adoption increased since assessment.

**Solution:**
1. Clarify with team: Is adoption higher than perceived?
2. If assessment outdated, update answers
3. Note in report: "Logs suggest higher adoption than team reported"
4. Use this as coaching opportunity with assessment respondent

---

## Section 10: Contact & Support

**Auto-SDLC Project:** https://github.com/Headstorm/auto-sdlc-baseline-tooling

**Report Issues:** Open an issue on GitHub with:
- Error message or discrepancy observed
- Command used to generate report
- Output of `auto-sdlc --version`

**Request Features:** Discussion forum or GitHub issues

**Contribute:** Pull requests welcome! See CONTRIBUTING.md

---

## Appendix: Full Assessment Question Set

Complete list of 50 assessment questions organized by dimension and sub-dimension.

### CAPABILITY DIMENSION

#### AI Tool Adoption (4 questions)

1. Who decides which AI tool to use? By choice or enforcement?
2. Are licenses managed centrally? How?
3. Does the team standardize on 1-2 tools or pick individually?
4. How do you handle license renewals and tool switching?

#### Prompt & Context Engineering (5 questions)

1. Does every repo have CLAUDE.md? What does it cover?
2. Are prompt templates shared? How often are they reused?
3. How do developers load context at session start?
4. Do developers reference documentation, code, or both when writing prompts?
5. How often do prompt improvements get shared across the team?

#### Agent Configuration (4 questions)

1. How many custom slash commands exist? (/review, /commit, /plan, etc.?)
2. Are agents multi-step or single-function?
3. How are agents versioned and updated?
4. How do developers discover and learn new agents?

### INTEGRATION DIMENSION

#### CI/CD Integration (4 questions)

1. Is AI integrated into your build pipeline?
2. Which specific AI tasks run automatically? (testing, review, deployment)
3. How often does CI/CD fail due to AI output issues?
4. Is there a rollback process if AI-generated code breaks the build?

#### Ticketing & Planning (4 questions)

1. Does your team use AI to help scope work before development starts?
2. Are AI outputs used to validate requirements?
3. Is AI mentioned in your sprint planning?
4. How does AI help with task decomposition?

#### Cross-System Connectivity (4 questions)

1. Can Claude Code access your GitHub/GitLab repo directly?
2. Can Claude Code access your internal docs/wiki?
3. Can Claude Code access JIRA or your issue tracking system?
4. Are there other systems (Slack, customer data, etc.) that Claude Code could access but doesn't?

### GOVERNANCE DIMENSION

#### Quality Controls (5 questions)

1. Are AI outputs held to the same code quality standards as human code?
2. How are AI-generated tests validated?
3. Is there a sign-off process for AI code before merge?
4. How do you detect and handle hallucinations?
5. What's the rollback process if AI output is problematic?

#### Security & Compliance (4 questions)

1. How do you prevent AI from leaking proprietary data or secrets?
2. Are there data residency or privacy requirements for AI usage?
3. Is AI usage logged or auditable for compliance?
4. How are API keys and credentials managed when using AI?

#### Measurement & KPIs (4 questions)

1. Do you measure AI adoption rate? (% of team using tools)
2. Do you measure AI impact? (velocity improvement, quality metrics, cycle time reduction)
3. Are AI metrics tracked and reported regularly?
4. Do you have specific targets for AI maturity or usage?

### EXECUTION OWNERSHIP DIMENSION

#### Ways of Working (4 questions)

1. Are AI workflows documented and shared across the team?
2. Do developers follow a standard AI session pattern (setup, context, task, review)?
3. Are there internal guides or best practices for using AI?
4. How often do teams discuss AI usage and share learnings?

#### Accountability & Ownership (5 questions)

1. Is there an AI champion or designated owner on your team?
2. Who is responsible for evaluating new AI tools?
3. Who maintains custom agents and keeps them up-to-date?
4. How do you ensure consistent AI practices across the team?
5. Is there executive sponsorship for AI adoption?

#### Scalability & Knowledge Transfer (4 questions)

1. How long does it take a new developer to become productive with AI?
2. Is AI onboarding documented in your team handbook?
3. Do you have mentoring or pairing for AI skill development?
4. Can a new team member find AI answers without asking others?

---

## Final Notes

This guide is living documentation. As you generate reports, use them to:
- Understand your team's AI capability
- Identify and prioritize growth areas
- Track progress toward L3 and L4 maturity
- Share insights with leadership

Reports should inform strategy, not drive it. Use the data as evidence to support informed decision-making with your team.

For questions, see Section 9 (Troubleshooting) or contact the Auto-SDLC team on GitHub.
