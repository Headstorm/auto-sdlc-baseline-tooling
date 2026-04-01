from auto_sdlc.logs.maturity import score_dimension, build_maturity_report


def test_score_dimension_boundaries():
    # prompting_sophistication thresholds: [0, 15, 30, 50, 70]
    assert score_dimension("prompting_sophistication", 0) == 0
    assert score_dimension("prompting_sophistication", 14) == 0
    assert score_dimension("prompting_sophistication", 15) == 1
    assert score_dimension("prompting_sophistication", 50) == 3
    assert score_dimension("prompting_sophistication", 70) == 4


def test_score_dimension_tooling():
    # tooling_adoption thresholds: [0, 0.05, 0.15, 0.30, 0.50]
    assert score_dimension("tooling_adoption", 0.0) == 0
    assert score_dimension("tooling_adoption", 0.05) == 1
    assert score_dimension("tooling_adoption", 0.50) == 4


def test_build_maturity_report_structure():
    behavioral = {
        "skill_invocation_ratio": 0.20,
        "sessions_per_day": 1.5,
        "avg_messages_per_session": 10,
    }
    token_agg = {
        "total_tokens": 1000,
        "total_cache_read_tokens": 800,
    }
    result = build_maturity_report(behavioral, avg_prompt_quality=55, token_usage_agg=token_agg)
    assert "overall_level" in result
    assert "overall_label" in result
    assert "dimensions" in result
    assert len(result["dimensions"]) == 5
    for dim in result["dimensions"].values():
        assert "label" in dim
        assert "level" in dim
        assert "level_label" in dim
        assert dim["level"] in range(5)


def test_build_maturity_report_overall_label():
    behavioral = {
        "skill_invocation_ratio": 0.50,
        "sessions_per_day": 3.0,
        "avg_messages_per_session": 25,
    }
    token_agg = {
        "total_tokens": 1000,
        "total_cache_read_tokens": 960,
    }
    result = build_maturity_report(behavioral, avg_prompt_quality=75, token_usage_agg=token_agg)
    assert result["overall_level"] == 4
    assert result["overall_label"] == "Expert"


def test_build_maturity_report_zero_tokens():
    behavioral = {"skill_invocation_ratio": 0, "sessions_per_day": 0, "avg_messages_per_session": 0}
    token_agg = {"total_tokens": 0, "total_cache_read_tokens": 0}
    result = build_maturity_report(behavioral, avg_prompt_quality=0, token_usage_agg=token_agg)
    assert result["overall_level"] == 0
    assert result["overall_label"] == "Beginner"
