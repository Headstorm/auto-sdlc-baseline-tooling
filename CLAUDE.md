# Auto-SDLC: AI Maturity Mapping

## Vision

**Generate professional PDF assessment reports** that measure team AI maturity against the **Ideal Development Team** framework (4 dimensions, 12 sub-dimensions, L1-L4 scale).

The goal is to help teams understand:
- ✅ Where are we? (Current maturity with evidence)
- ✅ Why? (What behaviors, practices, infrastructure support this level)
- ✅ What's working? (Strengths to build on)
- ✅ What's at risk? (Gaps and vulnerabilities)
- ✅ How do we progress? (Specific steps to next level with effort estimates)

**Report Types:**
1. **Team AI Maturity Report** (8-12 pages) — Leadership view of team capability, governance, integration, ownership
2. **Individual Developer Profile** (4-6 pages) — Developer's usage patterns, strengths, growth areas, fit with team baseline

**See `/docs/REPORT_STYLE_OUTLINE.md` for complete report structure, samples, and design.**

---

## The 4 Dimensions & 12 Sub-Dimensions

| # | Dimension | Sub-Dimension | What It Measures |
|---|-----------|---|---|
| **1** | **Capability** | AI Tool Adoption | Are tools standardized or scattered? |
| **2** | | Prompt & Context Engineering | Do teams share context or rebuild from scratch? |
| **3** | | Agent Configuration | Are custom agents configured or using out-of-the-box? |
| **4** | **Integration** | CI/CD Integration | Is AI integrated into the build pipeline? |
| **5** | | Ticketing & Planning | Is AI used to validate work before starting? |
| **6** | | Cross-System Connectivity | Can AI access repos, docs, JIRA, Slack, etc.? |
| **7** | **Governance** | Quality Controls | Are AI outputs held to code quality standards? |
| **8** | | Security & Compliance | Is AI usage governed and auditable? |
| **9** | | Measurement & KPIs | Are metrics tracked to show AI impact? |
| **10** | **Execution Ownership** | Ways of Working | Are AI workflows documented and shared? |
| **11** | | Accountability & Ownership | Is AI adoption owned by a specific person/team? |
| **12** | | Scalability & Knowledge Transfer | Can new developers be productive with AI quickly? |

**For detailed L1-L4 definitions:** See `AI_Maturity_Scorecard.xlsx` (reference file from ideal-team-vision.pdf context).

---

## Three Data Sources for Assessment

The tool triangulates evidence from **three independent sources**, not just logs:

### 1. **Logs** (Behavioral Evidence)
What developers actually do: session frequency, prompt quality, tool usage, /commands, error recovery, data handling.

### 2. **Configs** (Documented Practices)
What the team intends: CLAUDE.md (architecture, conventions), AGENTS.md (agent definitions), .rules (standards, gates), settings.json (tool approval, compliance).

### 3. **Capabilities** (Built Infrastructure)
What the team has constructed: Custom skills (/review, /commit, /plan), Agents, MCP integrations, Plugins.

**Why three sources matter:**

| Evidence | Team A | Team B |
|----------|--------|--------|
| **Logs** | 80% /review adoption | 80% /review adoption |
| **Configs** | No quality policy | Quality policy in CLAUDE.md |
| **Capabilities** | No /review skill | /review skill exists |
| **Assessment** | ⚠️ **L1** — Unsustainable | ✅ **L2** — Intentional, documented |

Same behavior, different maturity. Only holistic assessment works.

---

## Holistic Assessment Philosophy

**This tool should make assessment easier, not replace it.**

**Do NOT:** Auto-score from logs ("72% adoption = L2")  
**DO:** Use logs as evidence, ask questions, check artifacts, make judgment calls

A good assessment:
1. **Shows evidence:** "Your logs show 72% Claude Code adoption"
2. **Asks questions:** "Is that by choice or enforcement? How are tools managed?"
3. **Checks artifacts:** "Show me your tool selection policy or CLAUDE.md"
4. **Makes a judgment call:** "Based on all three, you're L2 Integrated"

The assessor is the expert. The tool is a facilitator.

---

## Log-Based Signals (One-Source Reference)

If only logs are available, these dimensions have strong behavioral signals:

