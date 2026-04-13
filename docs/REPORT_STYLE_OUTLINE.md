# AI Maturity Assessment Report — Style & Outline

**Goal:** Generate PDF reports (similar to `ideal-team-vision.pdf`) that tell a holistic story of a team's or individual developer's AI maturity. The report combines quantitative signals, qualitative assessment, evidence, and actionable recommendations.

---

## Report Types

### 1. Team AI Maturity Report
**Audience:** Engineering leadership, product managers, AI champions  
**Length:** 8-12 pages  
**Purpose:** Understand the team's overall AI capability, governance, integration, and execution maturity. Identify gaps and roadmap to next level.

### 2. Individual Developer AI Maturity Profile
**Audience:** Developer themselves, manager, AI champion  
**Length:** 4-6 pages  
**Purpose:** Help developer understand their own AI usage patterns, strengths, and growth areas. Contextualize within team baseline.

---

## Team Report Structure

### Cover Page
- **Title:** "AI Maturity Assessment Report: [Team Name]"
- **Date:** Assessment date
- **Team Size:** X developers
- **Overall Maturity Level:** L1 | L2 | L2.5 | L3 | L4 (with visual indicator)
- **Assessment Sources:** Logs (X weeks), Configs, Capabilities
- **Key Stat:** "This team is at [Level] [Integrated] — [1 sentence positioning]"

---

### Executive Summary (1 page)
**What:** High-level snapshot of maturity across 4 dimensions

**Section 1: Maturity Scorecard**
```
Dimension                    Score    L2 Target   Status
─────────────────────────────────────────────────────────
1. Capability               2.2      2.0+        ✅ Met
2. Integration              1.8      2.0+        ⚠️  Close
3. Governance              2.0      2.0+        ✅ Met
4. Execution Ownership     1.5      2.0+        ❌ Gap

OVERALL TEAM MATURITY       1.9      2.0+        ⚠️  At Boundary
```

**Section 2: Key Findings (3 bullets)**
- What the team is doing well
- What's at risk or underdeveloped
- One critical opportunity

**Section 3: Next Steps**
- Top 3 actions to reach next level
- Estimated effort (1 month / 1 quarter / ongoing)

---

### Section 1: Capability Dimension (1-2 pages)

#### 1.1 AI Tool Adoption
**Current State Assessment**
- **Evidence from Logs:** X% team adoption, tools used, consistency trend
- **Evidence from Configs:** Documented tool standardization? Licensing managed?
- **Evidence from Capabilities:** Infrastructure for multi-tool orchestration?

**Maturity Statement**
- Current level: L1 | L2 | L3 | L4
- Rubric match: [Quote from rubric showing why this level]

**Assessment Question Responses**
- Q: "Who decides which AI tool to use?" → "[Answer from team]"
- Q: "Are licenses managed centrally?" → "[Answer]"
- Q: "Is tool choice standardized or individual?" → "[Answer]"

**Evidence Summary**
```
Finding: Team standardized on Claude Code + Copilot
├── Logs: 92% of developers use Claude Code
├── Configs: Tool approval documented in settings.json
├── Capabilities: No tool switching agents (not yet L3)
└── Assessment: "Tool selection centrally enforced"
```

**Gap Analysis**
- What's missing for next level?
- Example: "To reach L3: Implement multi-agent toolchain with dynamic tool selection based on task type"

**Supporting Data**
- Chart: Tool adoption trend over time (from logs)
- Table: Tool usage by developer (shows consistency)
- Evidence: Screenshot or quote from CLAUDE.md or settings.json

---

#### 1.2 Prompt & Context Engineering
[Same structure as 1.1 above]

**Assessment Question Responses**
- Q: "Does every repo have CLAUDE.md?" → [Answer]
- Q: "What does CLAUDE.md cover?" → [Answer: architecture, conventions, gotchas, domain context]
- Q: "How often do developers load CLAUDE.md at session start?" → [Answer from log analysis]

