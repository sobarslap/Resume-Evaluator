# 📄 Resume Evaluator

A free web app that ranks resumes against a job description. Paste a JD, upload PDF/DOCX
resumes, and get a ranked shortlist with scores, matching/missing skills, and a short verdict
per candidate. Built with [Streamlit](https://streamlit.io) and the [Groq](https://groq.com)
free tier.

## What it does
1. You paste a job description and upload one or more resumes (`.pdf` / `.docx`).
2. An LLM parses the JD into structured requirements and each resume into structured fields.
3. Each resume is scored 0–100 against the JD.
4. Results appear as a ranked table with per-candidate detail and a CSV download.

## Project layout
```
app.py            Streamlit UI and orchestration
evaluator/
  config.py       model id, constants, API-key loading
  models.py       pydantic models (JobD, Resume, Experience, MatchResult)
  extractors.py   read PDF/DOCX from uploaded bytes
  llm.py          Groq calls: parse JD, parse resume, score match
tests/            pytest (extraction + model guards, no network)
docs/             scope, specs, handoff
```

## Run locally
Needs [uv](https://docs.astral.sh/uv/) and a free Groq API key
(https://console.groq.com/keys).

```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Provide your key (either way works)
echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml
# or: export GROQ_API_KEY="gsk_your_key_here"

# 3. Run
uv run streamlit run app.py
```

Then open http://localhost:8501.

## Tests
```bash
uv run pytest
```

## Deploy free (Streamlit Community Cloud)
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io, sign in with GitHub, and click **New app**.
3. Pick this repo/branch and set the main file to `app.py`.
4. In **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Deploy. You get a free public URL.

## Notes
- **Zero spend:** Groq free tier + Streamlit Community Cloud.
- Groq's free tier can throttle very large batches; resumes are processed sequentially with
  automatic retry/backoff, and a file that fails is shown as an error row instead of crashing
  the run.
- Never commit `.streamlit/secrets.toml` — it is gitignored.
