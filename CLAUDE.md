# Auto-SDLC: AI Maturity Mapping

## Vision

Map Claude Code session logs to the **Ideal Development Team** framework (4 dimensions, 12 sub-dimensions, L1-L4 scale) to measure team AI maturity beyond behavioral metrics.

Current state: We measure *how developers use Claude Code* (prompt quality, tool adoption, session depth, etc.)

Target state: We measure *what capabilities the team has built* using AI, mapped to business outcomes and team practices.

---

## The 4 Base Dimensions

### 1. Capability
How equipped is the team with AI tools and skills?

**Sub-dimensions:**
- **AI Tool Adoption** — Standardized tools, licenses managed, no fragmentation across Claude/Cursor/Gemini
- **Prompt & Context Engineering** — CLAUDE.md in repos, shared templates, context reuse
- **Agent Configuration** — Custom skills, slash commands, Copilot instruction sets

**L2 Requirement:** Team standardized on Claude Code + Copilot; CLAUDE.md in every active repo; at least 1 custom skill

---

### 2. Integration
How deeply is AI woven into the development workflow?

**Sub-dimensions:**
- **CI/CD Integration** — AI review layers (pre-push checks, PR-level review), code validation
- **Ticketing & Planning** — AI used to validate/refine tickets before work starts
- **Cross-System Connectivity** — AI reads from repos, docs, JIRA, GitHub, Slack (2+ MCP servers active)

**L2 Requirement:** Every PR passes 2 AI review layers; AI assists with ticket quality; 2+ integrations active

---

### 3. Governance
How does the team manage quality, security, and compliance with AI?

**Sub-dimensions:**
- **Quality Controls** — Linting + checks on AI code; PR review checklists with AI-specific items
- **Security & Compliance** — Documented AI usage policy; data handling rules; approved tools
- **Measurement & KPIs** — Adoption rate, PR review time (before/after AI), cycle time tracked

**L2 Requirement:** Documented PR review checklist; AI usage policy exists; adoption/timing metrics tracked

---

### 4. Execution Ownership
How does the team organize knowledge, accountability, and growth around AI?

**Sub-dimensions:**
- **Ways of Working** — "AI Ways of Working" doc exists; how to start sessions, when to use plan mode, PR submission expectations
- **Accountability & Ownership** — Named AI champion; explicit responsibilities (CLAUDE.md maintenance, prompt curation, onboarding)
- **Scalability & Knowledge Transfer** — Onboarding includes AI workflow guide; prompt library maintained; knowledge in artifacts, not heads

**L2 Requirement:** Documented AI ways of working; AI champion assigned; onboarding materials include AI workflow

---

## Mapping Claude Code Logs to These 12 Categories

### The Challenge

Claude Code logs show:
- Prompt quality scores (0-100)
- Tool invocations (counts, types)
- Session depth (messages per session)
- Usage frequency (sessions per day)

But they don't directly show:
- Whether the team has a CLAUDE.md strategy → **Prompt & Context Engineering**
- Whether they use /review before pushing → **Quality Controls**
- Whether multiple team members are using AI → **AI Tool Adoption**
- Whether they have an AI champion → **Accountability & Ownership**
- Whether there's a documented policy → **Security & Compliance**

### Inference Strategy

We can infer maturity from behavioral patterns:

| Dimension | Signal from Logs | Example |
|-----------|------------------|---------|
| **AI Tool Adoption** | Multiple developers using Claude Code consistently | >70% of team, >0.5 sessions/day avg |
| **Prompt & Context Engineering** | High avg prompt quality (70+), file/line refs frequent | Context-aware prompts indicate CLAUDE.md use |
| **Agent Configuration** | Frequent skill invocations, tool diversity | >20% of messages use skills (custom or built-in) |
| **CI/CD Integration** | Use of /review, /commit, integration tool invocations | /review before every push; MCP tool usage |
| **Ticketing & Planning** | Early-session file references to JIRA/tickets; planning patterns | Prompts reference tickets, architecture docs |
| **Cross-System Connectivity** | MCP tool invocation frequency and diversity | GitHub, JIRA, Confluence tool calls detected |
| **Quality Controls** | /review usage, test writing patterns, error recovery | Every PR gets /review; tests generated with prompts |
| **Security & Compliance** | Consistency in data handling, token usage patterns | No PII in prompts; consistent cache usage |
| **Measurement & KPIs** | Adoption rate trends, cycle time inference | Velocity trend per developer, tool adoption >80% |
| **Ways of Working** | Session opening patterns, plan mode usage | Plan mode for >50% of non-trivial tasks |
| **Accountability & Ownership** | Consistency in prompt patterns, CLAUDE.md updates | High prompt sophistication suggests champion guidance |
| **Scalability & Knowledge Transfer** | Onboarding velocity, new dev ramp time | New team members hit target adoption within 2 weeks |

---

## The 12 Sub-Dimensions: Full L1-L4 Rubric

### 1. AI Tool Adoption
**What it measures:** Are tools standardized, or scattered?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Assisted** | Ad-hoc use of copilots; no org-wide tool strategy | Who decides which AI tool to use? Is choice individual or enforced? Are licenses managed? | Multiple different tools in use; inconsistent tool choices per session; low adoption density |
| **L2: Integrated** | Standardized on 1–2 AI tools across the team; licenses managed | Is the team standardized on a single primary tool (e.g., Claude Code + Copilot)? Are licenses managed centrally? | >70% of team uses same tool(s); consistent tool patterns; managed licensing visible |
| **L3: Agentic** | Multi-agent toolchains configured per workflow; prompt libraries maintained | Do you have orchestration between multiple agents or tools? Are prompt templates curated? | Orchestrated tool calls; specialized agents per task; documented prompt templates in use |
| **L4: Autonomous** | Agents select and orchestrate tools autonomously based on task context; consistently adhere to standards | Do agents choose tools dynamically? Are coding standards enforced automatically? | Agents switch tools based on task; zero manual tool selection; style/convention consistency perfect |