**Evidence Summary**
```
Finding: Shared context strategy emerging, incomplete rollout
├── Logs: 67% of session starts load CLAUDE.md (target: >90%)
├── Configs: CLAUDE.md exists in 15/22 repos (68% coverage)
│  - Quality ranges from minimal to comprehensive
│  - Last updates: last month (Alice), 3 months ago (Bob)
├── Capabilities: Shared prompt library in 1 repo (not team-wide)
└── Assessment: "Practices partially documented; execution spotty"
```

---

#### 1.3 Agent Configuration
[Same structure]

**Assessment Question Responses**
- Q: "How many custom slash commands exist?" → [Count: /review, /commit, /plan, /test]
- Q: "Are agents multi-step or single-function?" → [Answer]
- Q: "Who maintains agent code?" → [Answer]

**Evidence Summary**
```
Finding: Foundation-level agent infrastructure
├── Logs: /review in 85% of PR sessions, /plan in 32% of feature work
├── Configs: 3 agents defined in AGENTS.md (basic error handling)
├── Capabilities: /review, /commit, /plan skills deployed; test generation WIP
└── Assessment: "Basic agents working; orchestration not yet in place"
```

---

### Section 2: Integration Dimension (1-2 pages)

#### 2.1 CI/CD Integration
**Current State Assessment**
- Evidence from Logs: /review adoption rate, test generation frequency
- Evidence from Configs: CI/CD gates documented in .rules?
- Evidence from Capabilities: /lint, /test skills active?

**Assessment Question Responses**
- Q: "Does every PR get AI review before human review?" → [Answer: 85% today, target 100%]
- Q: "Are test suites generated automatically?" → [Answer: 40% auto-generated, 60% manual]

**Evidence Summary**
```
Finding: AI review layer established; testing incomplete
├── Logs: /review in 85% of sessions (strong adoption)
├── Configs: PR review checklist includes AI steps
├── Capabilities: /review and /lint skills active; /test_gen skill underutilized
└── Assessment: "CI layer active but not comprehensive"
```

---

#### 2.2 Ticketing & Planning
[Similar structure]

---

#### 2.3 Cross-System Connectivity
[Similar structure]

**Evidence Summary**
```
Finding: Limited integration maturity
├── Logs: JIRA lookups in 12% of sessions (target: >40%)
├── Configs: 1 MCP integration configured (GitHub); JIRA pending
├── Capabilities: GitHub MCP active; Slack, Confluence not yet wired
└── Assessment: "Starting point; 4+ integrations possible"
```

---

### Section 3: Governance Dimension (1-2 pages)

#### 3.1 Quality Controls
#### 3.2 Security & Compliance
#### 3.3 Measurement & KPIs

[Each follows same structure: logs + configs + capabilities evidence + assessment questions + gap analysis]

---

### Section 4: Execution Ownership Dimension (1-2 pages)

#### 4.1 Ways of Working
**Assessment Question Responses**
- Q: "Is there a documented 'AI Ways of Working' guide?" → [Answer: Yes, in team wiki, last updated March]
- Q: "What does it cover?" → [Answer: session startup, plan mode usage, PR submission, review workflow]
- Q: "Is it followed consistently?" → [Answer from logs: 78% of sessions follow documented protocol]

**Evidence Summary**
```
Finding: Documented; execution uneven
├── Logs: 78% session start follows documented protocol (plan mode + context loading)
├── Configs: "AI Ways of Working" doc exists, last updated March 8
├── Capabilities: Workflow automation built into /plan, /commit, /review skills
└── Assessment: "L2 achieved; opportunity for consistency training"
```

---

#### 4.2 Accountability & Ownership
**Assessment Question Responses**
- Q: "Who is the AI champion?" → [Answer: Alice, backend tech lead]
- Q: "What are their explicit responsibilities?" → [Answer: CLAUDE.md maintenance, new dev onboarding, prompt library curation]
- Q: "Is this documented?" → [Answer: Partially — informal, not explicit in team charter]

**Evidence Summary**
```
Finding: Champion exists; responsibilities informal
├── Logs: Alice shows consistent mentorship patterns (high prompt quality, /review usage)
│  - CLAUDE.md authored/maintained by Alice (git blame)
│  - New dev onboarding traces back to Alice interactions
├── Configs: Responsibilities not documented in AGENTS.md or team handbook
├── Capabilities: Alice's skills curated; no succession plan
└── Assessment: "L2 soft ownership; L2.5 if formalized"
```

