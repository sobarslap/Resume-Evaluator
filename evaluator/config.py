"""Configuration: model id, constants, and API-key loading."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Groq model used for all LLM calls (free tier).
MODEL = "openai/gpt-oss-120b"

# Retry/backoff settings for Groq calls (free tier can rate-limit).
MAX_RETRIES = 4
BACKOFF_BASE_SECONDS = 2.0

# Accepted resume file types.
SUPPORTED_SUFFIXES = (".pdf", ".docx")


def get_api_key() -> str | None:
    """Return the Groq API key from Streamlit secrets or the environment.

    Checking st.secrets is wrapped in try/except so the module also works
    outside a Streamlit runtime (e.g. tests, scripts).
    """
    try:
        import streamlit as st

        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return str(key)
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")