---

### 2. Prompt & Context Engineering
**What it measures:** Do teams share context, or rebuild from scratch?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Assisted** | Individual engineers write one-off prompts; no sharing | Do developers write prompts from scratch each time? Is there shared context? | High variation in prompt quality; no file path references; vague prompts; no architecture context |
| **L2: Integrated** | Teams share prompt templates; some reuse; implementation standards at repo level | Does your repo have CLAUDE.md? Are prompts templates shared? | Consistent prompt structure across team; file/line refs in >60% of prompts; CLAUDE.md evidence |
| **L3: Agentic** | Structured artifacts (architecture docs, product files, conventions) feed agents automatically | Does AI access structured context (docs, ADRs, design docs) automatically per session? | Agents load context automatically; artifact references in 80%+ of prompts; low prompt-writing overhead |
| **L4: Autonomous** | Agents maintain and update their own context documents; self-improving prompt chains (APO) | Do agents improve their own prompts or context based on outcomes? Is there feedback learning? | Agents refine prompts over sessions; context auto-updates; self-generated prompt improvements detected |

---

### 3. Agent Configuration
**What it measures:** Are custom agents configured, or using tools out-of-the-box?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Assisted** | No custom agents; using tools out-of-the-box only | Are you using defaults, or customized setups? | No custom skills; no /commands used; default Copilot settings |
| **L2: Integrated** | Basic slash commands or custom instructions configured | Do you have 1+ custom slash commands (e.g., /review, /commit)? Custom Copilot instructions? | /review, /commit, /plan usage detected; custom instructions in profiles; 20-30% skill invocation |
| **L3: Agentic** | Multi-step agents with defined workflows, error handling, validation loops | Do you have agents that orchestrate multiple steps? Error recovery? | Multi-step task execution; error handling patterns; validation loops; specialized agents per task |
| **L4: Autonomous** | Agents compose and decompose tasks, spawn sub-agents, self-correct within guardrails | Do agents spawn new agents? Decompose complex work autonomously? | Sub-agent orchestration; dynamic task decomposition; self-correction loops; >4 steps per task |

---

### 4. CI/CD Integration
**What it measures:** Is AI integrated into the build pipeline?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Assisted** | AI not connected to CI/CD; manual copy-paste of outputs | Is AI output manually copy-pasted to CI? Or is there automated integration? | No CI/CD tool invocations; /review not used; manual merges |
| **L2: Integrated** | AI-generated code goes through standard PR review; basic checks automated | Does every PR get /review before push? Are linting/test checks automated? | /review in >80% of sessions; CI/CD tool invocations present; test generation visible |
| **L3: Agentic** | When CI pipelines triggered, agents read results and auto-remediate failures | Do agents read CI failures and auto-fix them? | Agents respond to CI failures; auto-remediation patterns; re-commit on lint failures |
| **L4: Autonomous** | Full closed-loop: agents commit, test, deploy, monitor, roll back autonomously | Do agents deploy without human approval? Monitor and rollback automatically? | Autonomous commits; deploy invocations; rollback logic; 24/7 closed-loop cycles |

---

### 5. Ticketing & Planning
**What it measures:** Is AI used to validate and refine work before starting?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Assisted** | Issues written manually; AI used only for code | Do PMs or devs use AI to write/refine tickets? Or is it all manual? | No ticket references in prompts; task descriptions vague; no issue link context |
| **L2: Integrated** | AI assists in writing or refining tickets; humans approve | Do developers validate ticket quality with AI before starting? | Early-session prompts reference JIRA/issues; acceptance criteria validation; ticket refinement |
| **L3: Agentic** | Agents parse raw issues into structured, implementation-ready artifacts | Do agents automatically structure issues into specs? | Issues transformed into detailed specs; acceptance criteria auto-generated; task decomposition |
| **L4: Autonomous** | Agents triage backlog, size work, assign to parallel tracks, validate completion | Do agents triage bugs, size stories, auto-assign? Monitor completion? | Backlog triage automation; story pointing; parallel task spawning; completion validation |

---

### 6. Cross-System Connectivity
**What it measures:** Can AI access repos, docs, JIRA, GitHub, Slack, etc.?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Isolated** | AI works in isolation (IDE only); no access to org systems | Is AI only in the IDE? Or connected to GitHub, JIRA, docs? | No GitHub, JIRA, Slack, doc tool invocations; isolated context |
| **L2: Connected** | AI reads from repos and docs; limited write access | Does AI fetch PR context, issue details, or architectural docs? | GitHub/JIRA lookups detected; doc references; limited write operations |
| **L3: Context-Sharing** | Agents read/write across repos, ticketing, CI/CD, monitoring systems | Do agents share state across systems? Read+write to multiple tools? | Multi-system context sharing; cross-repo coordination; bi-directional sync |
| **L4: Unified Context Layer** | Agents operate across all SDLC systems with full bi-directional integration | Is there a unified context layer feeding all agents? Business+product+tech metrics? | Unified context updates; business metrics feeding technical decisions; monitoring loop |

---

