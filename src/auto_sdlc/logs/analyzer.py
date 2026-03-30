"""Token and session metadata analyzer for Claude sessions."""


def extract_token_usage(events):
    """Sum token usage across all assistant turns in a session."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
    for event in events:
        if event.get("type") != "assistant":
            continue
        usage = event.get("message", {}).get("usage", {})
        for key in totals:
            totals[key] += usage.get(key, 0)
    totals["total_tokens"] = sum(totals.values())
    return totals


def extract_session_metadata(events):
    """Extract session-level metadata, preferring the turn_duration record."""
    meta = {
        "session_id": None,
        "duration_ms": None,
        "message_count": None,
        "slug": None,
        "cwd": None,
        "git_branch": None,
        "start_timestamp": None,
        "end_timestamp": None,
    }
    timestamps = []
    for event in events:
        if event.get("sessionId") and meta["session_id"] is None:
            meta["session_id"] = event["sessionId"]
        ts = event.get("timestamp")
        if ts:
            timestamps.append(ts)
        if event.get("type") == "system" and event.get("subtype") == "turn_duration":
            meta["duration_ms"] = event.get("durationMs")
            meta["message_count"] = event.get("messageCount")
            meta["slug"] = event.get("slug")
            meta["cwd"] = event.get("cwd")
            meta["git_branch"] = event.get("gitBranch")
    if timestamps:
        meta["start_timestamp"] = min(timestamps)
        meta["end_timestamp"] = max(timestamps)
    return meta


def aggregate_sessions(all_session_events):
    """Roll up stats across multiple sessions."""
    total_input = total_output = total_cache_read = total_cache_create = 0
    session_durations = []

    for events in all_session_events:
        usage = extract_token_usage(events)
        total_input += usage["input_tokens"]
        total_output += usage["output_tokens"]
        total_cache_read += usage["cache_read_input_tokens"]
        total_cache_create += usage["cache_creation_input_tokens"]
        meta = extract_session_metadata(events)
        if meta["duration_ms"] is not None:
            session_durations.append(meta["duration_ms"])

    avg_duration = (
        sum(session_durations) / len(session_durations) if session_durations else None
    )

    return {
        "total_sessions": len(all_session_events),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cache_read_tokens": total_cache_read,
        "total_cache_creation_tokens": total_cache_create,
        "total_tokens": total_input + total_output + total_cache_read + total_cache_create,
        "avg_session_duration_ms": avg_duration,
    }
