def extract_behavioral_metrics(events):
    """Extract behavioral signals from one session's events."""
    user_messages = 0
    skill_invocations = 0
    tool_calls = 0
    tool_names = set()

    for event in events:
        if event.get("type") == "user":
            if event.get("isMeta"):
                skill_invocations += 1
            else:
                user_messages += 1
        elif event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls += 1
                        tool_names.add(block.get("name", "unknown"))

    return {
        "user_messages": user_messages,
        "skill_invocations": skill_invocations,
        "tool_calls": tool_calls,
        "unique_tools": sorted(tool_names),
    }


def aggregate_behavioral_metrics(all_session_events, total_days_active):
    """Roll up behavioral metrics across all sessions."""
    total_user = 0
    total_skills = 0
    total_tools = 0
    all_tools = set()
    msg_counts = []

    for events in all_session_events:
        m = extract_behavioral_metrics(events)
        total_user += m["user_messages"]
        total_skills += m["skill_invocations"]
        total_tools += m["tool_calls"]
        all_tools.update(m["unique_tools"])
        session_total = m["user_messages"] + m["skill_invocations"]
        if session_total > 0:
            msg_counts.append(session_total)

    total_messages = total_user + total_skills
    skill_ratio = (
        round(total_skills / total_messages, 3) if total_messages > 0 else 0.0
    )
    avg_msgs = (
        round(sum(msg_counts) / len(msg_counts), 1) if msg_counts else 0.0
    )
    sessions_per_day = (
        round(len(all_session_events) / total_days_active, 2)
        if total_days_active > 0 else 0.0
    )

    return {
        "total_user_messages": total_user,
        "total_skill_invocations": total_skills,
        "skill_invocation_ratio": skill_ratio,
        "total_tool_calls": total_tools,
        "unique_tools_used": sorted(all_tools),
        "avg_messages_per_session": avg_msgs,
        "sessions_per_day": sessions_per_day,
    }
