"""Log Evidence Extractor - Extracts behavioral signals from Claude logs across 12 dimensions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from auto_sdlc.logs.parser import parse_session_file, find_session_files
from auto_sdlc.logs.scorer import score_session_prompts, score_prompt
from auto_sdlc.logs.metrics import aggregate_behavioral_metrics, extract_behavioral_metrics
from auto_sdlc.logs.maturity import build_maturity_report, score_dimension
from auto_sdlc.logs.analyzer import extract_token_usage, extract_session_metadata


@dataclass
class LogEvidence:
    """Captures behavioral signals from Claude logs for a specific dimension.

    Attributes:
        dimension: Name of the 12 dimensions (e.g., 'AI Tool Adoption')
        signals: Named signals extracted for this dimension (e.g., tool_usage_pct: 0.45)
        raw_metrics: Underlying metrics for transparency (raw data supporting signals)
        confidence: Confidence level in the extracted evidence ("high", "medium", or "low")
    """

    dimension: str
    signals: Dict[str, float] = field(default_factory=dict)
    raw_metrics: Dict[str, Any] = field(default_factory=dict)
    confidence: str = "medium"


class LogEvidenceExtractor:
    """Extracts per-dimension behavioral signals from project logs."""

    def __init__(self):
        """Initialize the extractor."""
        self.session_events = []
        self.all_events = []
        self.sessions = []

    def extract_from_project(self, logs_path: Path) -> List[LogEvidence]:
        """Analyze project logs and extract evidence for all 12 dimensions.

        Args:
            logs_path: Path to the project logs directory

        Returns:
            List of LogEvidence objects, one per dimension
        """
        logs_path = Path(logs_path)
        session_files = find_session_files(logs_path)

        # Parse all session files
        for f in session_files:
            events = parse_session_file(f)
            if events:
                self.all_events.append(events)
                metadata = extract_session_metadata(events)
                token_usage = extract_token_usage(events)
                self.sessions.append({
                    "session_id": metadata.get("session_id"),
                    "metadata": metadata,
                    "token_usage": token_usage,
                    "events": events,
                })

        # Extract evidence for each dimension
        evidence_list = [
            self._extract_ai_tool_adoption(),
            self._extract_prompt_context_engineering(),
            self._extract_agent_configuration(),
            self._extract_ci_cd_integration(),
            self._extract_ticketing_planning(),
            self._extract_cross_system_connectivity(),
            self._extract_quality_controls(),
            self._extract_security_compliance(),
            self._extract_measurement_kpis(),
            self._extract_ways_of_working(),
            self._extract_accountability_ownership(),
            self._extract_scalability_knowledge_transfer(),
        ]

        return evidence_list

    def _extract_ai_tool_adoption(self) -> LogEvidence:
        """Extract signals: tool usage %, consistency, tool diversity."""
        if not self.all_events:
            return LogEvidence(
                dimension="AI Tool Adoption",
                signals={"tool_usage_pct": 0.0, "tool_consistency": 0.0, "tool_diversity": 0.0},
                raw_metrics={},
                confidence="low",
            )

        total_days = max(len(set(s["metadata"].get("start_timestamp", "")[:10]
                                 for s in self.sessions if s["metadata"].get("start_timestamp"))), 1)
        behavioral = aggregate_behavioral_metrics(self.all_events, total_days_active=total_days)

        total_tool_calls = behavioral.get("total_tool_calls", 0)
        total_messages = (behavioral.get("total_skill_invocations", 0) +
                         behavioral.get("total_user_messages", 0))
        tool_usage_pct = (total_tool_calls / total_messages * 100) if total_messages > 0 else 0.0

        # Tool consistency: % of sessions that have at least one tool call
        sessions_with_tools = sum(
            1 for events in self.all_events
            if any(
                block.get("type") == "tool_use"
                for event in events
                if event.get("type") == "assistant"
                for block in (event.get("message", {}).get("content") or [])
                if isinstance(block, dict)
            )
        )
        tool_consistency = (sessions_with_tools / len(self.all_events) * 100) if self.all_events else 0.0

        # Tool diversity: count unique tool names
        unique_tools = len(set(behavioral.get("unique_tools_used", [])))

        return LogEvidence(
            dimension="AI Tool Adoption",
            signals={
                "tool_usage_pct": float(round(tool_usage_pct, 2)),
                "tool_consistency": float(round(tool_consistency, 2)),
                "tool_diversity": float(unique_tools),
            },
            raw_metrics={
                "total_tool_calls": total_tool_calls,
                "total_messages": total_messages,
                "sessions_with_tools": sessions_with_tools,
                "total_sessions": len(self.all_events),
                "unique_tools": behavioral.get("unique_tools_used", []),
            },
            confidence="high" if self.all_events else "low",
        )

    def _extract_prompt_context_engineering(self) -> LogEvidence:
        """Extract signals: prompt quality score, file/line reference frequency."""
        if not self.all_events:
            return LogEvidence(
                dimension="Prompt & Context Engineering",
                signals={"avg_quality_score": 0.0, "file_ref_frequency": 0.0, "line_ref_frequency": 0.0},
                raw_metrics={},
                confidence="low",
            )

        all_scores = []
        file_ref_count = 0
        line_ref_count = 0
        total_prompts = 0

        for events in self.all_events:
            prompt_scores = score_session_prompts(events)
            for scored in prompt_scores:
                total_prompts += 1
                all_scores.append(scored["score"])
                if scored.get("has_file_ref"):
                    file_ref_count += 1
                if scored.get("has_line_ref"):
                    line_ref_count += 1

        avg_quality = sum(all_scores) / len(all_scores) if all_scores else 0.0
        file_ref_freq = (file_ref_count / total_prompts * 100) if total_prompts > 0 else 0.0
        line_ref_freq = (line_ref_count / total_prompts * 100) if total_prompts > 0 else 0.0

        return LogEvidence(
            dimension="Prompt & Context Engineering",
            signals={
                "avg_quality_score": float(round(avg_quality, 1)),
                "file_ref_frequency": float(round(file_ref_freq, 2)),
                "line_ref_frequency": float(round(line_ref_freq, 2)),
            },
            raw_metrics={
                "total_prompts_analyzed": total_prompts,
                "prompts_with_file_refs": file_ref_count,
                "prompts_with_line_refs": line_ref_count,
                "score_distribution": {
                    "min": min(all_scores) if all_scores else 0,
                    "max": max(all_scores) if all_scores else 0,
                    "count": len(all_scores),
                },
            },
            confidence="high" if all_scores else "low",
        )

    def _extract_agent_configuration(self) -> LogEvidence:
        """Extract signals: skill invocation ratio, tool diversity, agent count."""
        if not self.all_events:
            return LogEvidence(
                dimension="Agent Configuration",
                signals={
                    "skill_invocation_ratio": 0.0,
                    "tool_diversity": 0.0,
                    "unique_agents": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        total_days = max(len(set(s["metadata"].get("start_timestamp", "")[:10]
                                 for s in self.sessions if s["metadata"].get("start_timestamp"))), 1)
        behavioral = aggregate_behavioral_metrics(self.all_events, total_days_active=total_days)

        skill_ratio = behavioral.get("skill_invocation_ratio", 0.0)
        tool_diversity = len(set(behavioral.get("unique_tools_used", [])))

        # Agent count: estimate from unique tool/skill combinations or sessions
        unique_agents = len(self.all_events)

        return LogEvidence(
            dimension="Agent Configuration",
            signals={
                "skill_invocation_ratio": float(round(skill_ratio, 3)),
                "tool_diversity": float(tool_diversity),
                "unique_agents": float(unique_agents),
            },
            raw_metrics={
                "total_skill_invocations": behavioral.get("total_skill_invocations", 0),
                "total_messages": (behavioral.get("total_skill_invocations", 0) +
                                 behavioral.get("total_user_messages", 0)),
                "unique_tools": behavioral.get("unique_tools_used", []),
            },
            confidence="high" if self.all_events else "low",
        )

    def _extract_ci_cd_integration(self) -> LogEvidence:
        """Extract signals: /review adoption rate, test generation frequency."""
        if not self.all_events:
            return LogEvidence(
                dimension="CI/CD Integration",
                signals={
                    "review_adoption_rate": 0.0,
                    "test_generation_frequency": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # Count /review invocations (meta commands matching review pattern)
        review_count = 0
        test_mentions = 0
        total_meta_commands = 0

        for events in self.all_events:
            for event in events:
                if event.get("type") == "user" and event.get("isMeta"):
                    total_meta_commands += 1
                    content = event.get("message", {}).get("content", "")
                    if isinstance(content, str):
                        if "/review" in content.lower() or "review" in content.lower():
                            review_count += 1
                        if "test" in content.lower():
                            test_mentions += 1

        review_rate = (review_count / total_meta_commands * 100) if total_meta_commands > 0 else 0.0
        test_freq = (test_mentions / total_meta_commands * 100) if total_meta_commands > 0 else 0.0

        return LogEvidence(
            dimension="CI/CD Integration",
            signals={
                "review_adoption_rate": float(round(review_rate, 2)),
                "test_generation_frequency": float(round(test_freq, 2)),
            },
            raw_metrics={
                "review_invocations": review_count,
                "test_mentions": test_mentions,
                "total_meta_commands": total_meta_commands,
            },
            confidence="high" if total_meta_commands > 0 else "low",
        )

    def _extract_ticketing_planning(self) -> LogEvidence:
        """Extract signals: JIRA references early in sessions."""
        if not self.sessions:
            return LogEvidence(
                dimension="Ticketing & Planning",
                signals={"jira_references": 0.0, "early_jira_ratio": 0.0},
                raw_metrics={},
                confidence="low",
            )

        jira_sessions = 0
        early_jira_sessions = 0

        for events in self.all_events:
            has_jira = False
            early_jira = False
            for i, event in enumerate(events[:5]):  # First 5 events
                content_str = str(event.get("message", {}).get("content", ""))
                if "jira" in content_str.lower() or "ticket" in content_str.lower():
                    has_jira = True
                    if i < 3:
                        early_jira = True
            if has_jira:
                jira_sessions += 1
                if early_jira:
                    early_jira_sessions += 1

        jira_ref_rate = (jira_sessions / len(self.all_events) * 100) if self.all_events else 0.0
        early_rate = (early_jira_sessions / jira_sessions * 100) if jira_sessions > 0 else 0.0

        return LogEvidence(
            dimension="Ticketing & Planning",
            signals={
                "jira_references": float(round(jira_ref_rate, 2)),
                "early_jira_ratio": float(round(early_rate, 2)),
            },
            raw_metrics={
                "sessions_with_jira": jira_sessions,
                "sessions_with_early_jira": early_jira_sessions,
                "total_sessions": len(self.all_events),
            },
            confidence="medium" if self.all_events else "low",
        )

    def _extract_cross_system_connectivity(self) -> LogEvidence:
        """Extract signals: MCP tool invocation frequency."""
        if not self.all_events:
            return LogEvidence(
                dimension="Cross-System Connectivity",
                signals={"mcp_tool_invocation_frequency": 0.0},
                raw_metrics={},
                confidence="low",
            )

        mcp_calls = 0
        total_tool_calls = 0

        for events in self.all_events:
            for event in events:
                if event.get("type") == "assistant":
                    content = event.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                total_tool_calls += 1
                                tool_name = block.get("name", "").lower()
                                # MCP tools typically have specific naming patterns
                                if any(pattern in tool_name for pattern in ["mcp_", "web", "fetch", "grep"]):
                                    mcp_calls += 1

        mcp_freq = (mcp_calls / total_tool_calls * 100) if total_tool_calls > 0 else 0.0

        return LogEvidence(
            dimension="Cross-System Connectivity",
            signals={
                "mcp_tool_invocation_frequency": float(round(mcp_freq, 2)),
            },
            raw_metrics={
                "mcp_tool_calls": mcp_calls,
                "total_tool_calls": total_tool_calls,
            },
            confidence="high" if total_tool_calls > 0 else "low",
        )

    def _extract_quality_controls(self) -> LogEvidence:
        """Extract signals: /review usage %, test patterns, error recovery rate."""
        if not self.all_events:
            return LogEvidence(
                dimension="Quality Controls",
                signals={
                    "review_usage_pct": 0.0,
                    "test_pattern_prevalence": 0.0,
                    "error_recovery_rate": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        review_usage = 0
        test_patterns = 0
        error_recovery = 0
        error_patterns = 0
        total_meta_commands = 0
        total_user_messages = 0

        for events in self.all_events:
            session_has_recovery = False
            session_has_error = False
            for i, event in enumerate(events):
                if event.get("type") == "user" and event.get("isMeta"):
                    total_meta_commands += 1
                    content = event.get("message", {}).get("content", "")
                    if isinstance(content, str):
                        if "/review" in content.lower():
                            review_usage += 1
                        if "test" in content.lower():
                            test_patterns += 1
                        # Check for error mention followed by recovery attempt
                        if "error" in content.lower() or "bug" in content.lower():
                            session_has_error = True
                            error_patterns += 1
                            # Look ahead for recovery attempts
                            if i + 1 < len(events) and events[i + 1].get("type") == "assistant":
                                session_has_recovery = True
                elif event.get("type") == "user" and not event.get("isMeta"):
                    total_user_messages += 1
                    content = str(event.get("message", {}).get("content", ""))
                    # Check for test mentions in regular prompts
                    if "test" in content.lower():
                        test_patterns += 1
                    # Check for error patterns
                    if "error" in content.lower() or "bug" in content.lower():
                        session_has_error = True
            if session_has_error and session_has_recovery:
                error_recovery += 1

        review_pct = (review_usage / total_meta_commands * 100) if total_meta_commands > 0 else 0.0
        # Calculate test pattern prevalence from both meta and real user messages
        total_user_interactions = total_meta_commands + total_user_messages
        test_pct = (test_patterns / total_user_interactions * 100) if total_user_interactions > 0 else 0.0
        recovery_rate = (error_recovery / len(self.all_events) * 100) if self.all_events else 0.0

        return LogEvidence(
            dimension="Quality Controls",
            signals={
                "review_usage_pct": float(round(review_pct, 2)),
                "test_pattern_prevalence": float(round(test_pct, 2)),
                "error_recovery_rate": float(round(recovery_rate, 2)),
            },
            raw_metrics={
                "review_invocations": review_usage,
                "test_commands": test_patterns,
                "error_recovery_sessions": error_recovery,
                "total_error_patterns": error_patterns,
                "total_meta_commands": total_meta_commands,
                "total_user_messages": total_user_messages,
            },
            confidence="high" if total_meta_commands > 0 else "low",
        )

    def _extract_security_compliance(self) -> LogEvidence:
        """Extract signals: PII/data handling patterns, cache hit ratio."""
        if not self.sessions:
            return LogEvidence(
                dimension="Security & Compliance",
                signals={
                    "pii_handling_awareness": 0.0,
                    "cache_hit_ratio": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # PII awareness: count prompts mentioning security/pii terms
        pii_mentions = 0
        total_prompts = 0

        for events in self.all_events:
            for event in events:
                if event.get("type") == "user" and not event.get("isMeta"):
                    content = event.get("message", {}).get("content", "")
                    content_str = str(content)
                    if content_str:
                        total_prompts += 1
                        if any(term in content_str.lower() for term in ["pii", "password", "secret", "token", "credential", "secure"]):
                            pii_mentions += 1

        pii_awareness = (pii_mentions / total_prompts * 100) if total_prompts > 0 else 0.0

        # Cache hit ratio: aggregate from all sessions
        total_tokens = 0
        total_cache_read = 0

        for session in self.sessions:
            token_usage = session.get("token_usage", {})
            total_tokens += token_usage.get("total_tokens", 0)
            total_cache_read += token_usage.get("cache_read_input_tokens", 0)

        cache_ratio = (total_cache_read / total_tokens * 100) if total_tokens > 0 else 0.0

        return LogEvidence(
            dimension="Security & Compliance",
            signals={
                "pii_handling_awareness": float(round(pii_awareness, 2)),
                "cache_hit_ratio": float(round(cache_ratio, 2)),
            },
            raw_metrics={
                "pii_mentions": pii_mentions,
                "total_prompts_analyzed": total_prompts,
                "total_tokens": total_tokens,
                "cache_read_tokens": total_cache_read,
            },
            confidence="high" if total_tokens > 0 else "low",
        )

    def _extract_measurement_kpis(self) -> LogEvidence:
        """Extract signals: adoption trend, cycle time changes."""
        if not self.sessions:
            return LogEvidence(
                dimension="Measurement & KPIs",
                signals={
                    "adoption_trend": 0.0,
                    "cycle_time_avg_ms": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # Adoption trend: sessions per day
        start_dates = [
            s["metadata"].get("start_timestamp", "")[:10]
            for s in self.sessions
            if s["metadata"].get("start_timestamp")
        ]
        unique_days = len(set(start_dates))
        adoption_trend = len(self.sessions) / unique_days if unique_days > 0 else 0.0

        # Cycle time: average session duration
        durations = [
            s["metadata"].get("duration_ms")
            for s in self.sessions
            if s["metadata"].get("duration_ms")
        ]
        avg_cycle_time = sum(durations) / len(durations) if durations else 0.0

        return LogEvidence(
            dimension="Measurement & KPIs",
            signals={
                "adoption_trend": float(round(adoption_trend, 2)),
                "cycle_time_avg_ms": float(round(avg_cycle_time, 0)),
            },
            raw_metrics={
                "total_sessions": len(self.sessions),
                "unique_days": unique_days,
                "avg_session_duration_ms": avg_cycle_time,
                "session_count": len(durations),
            },
            confidence="high" if durations else "medium",
        )

    def _extract_ways_of_working(self) -> LogEvidence:
        """Extract signals: session opening patterns, plan mode usage."""
        if not self.all_events:
            return LogEvidence(
                dimension="Ways of Working",
                signals={
                    "session_opening_pattern": 0.0,
                    "plan_mode_usage": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # Session opening patterns: measure how sessions start (quick vs. deliberate)
        avg_opening_message_length = 0
        plan_mode_count = 0
        total_sessions = len(self.all_events)

        for events in self.all_events:
            # Look at first user message
            for event in events:
                if event.get("type") == "user" and not event.get("isMeta"):
                    content = event.get("message", {}).get("content", "")
                    content_str = str(content)
                    avg_opening_message_length += len(content_str.split())
                    if "/plan" in content_str.lower() or "plan" in content_str.lower():
                        plan_mode_count += 1
                    break

        avg_msg_length = (avg_opening_message_length / total_sessions) if total_sessions > 0 else 0.0
        plan_usage = (plan_mode_count / total_sessions * 100) if total_sessions > 0 else 0.0

        return LogEvidence(
            dimension="Ways of Working",
            signals={
                "session_opening_pattern": float(round(avg_msg_length, 2)),
                "plan_mode_usage": float(round(plan_usage, 2)),
            },
            raw_metrics={
                "avg_opening_message_words": avg_msg_length,
                "plan_mode_sessions": plan_mode_count,
                "total_sessions": total_sessions,
            },
            confidence="high" if total_sessions > 0 else "low",
        )

    def _extract_accountability_ownership(self) -> LogEvidence:
        """Extract signals: champion candidate patterns (git consistency)."""
        if not self.sessions:
            return LogEvidence(
                dimension="Accountability & Ownership",
                signals={
                    "git_consistency": 0.0,
                    "branch_discipline": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # Git consistency: check for consistent branch names across sessions
        branches = set()
        cwds = set()

        for session in self.sessions:
            metadata = session.get("metadata", {})
            branch = metadata.get("git_branch")
            cwd = metadata.get("cwd")
            if branch:
                branches.add(branch)
            if cwd:
                cwds.add(cwd)

        # Consistency score: fewer unique branches suggests more disciplined work
        unique_branches = len(branches)
        unique_cwds = len(cwds)
        sessions_count = len(self.sessions)

        # Lower ratio = more consistent (reusing branches)
        branch_discipline = (1.0 - (min(unique_branches, 5) / 5)) * 100 if unique_branches > 0 else 0.0
        git_consistency = (sessions_count / max(unique_branches, 1)) * 10  # Normalize to 0-100 range

        return LogEvidence(
            dimension="Accountability & Ownership",
            signals={
                "git_consistency": float(round(min(100, git_consistency), 2)),
                "branch_discipline": float(round(branch_discipline, 2)),
            },
            raw_metrics={
                "unique_branches": unique_branches,
                "unique_cwds": unique_cwds,
                "total_sessions": sessions_count,
                "branches": sorted(branches),
            },
            confidence="high" if branches else "low",
        )

    def _extract_scalability_knowledge_transfer(self) -> LogEvidence:
        """Extract signals: new dev ramp time (based on early-session patterns)."""
        if not self.sessions:
            return LogEvidence(
                dimension="Scalability & Knowledge Transfer",
                signals={
                    "new_dev_ramp_time": 0.0,
                    "documentation_patterns": 0.0,
                },
                raw_metrics={},
                confidence="low",
            )

        # New dev ramp time: estimate from session progression
        # Measure quality/confidence in early sessions vs. later ones
        early_session_quality = []
        late_session_quality = []
        doc_mentions = 0

        for i, events in enumerate(self.all_events):
            prompt_scores = score_session_prompts(events)
            if prompt_scores:
                avg_score = sum(s["score"] for s in prompt_scores) / len(prompt_scores)
                if i < len(self.all_events) // 3:
                    early_session_quality.append(avg_score)
                elif i >= (2 * len(self.all_events) // 3):
                    late_session_quality.append(avg_score)

            # Count documentation mentions
            for event in events:
                if event.get("type") == "user":
                    content = str(event.get("message", {}).get("content", ""))
                    if any(term in content.lower() for term in ["doc", "readme", "guide", "tutorial"]):
                        doc_mentions += 1

        early_avg = sum(early_session_quality) / len(early_session_quality) if early_session_quality else 0.0
        late_avg = sum(late_session_quality) / len(late_session_quality) if late_session_quality else 0.0

        # Ramp time: improvement from early to late sessions (positive = ramping up)
        ramp_improvement = (late_avg - early_avg) if early_session_quality and late_session_quality else 0.0
        doc_freq = (doc_mentions / len(self.all_events) * 100) if self.all_events else 0.0

        return LogEvidence(
            dimension="Scalability & Knowledge Transfer",
            signals={
                "new_dev_ramp_time": float(round(max(0, ramp_improvement), 2)),
                "documentation_patterns": float(round(doc_freq, 2)),
            },
            raw_metrics={
                "early_session_avg_quality": round(early_avg, 1),
                "late_session_avg_quality": round(late_avg, 1),
                "doc_mentions": doc_mentions,
                "total_sessions": len(self.all_events),
            },
            confidence="medium" if self.all_events else "low",
        )
