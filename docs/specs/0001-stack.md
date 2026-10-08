# Spec 0001 — Stack & Architecture

## Decision
Build the resume evaluator as a **Streamlit** web app in Python, deployed on
**Streamlit Community Cloud**. The LLM stays **Groq** (free tier), model
`openai/gpt-oss-120b`.

## Why
- Reuses the existing Python logic (Groq, pydantic, pypdf, python-docx) almost verbatim.
- Native file-upload + table/dataframe widgets; no separate frontend to build or host.
- Free deploy straight from a GitHub repo; `GROQ_API_KEY` stored as a Streamlit secret.
- Simplest thing that meets every constraint (zero-spend, deployable, learning).

## Architecture
```
app.py                     UI only: inputs, orchestration, results rendering
evaluator/
  config.py                model id, constants, API-key loading (st.secrets -> env)
  models.py                pydantic: JobD, Experience, Resume, MatchResult
  extractors.py            read_pdf / read_docx from in-memory bytes (BytesIO)
  llm.py                   Groq client + parse_job_description / parse_resume / score_match
```
Data flow: upload bytes -> `extractors` -> text -> `llm.parse_resume` -> `Resume`;
JD text -> `llm.parse_job_description` -> `JobD`; `(JobD, Resume)` -> `llm.score_match`
-> `MatchResult`. `app.py` sorts by score and renders.

## Key choices
- **In-memory extraction.** Streamlit uploads are `UploadedFile`; read via `io.BytesIO`,
  no temp files or `resumes/` folder.
- **Structured `MatchResult`** with explicit fields (candidate_name, matching_skills,
  missing_skills, experience_met, verdict, score) so the table renders cleanly.
- **Retry/backoff** around every Groq call; guarded JSON parse so one bad resume is isolated.
- **Cache the parsed JD** (`st.cache_data`) so re-runs don't re-call the LLM for the JD.

## Dependencies
streamlit, groq, pydantic, pypdf, python-docx, python-dotenv; pytest (dev). Managed by `uv`.