### 7. Quality Controls
**What it measures:** Are AI outputs held to code quality standards?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: No AI-specific** | No AI-specific quality gates; standard code review only | Is AI-generated code reviewed differently than human code? | No /review usage; test generation absent; coverage not validated |
| **L2: Linting & Checks** | Linting and basic checks on AI-generated code; review checklists exist | Are there linting jobs on AI code? PR review checklist with AI items? | Lint run failures present; test generation; coverage checks visible in logs |
| **L3: Eval Harnesses** | Automated eval harnesses validate AI output against defined quality criteria | Do you have test suites that validate AI output quality? | Comprehensive test generation; edge case testing; harness validation runs |
| **L4: Auto-Rejection** | Continuous quality scoring with auto-rejection, re-generation, escalation | Does the system auto-reject bad output and retry? | Quality score tracking; auto-rejection logic; re-generation loops; escalation protocols |

---

### 8. Security & Compliance
**What it measures:** Is AI usage governed and auditable?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: No Policy** | No policy on AI usage; shadow AI likely | Is there an AI usage policy? Data handling rules? | No compliance signals; PII-like patterns in prompts; unclear data source governance |
| **L2: Documented Policy** | AI usage policy exists; approved tool list; basic data handling rules | Is there a written policy? Approved tools documented? Data restrictions clear? | Policy reference visible; data-handling consistency; approved tool usage only |
| **L3: Enforced Guardrails** | Guardrails enforced in code (hooks, scans); AI actions logged and auditable | Are there hooks that prevent sensitive data in prompts? Audit logs enabled? | Sensitive data filtering detected; comprehensive logging; audit trail visible |
| **L4: Policy-as-Code** | Policy-as-code; agents self-enforce compliance; real-time violation detection | Are compliance rules automated? Real-time violation alerts? | Automated compliance checks; self-healing enforcement; real-time alerting detected |

---

### 9. Measurement & KPIs
**What it measures:** Are metrics tracked to show AI impact?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: No Metrics** | No metrics tracked for AI-assisted work | Do you track adoption rate or usage frequency? | No usage pattern analysis; adoption unclear |
| **L2: Basic Metrics** | Basic metrics: adoption rate, usage frequency; reported manually | Do you track % of team using AI and sessions/day? | Adoption rate >50%; session frequency visible; usage trending |
| **L3: DORA-Aligned** | DORA-aligned KPIs tracked automatically: velocity, throughput, cycle time, CFR | Do you track PR cycle time, deployment frequency, change failure rate? | Cycle time improvements; throughput gains; failure rate trends correlate with AI adoption |
| **L4: AI-Driven Dashboards** | AI-driven dashboards; agents optimize their own workflows based on KPI feedback loops | Do agents see KPIs and adjust their approach? Feedback loops? | Agents optimize for measured KPIs; feedback-driven improvements; continuous optimization |

---

### 10. Ways of Working
**What it measures:** Are AI workflows documented and shared?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Individual** | Each engineer uses AI independently; no team conventions | Do developers follow shared conventions, or each do their own thing? | Highly variable session patterns; no consistent entry protocol; ad-hoc workflows |
| **L2: Documented** | Team has shared conventions for AI use; documented in wiki or README | Is there an "AI Ways of Working" doc? Shared conventions documented? | Consistent session openers; CLAUDE.md loading; shared prompt patterns visible |
| **L3: Defined Gates** | Defined review gates, handoff protocols, escalation paths for agentic work | Are there review gates for AI-generated code? Escalation paths? | Clear review gate usage; escalation patterns; handoff protocol adherence |
| **L4: Shared Accountability** | Teams and agents share accountability; human oversight is structured, not ad-hoc | Do teams and agents have shared KPI accountability? Structured oversight? | Structured approval gates; agent KPI alignment; human oversight metrics tracked |

---

### 11. Accountability & Ownership
**What it measures:** Is AI adoption owned by a specific person/team?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: No Owner** | No one owns AI outcomes; results are individual | Is there a designated AI champion or owner? | No visible AI champion behavior; isolated adoption; no cross-team sharing |
| **L2: Tech Lead/Champion** | Tech lead or champion owns AI adoption for the team | Do you have a named AI champion? What are their responsibilities? | Consistent champion patterns visible; CLAUDE.md updates by same person; mentorship signals |
| **L3: Team Ownership** | Team collectively owns agentic output quality; KPIs tied to team performance | Are AI KPIs tied to team performance reviews? | Collective ownership signals; shared code review patterns; team velocity metrics |
| **L4: Measured SLAs** | End-to-end delivery outcomes owned by team+agents with measurable SLAs | Are delivery SLAs tied to AI outcomes? | Agent SLA compliance; delivery KPIs tracked; accountability metrics visible |

---

### 12. Scalability & Knowledge Transfer
**What it measures:** Can new developers be productive with AI quickly?

| Level | Definition | Assessment Questions | Claude Log Signals |
|-------|-----------|----------------------|-------------------|
| **L1: Tribal** | Knowledge is tribal; nothing documented or transferable | Is there onboarding material for AI? Or do new devs figure it out? | New dev sessions show low productivity; gradual ramp; no shared context available |
| **L2: Documented** | Some documentation; onboarding materials for AI tools exist | Do new devs get CLAUDE.md? Prompt library? Training? | New dev ramp visible; onboarding docs loaded; baseline context available |
| **L3: Reusable Playbooks** | Reusable playbooks, module configs, patterns documented and shared cross-team | Are common workflows documented as playbooks? Shared across teams? | Consistent playbook usage; cross-team adoption of patterns; documentation quality high |
| **L4: Self-Service** | Self-service enablement; new teams can adopt the model independently | Can a new team adopt AI workflows without COE help? | Zero-dependency onboarding; new team velocity; no handholding required |