**Recommendation:** Formalize Alice's role. Document responsibilities in team handbook or AGENTS.md. Identify successor.

---

#### 4.3 Scalability & Knowledge Transfer
**Assessment Question Responses**
- Q: "What happens when a new developer joins?" → [Answer: Alice onboards them, typically 2-3 week ramp]
- Q: "What materials are available?" → [Answer: CLAUDE.md, prompt examples, pair session on day 1]
- Q: "How fast do they reach baseline productivity?" → [Answer from logs: 2-3 weeks to match team avg prompt quality]

**Evidence Summary**
```
Finding: Sustainable onboarding; could be faster
├── Logs: New dev Bob (joined 6 weeks ago) now at team baseline (quality 72 vs. team avg 73)
├── Configs: CLAUDE.md + prompt library used in onboarding
├── Capabilities: /plan, /review skills available to all; documentation of playbooks partial
└── Assessment: "L2 process; L2.5 if playbooks documented"
```

---

### Section 5: Synthesis & Roadmap (1-2 pages)

#### 5.1 Maturity Narrative
**What's Working Well:**
- Strong /review adoption (85%)
- Clear AI champion and mentorship patterns
- CLAUDE.md in most repos, actively maintained
- Documented "Ways of Working"

**What's at Risk:**
- Incomplete integration (only 1 of 4 needed MCP servers)
- Governance underdocumented (policy exists informally, not written)
- New developer ramp time longer than it should be (2-3 weeks vs. L3 target of 1 week)
- Testing infrastructure underutilized

**Assessment:**
This team is at the **L2–L2.5 boundary**. You have:
- ✅ Intentional practices (documented ways of working, champion ownership)
- ✅ Infrastructure investment (/review, /plan, /commit skills)
- ✅ Cross-team consistency (CLAUDE.md culture, shared standards)

But you're missing:
- ❌ Complete integration (4 out of 4 JIRA, Slack, Confluence, docs)
- ❌ Formalized governance (policy in writing, escalation paths explicit)
- ❌ Optimized onboarding (2-3 weeks vs. 1 week)

**Sustainability Assessment:**
You are **sustainable at L2**, but at risk if:
- Alice (champion) leaves without documented successor plan
- Integrations remain incomplete (creates context gaps)
- Policy stays informal (compliance/audit exposure)

---

#### 5.2 Roadmap to L3 (Agentic)

**Immediate (Next 1 month):**
1. **Formalize Accountability:**
   - Document Alice's role and responsibilities in team handbook
   - Identify Bob as successor candidate; pair on CLAUDE.md maintenance
   - Add AI ownership to Alice's job description / OKRs

2. **Write Security & Compliance Policy:**
   - Codify data handling rules currently enforced informally
   - Document approval gates and escalation paths
   - Add to CLAUDE.md "Governance" section

**Near-term (Q2 - 2-3 months):**
3. **Complete Integration:**
   - Deploy JIRA MCP (already licensed; Alice has prototype)
   - Deploy Slack MCP (for team coordination signals)
   - Add Confluence MCP (documentation federation)

4. **Accelerate Onboarding:**
   - Convert CLAUDE.md wisdom into playbooks (bug investigation, PR creation, test writing)
   - Document workflow variations by project (monorepo patterns)
   - Target: new dev reaches baseline in 1 week, not 3

**Medium-term (Q3 - ongoing):**
5. **Multi-Agent Orchestration:**
   - Design agents for multi-phase workflows (design → code → test → deploy)
   - Implement agent composition (agents calling other agents)
   - Add workflow optimization based on cycle time metrics

**Estimated Effort:**
- Formalize accountability: 4-8 hours (documentation)
- Write security policy: 8-16 hours (team interviews, documentation)
- Deploy 3 MCP integrations: 20-30 hours (engineering)
- Create onboarding playbooks: 12-20 hours (Alice + team knowledge capture)
- Multi-agent orchestration: 40-60 hours (engineering + testing)

