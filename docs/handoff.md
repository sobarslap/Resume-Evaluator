# Handoff

## Status: v1 built, verified locally, not yet deployed

### Done
- Scaffold: `uv` project, deps, `.gitignore`, `.streamlit/` config + secrets example.
- `evaluator/models.py` — JobD, Experience, Resume, structured MatchResult.
- `evaluator/config.py` — model id, retry settings, `get_api_key()` (st.secrets → env).
- `evaluator/extractors.py` — read PDF/DOCX from bytes; reject unsupported types.
- `evaluator/llm.py` — Groq calls with retry/backoff + guarded JSON/pydantic parsing.
- `app.py` — Streamlit UI: JD textarea + multi-upload, progress bar, ranked table,
  per-candidate expanders, CSV download, error rows for failed files.
- `tests/` — 11 tests passing (`uv run pytest`), no network needed.
- Streamlit app serves (headless smoke test returned HTTP 200).
- Docs: scope, spec 0001, AGENTS.md, README with run + deploy steps.

### Not yet done
- **Live LLM run with a real GROQ_API_KEY** — the LLM calls are structurally verified but
  have not been exercised against the real API (no key in this environment).
- **Push to GitHub** and **deploy to Streamlit Community Cloud** — awaiting user go-ahead.

### Next commands
```bash
# Try it for real locally (needs a key):
echo 'GROQ_API_KEY = "gsk_..."' > .streamlit/secrets.toml
uv run streamlit run app.py

# When ready to publish (only on user go-ahead):
git add -A && git commit -m "Resume evaluator web app (Streamlit)"
git push -u origin claude/determined-wright-8h1o6t
# then deploy on https://share.streamlit.io and set GROQ_API_KEY in Secrets
```
