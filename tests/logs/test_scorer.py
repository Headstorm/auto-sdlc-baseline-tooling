import pytest
from auto_sdlc.logs.scorer import score_prompt, extract_real_prompts, score_session_prompts


def test_score_high_quality_prompt():
    # 20+ words, file ref, line ref, error ref, action verb — all 5 criteria
    prompt = "Fix the authentication bug in src/auth.py at line 42 the TypeError is causing production failures and needs immediate attention right now"
    result = score_prompt(prompt)
    assert result["score"] == 100
    assert result["has_file_ref"] is True
    assert result["has_line_ref"] is True
    assert result["has_error_ref"] is True
    assert result["has_action_verb"] is True
    assert result["has_word_count"] is True


def test_score_vague_prompt():
    prompt = "it broken"
    result = score_prompt(prompt)
    assert result["score"] == 0
    assert result["has_file_ref"] is False
    assert result["has_action_verb"] is False


def test_score_medium_prompt():
    # word_count(30) + file_ref(25) + action_verb(15) = 70; no line/error
    prompt = "Add a new route handler to src/routes.py to support the user settings page with proper validation and authentication checks please"
    result = score_prompt(prompt)
    assert result["score"] == 70
    assert result["has_action_verb"] is True
    assert result["has_file_ref"] is True
    assert result["has_line_ref"] is False
    assert result["has_error_ref"] is False


def test_extract_real_prompts_excludes_meta(sample_session_lines):
    prompts = extract_real_prompts(sample_session_lines)
    assert len(prompts) == 1
    assert "Fix the login bug" in prompts[0]


def test_score_session_prompts_returns_list(sample_session_lines):
    results = score_session_prompts(sample_session_lines)
    assert len(results) == 1
    assert "score" in results[0]
    assert "prompt_preview" in results[0]
