# Scope — Resume Evaluator

## One-liner
A free web app where a recruiter pastes a job description, uploads a batch of PDF/DOCX
resumes, and gets a ranked list of candidates with scores, matching/missing skills, and a
short verdict.

## Users & core value
- **User:** a recruiter / hiring person (or a student screening their own resume).
- **Core value:** turn a pile of resumes + one JD into a ranked shortlist in minutes,
  without reading each one by hand.

## In the first launch
- Paste a job description (text).
- Upload one or more resumes (`.pdf`, `.docx`).
- LLM parses the JD into structured requirements.
- LLM parses each resume into structured fields.
- LLM scores each resume against the JD (0–100) with matching/missing skills + verdict.
- Results shown as a ranked table, highest score first, with per-candidate detail.
- Download results as CSV.

## Out of first launch (later, maybe)
- Accounts / saved history.
- Bulk async processing / queues.
- `.txt` / `.doc` / image-scan (OCR) resumes.
- Editing or re-weighting the scoring criteria in the UI.

## Constraints (standing)
- **Zero spend.** Groq free tier for the LLM, Streamlit Community Cloud for hosting.
- Learning project; readable, modular code over cleverness.
- Must be deployable to a free public URL.

## Risks
- Groq free-tier rate limits on large batches → sequential calls + exponential backoff,
  and a UI note that very large batches may be throttled.
- LLM returning invalid JSON → guarded parse + pydantic validation; a bad file becomes an
  error row instead of crashing the batch.

## Status
- [x] Scope written
- [ ] Stack & scaffold
- [ ] Models & config
- [ ] Text extraction
- [ ] LLM layer
- [ ] UI (inputs + results)
- [ ] Tests + deploy
