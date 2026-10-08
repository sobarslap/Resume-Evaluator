"""Resume Evaluator — Streamlit web app.

Paste a job description, upload PDF/DOCX resumes, and get a ranked shortlist.
"""

from __future__ import annotations

import csv
import io

import streamlit as st

from evaluator.config import get_api_key
from evaluator.extractors import UnsupportedFileError, extract_text
from evaluator.llm import LLMError, parse_job_description, parse_resume, score_match
from evaluator.models import JobD, MatchResult

st.set_page_config(page_title="Resume Evaluator", page_icon="📄", layout="wide")


@st.cache_data(show_spinner=False)
def _parse_jd_cached(job_description: str) -> dict:
    """Parse the JD once per unique text; cache the dict form."""
    return parse_job_description(job_description).model_dump()


def _results_to_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    fieldnames = [
        "rank",
        "candidate_name",
        "score",
        "experience_met",
        "matching_skills",
        "missing_skills",
        "verdict",
        "file",
        "error",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


st.title("📄 Resume Evaluator")
st.caption("Rank resumes against a job description. Free, powered by Groq.")

if not get_api_key():
    st.warning(
        "No GROQ_API_KEY found. Set it in the environment or "
        "`.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`). "
        "Get a free key at https://console.groq.com/keys."
    )

col_jd, col_files = st.columns(2)
with col_jd:
    job_description = st.text_area(
        "Job description", height=300, placeholder="Paste the full job description here..."
    )
with col_files:
    uploaded = st.file_uploader(
        "Resumes (PDF or DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )
    st.caption("Tip: Groq's free tier can throttle very large batches.")

evaluate = st.button("Evaluate", type="primary", use_container_width=True)

if evaluate:
    if not job_description.strip():
        st.error("Please paste a job description.")
        st.stop()
    if not uploaded:
        st.error("Please upload at least one resume.")
        st.stop()
    if not get_api_key():
        st.error("Cannot run without a GROQ_API_KEY.")
        st.stop()

    try:
        with st.spinner("Reading the job description..."):
            job = JobD.model_validate(_parse_jd_cached(job_description))
    except LLMError as exc:
        st.error(f"Could not parse the job description: {exc}")
        st.stop()

    with st.expander(f"Parsed role: {job.role or 'N/A'}", expanded=False):
        st.json(job.model_dump())

    rows: list[dict] = []
    progress = st.progress(0.0, text="Evaluating resumes...")
    total = len(uploaded)

    for i, file in enumerate(uploaded, start=1):
        progress.progress(i / total, text=f"Evaluating {file.name} ({i}/{total})")
        try:
            text = extract_text(file.name, file.getvalue())
            if not text.strip():
                raise ValueError("No readable text found in the file.")
            resume = parse_resume(text)
            result: MatchResult = score_match(job, resume)
            rows.append(
                {
                    "candidate_name": result.candidate_name or resume.name or file.name,
                    "score": round(result.score, 1),
                    "experience_met": result.experience_met,
                    "matching_skills": result.matching_skills,
                    "missing_skills": result.missing_skills,
                    "verdict": result.verdict,
                    "file": file.name,
                    "error": "",
                }
            )
        except (UnsupportedFileError, LLMError, ValueError) as exc:
            rows.append(
                {
                    "candidate_name": file.name,
                    "score": None,
                    "experience_met": None,
                    "matching_skills": [],
                    "missing_skills": [],
                    "verdict": "",
                    "file": file.name,
                    "error": str(exc),
                }
            )

    progress.empty()

    ok_rows = [r for r in rows if r["error"] == ""]
    err_rows = [r for r in rows if r["error"] != ""]
    ok_rows.sort(key=lambda r: r["score"], reverse=True)
    for rank, row in enumerate(ok_rows, start=1):
        row["rank"] = rank

    st.subheader(f"Results — {len(ok_rows)} ranked, {len(err_rows)} failed")

    if ok_rows:
        table = [
            {
                "Rank": r["rank"],
                "Candidate": r["candidate_name"],
                "Score": r["score"],
                "Experience met": r["experience_met"],
                "Matching": ", ".join(r["matching_skills"]),
                "Missing": ", ".join(r["missing_skills"]),
            }
            for r in ok_rows
        ]
        st.dataframe(table, use_container_width=True, hide_index=True)

        for r in ok_rows:
            with st.expander(f"#{r['rank']} — {r['candidate_name']} ({r['score']}%)"):
                st.markdown(f"**Verdict:** {r['verdict'] or '—'}")
                st.markdown(f"**Matching skills:** {', '.join(r['matching_skills']) or '—'}")
                st.markdown(f"**Missing skills:** {', '.join(r['missing_skills']) or '—'}")
                st.markdown(f"**Experience requirement met:** {r['experience_met']}")

        st.download_button(
            "Download results as CSV",
            data=_results_to_csv(ok_rows + err_rows),
            file_name="resume_evaluation.csv",
            mime="text/csv",
        )

    if err_rows:
        st.subheader("Could not process")
        for r in err_rows:
            st.error(f"{r['file']}: {r['error']}")