---

## L2 Maturity Profile

An L2 team (the "Ideal Development Team" at Semios):

- ✅ All 12 sub-dimensions at 1.5+ maturity
- ✅ 70%+ of active developers using Claude Code daily
- ✅ Average prompt quality 70+ (detailed, grounded, actionable)
- ✅ /review used before every PR (pre-push AI validation)
- ✅ Prompt quality high and consistent across team (indicates shared context, CLAUDE.md)
- ✅ Tool adoption >20% (skills, integrations used regularly)
- ✅ Plan mode used for non-trivial work
- ✅ Documented practices visible in repo (CLAUDE.md, prompts, config)
- ✅ Evidence of AI champion (consistent quality, mentorship patterns)

---

## Qualitative Assessment Questions by Dimension

These questions help verify maturity levels. They should be asked during team interviews or surveys.

### SECTION 1: Capability (AI Tool Adoption, Prompt & Context Engineering, Agent Configuration)

**1.1 Current AI Usage in Delivery**
- How are developers currently using AI tools (Copilot, Claude Code, internal tools)?
- Are AI tools standardized or chosen individually? What is the selection process?
- What processes do you follow for planning, issue refinement, code generation, test creation, CI/CD? Where does AI live?
- How are AI outputs reviewed? Are there organizational policies that set standards for AI usage?

**1.2 Automation Across SDLC Phases**
- **Plan:** Is AI used to prioritize or synthesize backlog items?
- **Design:** Does AI draft or validate technical designs?
- **Build:** Does AI generate code beyond autocomplete?
- **Test:** Is AI generating or maintaining test suites?
- **Deploy:** Does AI assist in release management or rollout decisions?
- **Operate:** Does telemetry feed back into automated issue creation?

**1.3 Custom Agents & Skills**
- Do you have custom slash commands (e.g., /review, /commit, /plan)? How widely used?
- Does your team have at least 1 custom skill for repeated tasks?
- Are prompt templates curated and shared across team members?

---

### SECTION 2: Integration (CI/CD, Ticketing & Planning, Cross-System Connectivity)

**2.1 CI/CD Integration**
- How is AI-generated code validated before human review? (e.g., /review, automated lint checks, test generation)
- Does every PR pass through AI review layers? How many?
- Are test suites generated automatically or validated by AI?

**2.2 Ticketing & Planning**
- Do developers use AI to validate ticket quality before starting work?
- Are AI outputs used to enrich tickets (acceptance criteria, edge cases)?
- Are issues structured with sufficient context for both developers and AI?

**2.3 Cross-System Connectivity**
- Is AI connected to Git, CI/CD, JIRA/DevOps, documentation?
- Do AI tools share context across systems (e.g., PR history, architecture docs, CI results)?
- Are there 2+ MCP integrations active (JIRA + GitHub, etc.)?

---

### SECTION 3: Governance (Quality Controls, Security & Compliance, Measurement & KPIs)

**3.1 Quality Controls**
- Is there a documented PR review checklist with AI-specific items?
- Are AI-generated changes held to the same quality bar as human code?
- How are edge cases and test coverage validated for AI output?

**3.2 Security & Compliance**
- Is there a formal AI usage policy? Approved tools documented?
- What data restrictions exist (what can/cannot be sent to AI)?
- Are AI actions logged and auditable?
- Do you have hooks or scans that prevent sensitive data from reaching AI?

**3.3 Measurement & KPIs**
- What metrics do you track for AI adoption? (% of team, sessions/day, PR cycle time)
- How is AI impact measured? (Pre/post baselines, DORA metrics)
- Are adoption and timing metrics tracked automatically or manually?

---

### SECTION 4: Execution Ownership (Ways of Working, Accountability, Scalability)

**4.1 Ways of Working**
- Is there a documented "AI Ways of Working" page?
- What is the standard protocol for starting an AI session? (Load CLAUDE.md? Load context?)
- When do developers use plan mode vs. direct generation?

**4.2 Accountability & Ownership**
- Is there a designated AI champion? What are their explicit responsibilities?
- Who owns CLAUDE.md maintenance? Prompt library curation? Onboarding?
- Are AI KPIs tied to team performance reviews or individual accountability?

**4.3 Scalability & Knowledge Transfer**
- When new developers join, what AI onboarding materials do they receive?
- Is there a prompt library or playbook for common tasks?
- How quickly do new team members become productive with AI?

---


## Critical Philosophy: Holistic Understanding Over Numbers

**The 12 dimensions cannot be cleanly scored from numbers alone.**

A team can have:
- ✅ 70% of developers using Claude Code (looks like L2 adoption)
- ✅ High average prompt quality (looks like L2 engineering)
- ✅ 80% /review adoption (looks like L2 CI/CD)

...yet be L1 overall because:
- ❌ No CLAUDE.md (shared context missing)
- ❌ No documented policy (governance absent)
- ❌ No AI champion (ownership missing)
- ❌ No documented ways of working (processes ad-hoc)

**Conversely, a team with lower quantitative metrics can be L2+ if:**
- ✅ They have a strong CLAUDE.md strategy
- ✅ They have a designated AI champion and explicit responsibilities
- ✅ They have documented workflows and escalation paths
- ✅ They have a security policy and approval gates

**The point:** Quantitative signals are supporting evidence, not the score itself. The real maturity comes from:
1. **Governance** — Are practices documented and enforced?
2. **Ownership** — Is someone responsible and accountable?
3. **Integration** — Are workflows designed for AI from the start?
4. **Consistency** — Are practices team-wide or individual?
5. **Intentionality** — Is AI use strategic, or ad-hoc?