**Total:** ~100 hours of work, distributed over 3-6 months. Doable in parallel.

---

#### 5.3 Success Metrics

**To reach L3, you need:**
- ✅ 4/4 MCP integrations active (currently 1/4)
- ✅ Security policy documented in writing (currently implicit)
- ✅ Successor onboarded to champion role (currently single point of failure)
- ✅ Multi-step agents deployed for 2+ workflows (currently single-step)
- ✅ New developer ramp time ≤1 week (currently 2-3 weeks)

**Monitoring:**
- Track integration adoption monthly (are devs actually using JIRA MCP? Slack?)
- Survey team on policy clarity quarterly
- Measure new dev ramp time per hire (should trend down)
- Count active multi-step agent workflows (target: 3+ by Q3)

---

### Appendices

#### A. Detailed Evidence Tables
- Tool adoption by developer
- Session patterns over time
- CLAUDE.md coverage by repo (with quality ratings)
- Assessment question responses (full transcripts)

#### B. Config File Excerpts
- CLAUDE.md sections (architecture, conventions)
- AGENTS.md agent definitions
- .rules quality gates
- settings.json approved tools

#### C. Capability Inventory
- List of all custom skills (/review, /commit, /plan, etc.)
- MCP integrations declared vs. active
- Plugin list and usage metrics

#### D. Individual Developer Profiles (Summary)
- Alice: L2.5 (strong champion patterns)
- Bob: L2 (baseline, high potential)
- Carol: L1.5 (lower adoption, technical constraint)
- [etc. — 1 paragraph per dev]

---

---

## Individual Developer Profile Structure

**Audience:** Developer, manager, AI champion  
**Length:** 4-6 pages  
**Purpose:** Help developer understand their AI usage, growth, and fit with team baseline

### Cover Page
- **Name:** Developer name
- **Role:** Backend engineer, frontend engineer, etc.
- **Individual Maturity Level:** L1 | L2 | L3 | L4
- **Team Baseline:** L2 (Integrated)
- **Status:** "Aligned with team" | "Exceeds team" | "Below team, improving" | "Below team, at risk"

---

### Section 1: Usage Profile (1 page)

**How They Use AI:**
- Sessions per day: X (team avg: Y)
- Average session length: X minutes (team avg: Y)
- Prompt quality score: X/100 (team avg: Y)
- Top skills used: /review (45%), /plan (22%), /commit (18%), other (15%)
- Tool consistency: 99% Claude Code (team avg: 92%)

**Context Reuse:**
- CLAUDE.md loading: 78% of sessions (team avg: 67%)
- File path references: 58% of prompts (team avg: 52%)
- Architecture context references: 32% of prompts (team avg: 27%)

**Pattern Insight:**
"Bob is a power user. He loads context consistently, writes detailed prompts, and uses plan mode frequently. His prompt quality (76/100) exceeds the team average (73/100). He's showing characteristics of an L2–L2.5 developer."

---

### Section 2: Strengths & Gaps (1 page)

**Strengths:**
- ✅ High prompt quality (76 vs. 73 team avg)
- ✅ Consistent CLAUDE.md loading (78% vs. 67% team avg)
- ✅ Active use of plan mode (28% vs. 19% team avg)

**Growth Opportunities:**
- ⚠️ Low /review adoption (22% vs. 85% team avg) — Why? "Prefers manual review"
- ⚠️ Rare cross-system context (JIRA lookups in 8% of sessions vs. 18% team avg)
- ⚠️ Low error recovery patterns (typically restarts session vs. iterative debugging)

**Team Context:**
Your profile shows **L2 integration** — you're aligned with team practices. But there are opportunities:
- Embracing /review would strengthen code quality (team best practice)
- Using JIRA MCP would ground prompts in ticket context (Alice does this)
- More iterative debugging (rather than session restarts) would reduce cycle time

---

### Section 3: Growth Trajectory (1 page)

**Progress Over Time (Last 6 weeks):**
- Prompt quality trend: Steady at 75–76 (good consistency)
- CLAUDE.md loading: Increased from 65% → 78% (improvement)
- /plan adoption: Increased from 20% → 28% (growth in structured thinking)
- /review adoption: Flat at 22% (opportunity)

