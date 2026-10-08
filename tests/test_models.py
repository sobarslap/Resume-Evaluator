"""Tests for pydantic models and LLM output guards (no network needed)."""

import pytest

from evaluator import llm
from evaluator.models import Experience, JobD, MatchResult, Resume


def test_jobd_defaults():
    job = JobD()
    assert job.required_skills == []
    assert job.minimum_experience is None


def test_resume_roundtrip():
    resume = Resume(
        name="Jane Doe",
        skills=["Python"],
        experiences=[Experience(company="Acme", role="SDE")],
    )
    dumped = resume.model_dump()
    restored = Resume.model_validate(dumped)
    assert restored.name == "Jane Doe"
    assert restored.experiences[0].company == "Acme"


def test_matchresult_score_bounds():
    with pytest.raises(Exception):
        MatchResult(score=150)


def test_parse_into_valid_json():
    result = llm._parse_into('{"score": 80, "verdict": "Good fit"}', MatchResult)
    assert isinstance(result, MatchResult)
    assert result.score == 80


def test_parse_into_rejects_bad_json():
    with pytest.raises(llm.LLMError):
        llm._parse_into("not json", MatchResult)


def test_parse_into_rejects_bad_schema():
    with pytest.raises(llm.LLMError):
        llm._parse_into('{"score": "not a number"}', MatchResult)