### How to Use This Framework

**Don't:** Try to auto-score all 12 dimensions from log data alone.

**Do:** Use logs as supporting evidence, then:
1. Ask the qualitative assessment questions
2. Interview the team about practices, policies, and ownership
3. Check artifacts (CLAUDE.md, PR checklists, onboarding docs)
4. Synthesize a holistic maturity rating

**The output should answer:**
- "What is this team intentionally doing with AI?"
- "Who owns AI outcomes?"
- "Are practices documented or tribal?"
- "Are workflows designed for AI, or is AI bolted on?"
- "What would it take to reach the next level?"

Not just: "They score 2.3 on dimension X."

---

## Detecting Maturity from Claude Code Logs

### Quantitative Signals (Supporting Evidence Only)

| Sub-Dimension | Claude Log Metric | L1 Range | L2 Range | L3 Range | L4 Range |
|---|---|---|---|---|---|
| **AI Tool Adoption** | % of team using Claude Code | <30% | 50-75% | 75-90% | >90% |
| **Prompt & Context Engineering** | Avg prompt quality score | <40 | 60-75 | 75-85 | 85+ |
| **Agent Configuration** | Skill invocation ratio | <5% | 20-30% | 40-60% | >60% |
| **CI/CD Integration** | /review usage (% of sessions) | <20% | >80% | >95% | 100% |
| **Ticketing & Planning** | Early-session JIRA/issue refs | <10% | >40% | >70% | >90% |
| **Cross-System Connectivity** | MCP tool invocations | 0 | 1-2 | 3-4 | 5+ |
| **Quality Controls** | Test generation % | <20% | 40-60% | 70-85% | 90%+ |
| **Security & Compliance** | PII/sensitive data patterns | Frequent | Occasional | Rare | None |
| **Measurement & KPIs** | Adoption rate trend | Declining | Stable | Growing | Rapidly growing |
| **Ways of Working** | Plan mode usage | <10% | 30-50% | 60-75% | >75% |
| **Accountability** | CLAUDE.md update frequency | Sporadic | Monthly | Weekly | Real-time |
| **Scalability** | New dev ramp time (weeks to baseline) | 6-8 | 3-4 | 1-2 | <1 |

### Qualitative Signals (Inferred from Log Patterns)

**AI Tool Adoption**
- L1: Multiple different tools detected; no coordination
- L2: Single primary tool (Claude Code); Copilot for PRs; consistent across team
- L3: Tool orchestration visible; multiple agents per task; coordinated tool switching
- L4: Agents autonomously select best tool per task; tool fragmentation impossible

**Prompt & Context Engineering**
- L1: Prompts rewritten each session; high variation; no file/line refs
- L2: Consistent prompt structure; file/line refs in >50% of prompts; CLAUDE.md loaded
- L3: Agents auto-load context; architecture/design doc references; minimal prompt preamble
- L4: Context self-updates; self-improving prompts detected; agent-optimized chains

**Agent Configuration**
- L1: Default tool behavior only; no customization
- L2: 1-2 custom slash commands; basic Copilot instructions configured
- L3: Multi-step agents; error handling patterns; specialized agents per task
- L4: Sub-agent orchestration; dynamic decomposition; self-correcting workflows

**CI/CD Integration**
- L1: Outputs manually copy-pasted; no automation signals
- L2: /review before push (>80%); lint failures recovered; tests generated
- L3: Agents respond to CI failures; auto-remediation patterns; re-commits on failure
- L4: Autonomous deploy; rollback; monitoring feedback loops; 24/7 closed-loop

**Ticketing & Planning**
- L1: Tasks described vaguely; no issue structure
- L2: Early session prompts reference JIRA; acceptance criteria validated
- L3: Issues auto-transformed into specs; task decomposition; structured data extraction
- L4: Backlog triage; story pointing; parallel task generation; completion validation

**Cross-System Connectivity**
- L1: No external tool invocations; IDE-only context
- L2: GitHub/JIRA lookups; doc references; fetch operations visible
- L3: Multi-system reads and writes; context sharing across tools
- L4: Unified context layer; business metrics feeding technical decisions

**Quality Controls**
- L1: No /review; no test generation; no coverage checks
- L2: /review in >80% of sessions; test generation; linting feedback
- L3: Comprehensive test suites; edge case generation; harness validation
- L4: Auto-rejection of low-quality output; re-generation loops; escalation protocols

**Security & Compliance**
- L1: PII, API keys, or sensitive data in prompts
- L2: Consistent data-handling patterns; no PII detected; policy adherence evident
- L3: Sensitive data actively filtered; audit logging enabled; compliance hooks detected
- L4: Real-time violation detection; automated self-healing; policy-as-code visible

**Measurement & KPIs**
- L1: No adoption metrics; usage unclear
- L2: Adoption rate >50%; sessions/day tracked; basic reporting
- L3: DORA metrics; cycle time improvements; throughput gains correlate with AI
- L4: Agents optimize for measured KPIs; feedback-driven improvements; continuous optimization

**Ways of Working**
- L1: Highly variable session patterns; no consistent entry protocol
- L2: Consistent CLAUDE.md loading; shared prompt patterns; standard session structure
- L3: Defined review gates; escalation patterns; handoff protocols evident
- L4: Structured oversight; agent KPI alignment; consistent accountability patterns

**Accountability & Ownership**
- L1: No visible champion; isolated adoption; no cross-team patterns
- L2: Consistent champion patterns; CLAUDE.md updates by 1-2 people; mentorship visible
- L3: Collective ownership; shared code review patterns; team velocity metrics
- L4: Agent SLA compliance; delivery KPIs tied to team and agent responsibility

