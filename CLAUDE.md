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

## Implementation Roadmap

### Phase 1: Extend Report JSON
Add to individual/team reports:
- Detected MCP integrations (tool call history)
- Skill vs. prompt invocation ratio breakdown
- Session opening patterns (context loading)
- Plan mode usage percentage
- /review adoption (% of sessions with /review)
- Prompt consistency score (variation across team)

### Phase 2: Add Dimension Category Mapping
Map the 12 sub-dimensions to behavioral patterns:
- Infer each sub-dimension score (0-4) from logs
- Show "Evidence" sections highlighting behaviors that signal maturity
- Example: "Agent Configuration (L2)" → "23% skill invocations, 5 unique tools, consistent use of /commit"

### Phase 3: Generate L2 Checklist Report
Generate a checklist showing:
- Which of the 12 sub-dimensions are at 1.5+ (L2)
- Which are gaps (need work)
- What behaviors would unlock the next level
- Recommendations for reaching L2/L3

### Phase 4: Integrate with CLAUDE.md Detection
Future: Actually parse CLAUDE.md files to verify:
- Repo coverage (% of active repos have CLAUDE.md)
- Content quality (architecture, conventions, context documented)
- Freshness (last updated date)
- Usage patterns (developers referencing it in sessions)

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
