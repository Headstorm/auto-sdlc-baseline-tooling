import json
from unittest.mock import patch, MagicMock
from auto_sdlc.logs.qualitative import (
    run_llm,
    analyze_workflow_patterns,
    analyze_anti_patterns,
    analyze_maturity_narrative,
    run_full_qualitative_analysis,
)


def _mock_run(output, returncode=0):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = output
    return m


def test_run_llm_returns_stripped_output():
    with patch("subprocess.run", return_value=_mock_run("  hello world  ")):
        result = run_llm("some prompt")
    assert result == "hello world"


def test_run_llm_returns_none_on_nonzero():
    with patch("subprocess.run", return_value=_mock_run("error", returncode=1)):
        result = run_llm("some prompt")
    assert result is None


def test_run_llm_returns_none_on_file_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = run_llm("some prompt")
    assert result is None


def test_analyze_workflow_patterns_parses_json():
    fake = json.dumps({"workflows": [{"pattern": "Debugging", "evidence": "Many error prompts"}]})
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=fake):
        result = analyze_workflow_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert result["workflows"][0]["pattern"] == "Debugging"


def test_analyze_workflow_patterns_handles_bad_json():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value="not json"):
        result = analyze_workflow_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert "workflows" in result
    assert result["workflows"] == []


def test_analyze_anti_patterns_parses_json():
    fake = json.dumps({"anti_patterns": [{"name": "Vague prompts", "recommendation": "Add file refs"}]})
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=fake):
        result = analyze_anti_patterns({"sessions": [], "summary": {}, "user_id": "test"})
    assert result["anti_patterns"][0]["name"] == "Vague prompts"


def test_analyze_maturity_narrative_returns_string():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value="Strong usage overall."):
        result = analyze_maturity_narrative({"sessions": [], "summary": {}, "user_id": "test"})
    assert result == "Strong usage overall."


def test_run_full_qualitative_analysis_structure():
    with patch("auto_sdlc.logs.qualitative.run_llm", return_value=json.dumps({"workflows": [], "anti_patterns": []})):
        result = run_full_qualitative_analysis({"sessions": [], "summary": {}, "user_id": "test"})
    assert "workflow_patterns" in result
    assert "anti_patterns" in result
    assert "narrative" in result