**Scalability & Knowledge Transfer**
- L1: New devs show low productivity; gradual 6-8 week ramp
- L2: New devs load CLAUDE.md; access prompt library; 3-4 week ramp to baseline
- L3: Consistent playbook usage; cross-team pattern adoption; 1-2 week ramp
- L4: New teams adopt independently; zero-dependency onboarding; <1 week ramp

---

## Three Data Sources for Assessment

The tool ingests from **three independent sources**, not just logs:

### 1. **Logs** (Behavioral Evidence)
What developers actually do with Claude Code:
- Session frequency, duration, depth
- Prompt quality, tool invocations, /commands used
- Error patterns, recovery behaviors
- Data handling patterns, context reuse

**Signal:** Usage patterns, adoption, discipline

### 2. **Configs** (Documented Practices)
Configuration files checked into the repo:
- **CLAUDE.md** — Project context, architecture, conventions, known gotchas
- **AGENTS.md** — Custom agent definitions, orchestration rules
- **.rules** — Coding standards, quality gates, governance rules
- **settings.json** — Tool configuration, approved integrations, compliance settings

**Signal:** Intentionality, documentation, governance

### 3. **Capabilities** (Built Infrastructure)
What the team has actually constructed:
- **Custom Skills** — /review, /commit, /plan, etc. (in Claude Code)
- **Commands** — Defined slash commands and automation
- **Agents** — Multi-step agents, orchestration logic
- **Plugins/MCP** — Integrations to JIRA, GitHub, Slack, docs, etc.

**Signal:** Investment, integration, sophistication

---

## Why Three Sources Matter: Triangulation

**Example: Assessing "Quality Controls" (L2 requirement: Linting + review checklists)**

| Source | Evidence | Interpretation |
|--------|----------|-----------------|
| **Logs** | 80% /review adoption, test generation in 45% of sessions | Team actively uses review; some testing |
| **Configs** | CLAUDE.md has PR review section; .rules defines linting rules; settings.json has quality gates | Quality practices are documented, not ad-hoc |
| **Capabilities** | Custom /review skill exists; /lint skill configured; test generation skill | Team invested in automation; tools aren't manual |

**Assessment:** ✅ **L2 Integrated** — Logs show practice, configs show intentionality, capabilities show infrastructure. All three sources align.

---

**Contrast with Team B (same logs, different configs/capabilities):**

| Source | Evidence | Interpretation |
|--------|----------|-----------------|
| **Logs** | 80% /review adoption, test generation in 45% of sessions | Same behavior as Team A |
| **Configs** | No CLAUDE.md, no quality rules, settings.json defaults only | Practices undocumented; ad-hoc |
| **Capabilities** | No custom skills; using Copilot defaults; no configured linting | No infrastructure investment |

**Assessment:** ⚠️ **L1-L2 Boundary** — Logs look good, but configs show no documentation and capabilities show no infrastructure. Unsustainable. At risk of regression if champion leaves.

---

## Implementation Roadmap

**Core Principle:** The goal is to enable better qualitative assessment and discovery, not to automate scoring. Evidence from three sources provides triangulation; people provide understanding.

### Phase 1: Extract Supporting Evidence from All Three Sources

**From Logs:**
- **Tool diversity:** Which tools are invoked; consistency across team
- **Command usage:** /review, /commit, /plan frequency (signals of practice)
- **Context patterns:** CLAUDE.md loading, early-session behavior (signals of discipline)
- **MCP/Integration invocations:** Cross-system connectivity evidence
- **Testing signals:** Test generation %, coverage validation
- **Data handling:** Scan for PII/sensitive patterns (compliance signals)
- **Session structure:** Opening protocol consistency (signals process maturity)
- **Consistency metrics:** Prompt variation across team, champion behavior detection

**From Configs (CLAUDE.md, AGENTS.md, .rules, settings.json):**
- **CLAUDE.md presence & quality:** Does it exist? Current? Covers architecture, conventions, gotchas?
- **AGENTS.md:** Are agents defined explicitly? Orchestration rules documented?
- **.rules:** Are coding standards codified? Quality gates defined?
- **settings.json:** Which tools approved? Compliance settings configured? MCP integrations declared?

**From Capabilities (Skills, Commands, Agents, MCP):**
- **Custom skills:** What /commands exist? (/review, /commit, /plan, custom domain skills)
- **Agents:** How many? Multi-step? Orchestrated? Error handling?
- **MCP integrations:** Active integrations (GitHub, JIRA, Slack, Confluence, docs?)
- **Plugins:** What's installed? Enabled? Configured?

**Output:** Evidence dashboard per dimension
```json
{
  "dimension_signals": {
    "quality_controls": {
      "logs": {
        "review_adoption": "80% of sessions",
        "test_generation": "45% of sessions"
      },
      "configs": {
        "claude_md_has_review_section": true,
        "rules_file_exists": true,
        "pr_checklist_documented": true
      },
      "capabilities": {
        "review_skill_exists": true,
        "lint_skill_configured": true,
        "test_generation_skill": true
      }
    },
    "accountability_ownership": {
      "logs": {
        "claude_md_authors": ["alice@co.com", "bob@co.com"],
        "champion_candidate": "alice@co.com (high consistency, mentorship signals)"
      },
      "configs": {
        "champion_named_in_agents_md": true,
        "responsibilities_documented": false,
        "claude_md_maintenance_owner": "alice@co.com (git blame analysis)"
      },
      "capabilities": {
        "custom_skills_created": 3,
        "skill_diversity_suggests": "Intentional agent architecture"
      }
    }
  }
}
```

