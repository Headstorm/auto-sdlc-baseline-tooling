import re

_ACTION_VERBS = {
    "fix", "add", "refactor", "update", "debug", "implement",
    "create", "remove", "test", "delete", "move", "rename",
    "change", "write", "build", "deploy", "install",
}

_FILE_PATH_PATTERN = re.compile(
    r'(src/|tests/|lib/|app/|\.py\b|\.ts\b|\.tsx\b|\.js\b|\.go\b|\.rs\b|/\w+\.\w{2,4})'
)

_LINE_REF_PATTERN = re.compile(
    r'\bline\s+\d+\b|\bL\d+\b', re.IGNORECASE
)

_ERROR_PATTERN = re.compile(
    r'(Error:|Traceback|Exception|TypeError|ValueError|KeyError|AttributeError|failed|crash)',
    re.IGNORECASE,
)


def score_prompt(text):
    """Score a prompt on 0-100 scale using rule-based heuristics."""
    words = text.split()
    word_count = len(words)
    first_five = [w.lower().strip(".,!?") for w in words[:5]]

    has_word_count = word_count >= 20
    has_file_ref = bool(_FILE_PATH_PATTERN.search(text))
    has_line_ref = bool(_LINE_REF_PATTERN.search(text))
    has_error_ref = bool(_ERROR_PATTERN.search(text))
    has_action_verb = bool(_ACTION_VERBS & set(first_five))

    score = (
        (30 if has_word_count else 0)
        + (25 if has_file_ref else 0)
        + (15 if has_line_ref else 0)
        + (15 if has_error_ref else 0)
        + (15 if has_action_verb else 0)
    )

    return {
        "score": score,
        "word_count": word_count,
        "has_word_count": has_word_count,
        "has_file_ref": has_file_ref,
        "has_line_ref": has_line_ref,
        "has_error_ref": has_error_ref,
        "has_action_verb": has_action_verb,
    }


def _extract_text(content):
    """Extract string text from a message content field (str or list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return " ".join(parts) if parts else None
    return None


def extract_real_prompts(events):
    """Return text of non-meta user messages from a session."""
    prompts = []
    for event in events:
        if event.get("type") != "user":
            continue
        if event.get("isMeta"):
            continue
        content = event.get("message", {}).get("content")
        text = _extract_text(content)
        if text and text.strip():
            prompts.append(text.strip())
    return prompts


def score_session_prompts(events):
    """Score all real user prompts in a session."""
    results = []
    for prompt in extract_real_prompts(events):
        scored = score_prompt(prompt)
        scored["prompt_preview"] = prompt[:120] + ("..." if len(prompt) > 120 else "")
        results.append(scored)
    return results