| Dimension | Log Signal | Confidence |
|-----------|-----------|------------|
| **AI Tool Adoption** | Tool usage patterns, consistency across team | **High** |
| **Prompt & Context Engineering** | Prompt quality score, file/line ref frequency | **High** |
| **Agent Configuration** | Skill invocation ratio, tool diversity | **High** |
| **CI/CD Integration** | /review adoption, test generation frequency | **High** |
| **Quality Controls** | /review usage, test patterns, error recovery | **High** |
| **Usage Frequency** | Sessions per day | **High** |
| **Session Depth** | Messages per session | **High** |
| **Ticketing & Planning** | JIRA/issue references early in sessions | **Medium** |
| **Cross-System Connectivity** | MCP tool invocation frequency | **Medium** |
| **Measurement & KPIs** | Adoption rate trends, cycle time | **Medium** |
| **Ways of Working** | Session opening patterns, plan mode usage | **Medium** |
| **Security & Compliance** | PII/data handling patterns | **Low** |
| **Accountability & Ownership** | Champion candidate patterns (git blame, consistency) | **Low** |
| **Scalability & Knowledge Transfer** | New dev ramp time | **Low** |

**Strategy:** Score conservatively. If data missing → estimate one level lower.

---

## Scoring with Incomplete Data

**Reality:** Early deployments often have only logs. Make educated guesses, flag limitations.

**Example comparison:**

**Logs-Only Estimate:** L1.3 ± 0.5 (low confidence)
- High adoption visible in logs
- But no visibility to governance, documentation, infrastructure

**Full Data (logs + configs + capabilities):** L1.8 ± 0.3 (high confidence)
- Adoption confirmed + documented + infrastructure built
- Major gaps identified; scores refined

**In reports, always include:**
```
ASSESSMENT DATA SOURCES
├── Logs: ✅ 6 weeks of session data
├── Configs: ⚠️ Partial (CLAUDE.md found; .rules not found)
└── Capabilities: ❌ Not collected (pending)

CONFIDENCE BY DIMENSION
├── High (visible in logs): Quality Controls, Usage Frequency, Tool Adoption
├── Medium (partial configs): Governance, Context Engineering
└── Low (no data): Accountability & Ownership, Ways of Working

NEXT STEPS
1. Share .rules and AGENTS.md files
2. Inventory deployed skills and MCP integrations
3. Brief interview with AI champion (1 hour)
```

This transparency builds trust and drives next-step data collection.

---

## Assessment Questions Reference

See **Appendix: Assessment Questions by Dimension** below for the full 50 questions organized by dimension.

These questions are asked during team interviews to verify/refine log-based signals and assess dimensions invisible to logs (governance, ownership, practices).

---

## Implementation Roadmap

All phases feed directly into the PDF report:

### Phase 1: Extract Evidence (All Three Sources)
**From Logs:** Tool usage, /command adoption, context loading, MCP invocations, test generation, data handling  
**From Configs:** CLAUDE.md presence/quality, AGENTS.md sophistication, .rules enforcement, settings.json configuration  
**From Capabilities:** Custom skills count, agents complexity, MCP integrations active, plugin inventory

**Output:** Evidence dashboard per dimension (supporting data for each source)

### Phase 2: Assessment Interview + Question Responses
Show triangulated evidence to team; ask the 50 assessment questions (organized by dimension).

**Output:** Team answers recorded; contradictions flagged for investigation

### Phase 3: Artifact Verification
Check for tangible evidence: CLAUDE.md freshness, AGENTS.md detail, .rules enforcement, capability maintenance.

**Output:** Artifact checklist verifying practices are documented and current

### Phase 4: Synthesis (Human-Driven)
For each dimension:
1. Evidence from logs
2. Evidence from configs/capabilities
3. Answers to assessment questions
4. Make judgment call on L1-L4 level

**Output:** Maturity score per dimension with confidence; roadmap to next level

### Phase 5: Deep Analysis
Parse configs for sophistication signals; analyze maintenance patterns (git blame, freshness dates).

**Output:** Detailed metrics and capability inventory for report appendices

---

## What This Is & Isn't

✅ **IS:**
- A structured framework (4 dimensions, 12 sub-dimensions, L1-L4 rubric)
- An evidence facilitator (surface log patterns + config/capability visibility)
- A gap mapper (triangulate three sources; flag misalignments)
- A roadmap generator (steps to next level with effort estimates)