**Purpose:** Provide assessors with triangulated evidence from all three sources. Contradictions are signals for deeper investigation, not reasons to dismiss sources.

### Phase 2: Generate Assessment Question Facilitator
Build a guided interview UI that:
1. Shows triangulated evidence (logs + configs + capabilities) for each question
2. Asks the 50 assessment questions from the template (organized by dimension)
3. Allows the assessor to record answers (L1-L4 per question)
4. Flags contradictions and misalignments:
   - **Logs-Config mismatch:** "Logs show /review in 80% of sessions, but CLAUDE.md has no review policy"
   - **Config-Capability mismatch:** ".rules file defines linting standards, but no /lint skill exists"
   - **Capability-Log mismatch:** "5 custom skills exist, but only 2 are actively used in sessions"

These misalignments are research opportunities, not errors to ignore.

**Output:** Qualitative assessment responses
```json
{
  "assessment_responses": {
    "ai_tool_adoption": {
      "Q: Who decides which AI tool to use?": "Tech lead recommends Claude Code, enforced in PR guidelines",
      "Q: Are licenses managed centrally?": "Yes, via IT. All 18 devs have Claude Code + Copilot",
      "INFERRED_LEVEL": 2,
      "CONFIDENCE": "High - evidence aligns with L2 requirements"
    }
  }
}
```

### Phase 3: Artifact Verification Layer
Check for tangible evidence of maturity:
- **CLAUDE.md presence + quality:** Does it exist? Is it current? What sections?
- **Documentation:** "AI Ways of Working" doc, PR review checklist, policy doc
- **Process artifacts:** Onboarding guide, prompt library, escalation paths
- **Ownership signals:** Named champion in team roster, responsibilities defined

**Output:** Artifact checklist per dimension
```json
{
  "artifacts": {
    "prompt_context_engineering": {
      "claude_md_exists": true,
      "repos_with_claude_md": "18/22 (82%)",
      "claude_md_quality": "High - includes architecture, conventions, gotchas",
      "last_updated": "2026-04-08",
      "evidence": "✅ L2 requirement met"
    },
    "accountability_ownership": {
      "ai_champion_named": true,
      "champion": "alice@co.com",
      "responsibilities_documented": false,
      "evidence": "⚠️ Champion exists, but responsibilities not explicit (L1.5)"
    }
  }
}
```

### Phase 4: Synthesis Report (Human-Driven, Three-Source Triangulation)
Combine signals from **Logs, Configs, and Capabilities** into a holistic assessment:

**For each dimension:**
1. **Evidence from Logs:** "72% adoption, consistent tool choice"
2. **Evidence from Configs (CLAUDE.md, AGENTS.md, .rules, settings.json):** "Tool standardization documented; Claude Code + Copilot approved; centralized licensing configured"
3. **Evidence from Capabilities (Skills, Commands, Agents, MCP):** "Custom /review, /commit, /plan skills built; 2+ MCP integrations active"
4. **Answers to assessment questions:** "Team says: 'Tech lead enforces Claude Code; all 18 devs have licenses; no tool fragmentation'"
5. **Synthesized maturity:** "L2 - Integrated" (all four sources align)
6. **Confidence:** "High" (triangulation confirms; logs + configs + capabilities + answers all point to L2)
7. **Gaps/next steps:** "To reach L3: implement multi-agent orchestration, add AGENTS.md definitions, deploy 2+ new MCP integrations"

**If sources DON'T align:**
- **Logs high, configs low:** "Team uses AI actively, but practices undocumented — risk of regression"
- **Configs high, capabilities low:** "Documented standards exist, but not built into actual skills/tools — implementation gap"
- **Capabilities exist, logs show low adoption:** "Infrastructure built but not used — usage training needed"

These misalignments are more valuable than alignment. They highlight where to focus improvement.

**This is NOT automated.** An assessor reads logs + configs + capabilities evidence, asks questions, synthesizes all sources, then makes the call.

### Phase 5: Deep Knowledge Artifact Analysis
Future: Extract, parse, and analyze config/capability files to understand:

**CLAUDE.md Analysis:**
- **Coverage:** % of active repos with CLAUDE.md
- **Completeness:** Does it include architecture, conventions, gotchas, domain context?
- **Freshness:** Last updated date (signals maintenance)
- **Quality:** Depth of architecture explanation, clarity of conventions
- **Usage:** How often do developers reference it in logs?

**AGENTS.md Analysis:**
- **Defined agents:** How many? Sophisticated orchestration?
- **Error handling:** Explicit error recovery paths?
- **Documentation:** Clear handoff protocols between agents?

**.rules Analysis:**
- **Quality gates:** Automated linting, test coverage, complexity checks?
- **Review requirements:** AI-specific review steps?
- **Compliance rules:** Data handling, security gates?

**Capabilities Analysis:**
- **Skill coverage:** Which workflows have custom skills vs. manual work?
- **Skill recentness:** When last updated? Signs of maintenance?
- **MCP saturation:** Which integrations exist? Which are gaps?
- **Adoption correlation:** Do skills in capabilities match usage in logs?

This feeds into:
- **Prompt & Context Engineering** — CLAUDE.md quality + coverage
- **Agent Configuration** — AGENTS.md sophistication + Capabilities count
- **Ways of Working** — Config completeness + process documentation
- **Accountability & Ownership** — Config maintenance patterns (git blame, freshness)
- **Quality Controls** — .rules enforcement + automated gates
- **Cross-System Connectivity** — MCP integrations declared in configs vs. used in logs

