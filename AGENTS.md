# AGENTS.md — Coding rules for Resume Evaluator

These rules apply to any agent or contributor working in this repo.

## Rules
- **Zero spend.** Never suggest anything that costs money. Groq free tier for the LLM,
  Streamlit Community Cloud for hosting, free libraries only.
- **Simplest code that works.** No extra libraries, no frameworks, no premature abstraction.
  Prefer standard library and the already-chosen deps. Delete code rather than add flags.
- **Keep state in the files.** Scope lives in `docs/scope/scope.md`, specs in `docs/specs/`,
  handoff in `docs/handoff.md`. A new chat should resume from these, not from scratch.
- **Never commit secrets.** `GROQ_API_KEY` comes from `st.secrets` or the environment.
  `.streamlit/secrets.toml` and `.env` are gitignored. Never hard-code a key.
- **Groq free-tier aware.** Calls are sequential with exponential backoff on rate-limit /
  transient errors. One bad resume must never crash the whole batch — isolate it as an error row.
- **Structured LLM output.** Every LLM call returns JSON validated against a pydantic model.
  Guard `json.loads` and validation; surface failures as clear messages.

## Project layout
- `app.py` — Streamlit UI and orchestration only.
- `evaluator/` — reusable logic: `config.py`, `models.py`, `extractors.py`, `llm.py`.
- `tests/` — pytest; extraction and model schema tests run without network.

## Run
- Local: `uv run streamlit run app.py` (needs `GROQ_API_KEY` in env or `.streamlit/secrets.toml`).
- Tests: `uv run pytest`.
