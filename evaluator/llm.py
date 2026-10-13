"""Groq-backed LLM calls: parse a JD, parse a resume, score a match.

Every call asks for JSON, guards the parse, and validates against a pydantic
model. Calls retry with exponential backoff on transient / rate-limit errors
(Groq free tier can throttle).
"""

from __future__ import annotations

import json
import time

from groq import Groq
from pydantic import BaseModel, ValidationError

from .config import BACKOFF_BASE_SECONDS, MAX_RETRIES, MODEL, get_api_key
from .models import JobD, MatchResult


class LLMError(RuntimeError):
    """Raised when the LLM call or its output cannot be used."""


def _client() -> Groq:
    key = get_api_key()
    if not key:
        raise LLMError(
            "GROQ_API_KEY is not set. Add it to the environment or "
            ".streamlit/secrets.toml."
        )
    return Groq(api_key=key)


def _chat_json(messages: list[dict]) -> str:
    """Call Groq for a JSON response, retrying on transient errors."""
    client = _client()
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as exc:  # groq raises various API errors
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
    raise LLMError(f"Groq request failed after {MAX_RETRIES} attempts: {last_error}")


def _parse_into(raw: str, model_cls: type[BaseModel]) -> BaseModel:
    """Parse JSON text and validate it against a pydantic model."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Model did not return valid JSON: {exc}") from exc
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise LLMError(f"Model output did not match the expected schema: {exc}") from exc


def parse_job_description(job_description: str) -> JobD:
    """Extract structured requirements from a job description."""
    schema = JobD.model_json_schema()
    system_prompt = f"""
You are an expert HR assistant. Analyze job descriptions and extract structured
information. Return ONLY valid JSON matching this schema:

{schema}

IMPORTANT:
- Do NOT return the schema itself (no "properties", "title", "type" keys).
- Fill the schema with information extracted from the job description.
- If minimum experience is not mentioned, return null.
- If a list has no information, return an empty list.
- Do not invent information.
"""
    user_prompt = f"Analyze the following job description:\n\n{job_description}"
    raw = _chat_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return _parse_into(raw, JobD)  # type: ignore[return-value]


def evaluate_resume(job: JobD, resume_text: str) -> MatchResult:
    """Read a resume and score it against the job description in one LLM call.

    Combining the old parse + score steps into a single request halves the
    number of API calls per resume (easier on the Groq free-tier limit).
    """
    schema = MatchResult.model_json_schema()
    system_prompt = f"""
You are an expert HR recruiter. You are given a structured job description and the
raw text of one candidate's resume. Read the resume (skills may appear anywhere:
a skills section, work experience, internships, or projects; include internships
as experience) and compare it against the job description.

Return ONLY valid JSON matching this schema:

{schema}

Fill it with:
- candidate_name: the candidate's name, taken from the resume.
- matching_skills: required/preferred skills the candidate clearly has.
- missing_skills: important required skills the candidate lacks.
- experience_met: true if the experience requirement is met, else false.
- score: overall match percentage from 0 to 100.
- verdict: one or two concise sentences summarizing the fit.

Rules:
- Do not invent information; judge only from the resume text.
- Do not return the schema itself (no "properties"/"title"/"type" keys).
"""
    user_prompt = f"""
JOB DESCRIPTION:
{job.model_dump_json(indent=2)}

CANDIDATE RESUME (raw text):
{resume_text}
"""
    raw = _chat_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return _parse_into(raw, MatchResult)  # type: ignore[return-value]