---

## Assessment Philosophy

**This tool should make assessment easier, not replace it.**

A good assessment:
1. **Starts with evidence:** "Your logs show 72% Claude Code adoption"
2. **Asks questions:** "Is that by choice or enforcement? How are tools managed?"
3. **Checks artifacts:** "Show me your tool selection policy or CLAUDE.md"
4. **Makes a judgment call:** "Based on all three, you're L2 Integrated on tool adoption"

**Not:** "Your logs show 72% adoption = L2 score."

The assessor is the expert. The tool is a facilitator.

---

## What This Tool Is NOT

❌ **Not an auto-scorer.** Don't build a function that reads logs and returns "L2.3 overall maturity." That's wrong.

❌ **Not a replacement for interviews.** You cannot assess "Accountability & Ownership" or "Ways of Working" from logs alone. You must ask the team.

❌ **Not a source of truth.** Logs are one data source. Contradictions matter: If logs show 80% /review adoption but the team says "we have no PR policy," that's a critical finding to explore, not ignore.

❌ **Not unbiased.** The rubric and questions embed assumptions about "good" AI practices. Different orgs may have valid L1/L2 approaches that don't fit the Semios ideal-team-vision.

---

## What This Tool IS

✅ **A structured assessment framework.** 4 dimensions, 12 sub-dimensions, L1-L4 definitions, 50 assessment questions.

✅ **An evidence facilitator.** Surfacing log patterns (tool usage, /review adoption, CLAUDE.md loading) to inform better questions.

✅ **A gap mapper.** Showing where log evidence aligns with or contradicts team answers, flagging areas that need deeper investigation.

✅ **A roadmap generator.** Suggesting what practices to adopt to move from L1 → L2 → L3 → L4.

✅ **A discovery tool.** Helping teams understand their own AI maturity holistically, not just "prompt quality = 73."

---

## Example: Why You Can't Auto-Score

**Team A:**
- Logs: 70% adoption, avg quality 72, /review in 85% of sessions
- Assessment Q: "Who owns AI outcomes?" → "No one; everyone uses it independently"
- Artifact check: "No CLAUDE.md, no policy, no champion"
- **Assessment:** L1 (Assisted) — Looks like L2 on logs, but governance is absent

**Team B:**
- Logs: 50% adoption, avg quality 65, /review in 40% of sessions
- Assessment Q: "Who owns AI outcomes?" → "Alice is our AI champion; owns CLAUDE.md and trains new devs"
- Artifact check: "CLAUDE.md in all repos, updated last week, comprehensive"
- **Assessment:** L2 (Integrated) — Lower quantitative metrics, but intentional practices + ownership = L2

**The moral:** The same log metrics can mean different things depending on governance, ownership, and intentionality. Only holistic assessment gets it right.

---

## Mapping Between Auto-SDLC Metrics and Maturity Dimensions

How existing auto-sdlc measurements feed the 12-dimension scorecard:

| Auto-SDLC Metric | Feeds Into Dimension | How It's Used |
|---|---|---|
| Avg prompt quality score (0-100) | Prompt & Context Engineering | Directly; L2 = 60+, L3 = 75+, L4 = 85+ |
| Skill invocation ratio (%) | Agent Configuration | Directly; L2 = 20-30%, L3 = 40-60%, L4 = 60%+ |
| Sessions per day | Ways of Working (implies engagement) | Trends; increasing = adoption accelerating |
| Messages per session | Session Depth + Ways of Working | High depth = thorough workflows; implies structured approach |
| Cache hit ratio | Security & Compliance (reuse patterns) | High ratio = consistent context reuse; implies shared practices |
| Tool diversity | Cross-System Connectivity | Multiple tools = integrations active |
| Prompt consistency (variation) | Accountability & Ownership | Low variation = strong champion or shared templates |
| New developer ramp time | Scalability & Knowledge Transfer | Time to baseline productivity with AI |
| /review adoption | Quality Controls | % of PRs reviewed by AI |
| CLAUDE.md presence | Prompt & Context Engineering | Indicator of shared context strategy |

---

## Key Insights

The current auto-sdlc tool measures **individual developer AI competence** (prompt sophistication, tool adoption, session depth).

The ideal tool measures **team AI maturity** (shared practices, governance, integration, knowledge management).

A developer can have high prompt quality (L3-4 individual) but the team might be L1 if:
- No shared CLAUDE.md
- No AI champion
- No documented policies
- No CI/CD integration
- No cross-team knowledge sharing

The reverse is also true: a team can reach L2 even with mid-range prompt quality if they have:
- Strong practices (CLAUDE.md, ways of working)
- Governance (security policy, review checklist)
- Integration (CI/CD, MCP connections)
- Ownership (champion, onboarding)

**Goal:** Shift the conversation from "How well do individuals use Claude?" to "How mature is our team's AI capability?"

---

## Metrics vs. Maturity

| Current Auto-SDLC | Future Ideal |
|---|---|
| Avg prompt quality: 72/100 | Prompt & Context Engineering: L2 (shared CLAUDE.md, templates) |
| Skill adoption ratio: 35% | Agent Configuration: L2 (1+ custom skill, documented) |
| Sessions/day: 0.8 | AI Tool Adoption: L2 (team standardized, consistent) |
| Cache hit ratio: 45% | Measurement & KPIs: L2 (adoption, timing, impact tracked) |
| Avg messages/session: 18 | Ways of Working: L2 (shared norms documented) |

The left column describes individuals. The right describes the team.