❌ **IS NOT:**
- An auto-scorer (don't return "L2.3 overall maturity")
- A replacement for interviews (governance invisible without talking to team)
- A one-time assessment (data gets richer; confidence improves over time)
- Unbiased (rubric embeds assumptions about "good" AI practices)

---

## Mapping Between Existing Auto-SDLC Metrics & Maturity Dimensions

| Auto-SDLC Metric | Feeds Into Dimension | Range | L2 Threshold |
|---|---|---|---|
| Avg prompt quality score (0-100) | Prompt & Context Engineering | 60-75 | 70+ |
| Skill invocation ratio (%) | Agent Configuration | 20-30% | 20%+ |
| Sessions per day | Ways of Working (engagement) | 0.5-0.8 | Trending ↑ |
| Messages per session | Session Depth + Ways of Working | 12-20 | 15+ |
| Cache hit ratio | Security & Compliance (reuse patterns) | 30-50% | 30%+ |
| Tool diversity | Cross-System Connectivity | 1-2 tools | 1-2 tools |
| /review adoption (%) | Quality Controls | 40-85% | 80%+ |
| Tool consistency % | AI Tool Adoption | 70-99% | 70%+ |
| New dev ramp time (weeks) | Scalability & Knowledge Transfer | 2-4 weeks | 1-3 weeks |

---

## Goals for the PDF Report

Every implementation phase feeds into reports that answer:

**For Leaders:** What's our team's AI maturity? Where should we invest? What's the roadmap?  
**For Developers:** How does my AI usage compare to the team? Where can I grow?  
**For Champions:** What gaps should I focus on? What's the next priority?

The report is **not a dashboard or auto-score.** It's a narrative document that synthesizes evidence, tells a story, and drives strategic decisions.

---

---

## Appendix: Assessment Questions by Dimension

### SECTION 1: Capability (AI Tools, Context, Agents)

**AI Tool Adoption:**
- Who decides which AI tool to use? By choice or enforcement?
- Are licenses managed centrally? How?
- Does the team standardize on 1-2 tools or pick individually?

**Prompt & Context Engineering:**
- Does every repo have CLAUDE.md? What does it cover?
- Are prompt templates shared? How often reused?
- How do developers load context at session start?

**Agent Configuration:**
- How many custom slash commands exist? (/review, /commit, /plan, etc.?)
- Are agents multi-step or single-function?
- Who maintains agent code?

---

### SECTION 2: Integration (CI/CD, Tickets, Connectivity)

**CI/CD Integration:**
- Does every PR get AI review before human review?
- Are test suites generated automatically or manually?
- How many AI review layers exist?

**Ticketing & Planning:**
- Do developers validate ticket quality with AI before starting?
- Are tickets structured with sufficient context for AI and humans?
- Does AI enrich issues with acceptance criteria or edge cases?

**Cross-System Connectivity:**
- Is AI connected to Git, JIRA, Slack, Confluence, docs?
- How many MCP integrations are active? Which are planned?
- Do developers pull context from multiple systems per session?

---

### SECTION 3: Governance (Quality, Security, Metrics)

**Quality Controls:**
- Is there a documented PR review checklist with AI-specific items?
- Are AI-generated changes held to the same quality bar as human code?
- How are edge cases and test coverage validated?

**Security & Compliance:**
- Is there a formal AI usage policy? Data handling rules?
- What restrictions exist on what can be sent to AI?
- Are AI actions logged and auditable?

**Measurement & KPIs:**
- What metrics do you track for AI adoption? (% of team, sessions/day, cycle time)
- Is AI impact measured? Pre/post baselines? Quantified or anecdotal?

---

### SECTION 4: Execution Ownership (Ways, Accountability, Scalability)

**Ways of Working:**
- Is there a documented "AI Ways of Working" page?
- What's the standard protocol for starting an AI session? (Load CLAUDE.md? Context?)
- When do developers use plan mode vs. direct generation?

**Accountability & Ownership:**
- Is there a designated AI champion? What are their responsibilities?
- Who owns CLAUDE.md maintenance? Prompt library? Onboarding?
- Are AI KPIs tied to team performance reviews?

**Scalability & Knowledge Transfer:**
- What AI onboarding materials do new developers receive?
- Is there a prompt library or playbook for common tasks?
- How quickly do new team members become productive with AI?

---

### SECTION 5: Value Realization (KPIs, Business Impact)

**Baseline Measurement:**
- Do you track DORA metrics? (PR cycle time, deployment frequency, change failure rate)
- Are these metrics trusted and acted upon?

**AI Impact Measurement:**
- Have you measured AI's impact? Pre/post baselines?
- Is improvement quantified or anecdotal?

**Business Alignment:**
- Is AI tied to business outcomes? (EBITDA, revenue, cost reduction, speed)

---