**Insight:**
"Bob is adopting team practices steadily. The recent increase in CLAUDE.md loading and plan mode usage suggests he's responding to team norms. If /review adoption increases next month, he'll be solidly L2."

---

### Section 4: Comparison to Team & Progression (1 page)

**Maturity Dimension Scores:**

| Dimension | Individual | Team Avg | Status |
|-----------|-----------|----------|--------|
| Prompting Sophistication | 2.2 | 2.0 | ✅ Exceeds |
| Tooling Adoption | 2.0 | 2.0 | ✅ Aligned |
| Usage Frequency | 2.1 | 1.9 | ✅ Exceeds |
| Session Depth | 2.3 | 2.0 | ✅ Exceeds |
| Context Efficiency | 1.8 | 1.9 | ⚠️ Slightly below |

**Overall Individual Maturity:** L2 (Integrated)  
**Progression Path to L3:**
1. Increase /review adoption (move from manual to automated review)
2. Embrace JIRA MCP for ticket context (like Alice)
3. Practice iterative debugging rather than session restarts
4. Document one team playbook (contribute to knowledge base)

**Estimated Timeline:** 2-3 months with deliberate practice

---

### Section 5: Recommendations (1 page)

**For Bob (Developer):**
1. **Shadow Alice for 1 session** — See how she uses JIRA MCP and structured review
2. **Try /review on next 3 PRs** — Commit to using AI review before pushing, see if it catches issues
3. **Document one playbook** — Write up your "bug investigation workflow" for the team
4. **Join Alice's weekly office hours** — Discuss growth, get feedback on practice

**For Bob's Manager:**
- Bob is tracking well on team norms; minimal coaching needed
- Growth areas are self-correctable with awareness
- Consider assigning him a peer pairing with Alice to accelerate learning

**For the AI Champion (Alice):**
- Bob is a good mentorship candidate; pair him on knowledge artifact maintenance
- His high prompt quality + context loading suggests he could contribute to CLAUDE.md

---

### Appendix: Detailed Metrics

- Session logs (last 4 weeks): [table of sessions with duration, tool usage, quality scores]
- Prompt quality breakdown: [distribution of scores, top-quality prompts, low-quality prompts]
- Skill usage timeline: [chart showing /review, /plan, /commit adoption over time]

---

---

## Design & Visual Style

**Similar to ideal-team-vision.pdf:**
- Professional serif font for headers (Georgia, Garamond)
- Clean sans-serif for body (Helvetica, Inter)
- Color palette: Navy blue (headers), light gray (background), green (success/positive), orange (caution), red (gaps)
- Sidebar callouts for key metrics or recommendations
- Charts and tables embedded (not screenshots)
- Whitespace and breathing room (not dense)
- Section dividers with icons (capability, integration, governance, ownership)
- PDF should be printable and screen-readable

**Tone:**
- Professional but conversational (like ideal-team-vision.pdf)
- Specific and concrete (quote actual evidence, don't generalize)
- Balanced (celebrate strengths, identify gaps objectively)
- Actionable (every gap includes a recommendation and effort estimate)

---

## Report Generation Workflow

1. **Assessment Phase:** Collect logs, configs, capabilities; conduct interviews
2. **Analysis Phase:** Score each dimension; identify gaps and strengths
3. **Synthesis Phase:** Write narrative that triangulates three data sources
4. **Report Gen Phase:** Template-driven PDF generation with charts/tables
5. **Distribution:** Email to team lead + individual profiles to developers
6. **Follow-up:** Quarterly check-ins to measure progress on roadmap

---

## Success Criteria for Reports

✅ **Specific:** References actual data (log metrics, config excerpts, capability inventories)  
✅ **Actionable:** Every gap has a recommended step with effort estimate  
✅ **Balanced:** Celebrates strengths equally with identifying gaps  
✅ **Triangulated:** Combines logs + configs + capabilities (not just one source)  
✅ **Contextual:** Positions individual/team against rubric and each other  
✅ **Progressive:** Shows roadmap to next maturity level  
✅ **Readable:** Professional design, clear structure, no jargon without explanation  
