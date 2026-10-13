"""Resume Evaluator — Streamlit web app.

Paste a job description, upload PDF/DOCX resumes, and get a ranked shortlist.
"""

from __future__ import annotations

import csv
import io

import streamlit as st

from evaluator.config import get_api_key
from evaluator.extractors import UnsupportedFileError, extract_text
from evaluator.llm import LLMError, evaluate_resume, parse_job_description
from evaluator.models import JobD

st.set_page_config(page_title="Resume Evaluator", page_icon="📄", layout="wide")


@st.cache_data(show_spinner=False)
def _parse_jd_cached(job_description: str) -> dict:
    """Parse the JD once per unique text; cache the dict form."""
    return parse_job_description(job_description).model_dump()


@st.cache_data(show_spinner=False)
def _evaluate_cached(jd_json: str, filename: str, data: bytes) -> dict:
    """Extract + score one resume. Cached on (JD, filename, bytes) so an
    identical re-run makes no new API calls."""
    job = JobD.model_validate_json(jd_json)
    text = extract_text(filename, data)
    if not text.strip():
        raise ValueError("No readable text found in the file.")
    return evaluate_resume(job, text).model_dump()


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


MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

# --- Header ---------------------------------------------------------------
st.title("📄 Resume Evaluator")
st.caption("Rank resumes against a job description. Free, powered by Groq.")
st.caption("How it works:  1) Paste a job description   2) Upload resumes   3) Click Evaluate")

if not get_api_key():
    st.warning(
        "No GROQ_API_KEY found. Set it in the environment or "
        "`.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`). "
        "Get a free key at https://console.groq.com/keys."
    )

# --- Inputs ---------------------------------------------------------------
col_jd, col_files = st.columns(2)
with col_jd:
    job_description = st.text_area(
        "Job description",
        height=300,
        placeholder="Paste the full job description here...",
        help="Paste the complete listing — required skills, experience, responsibilities. "
        "A fuller description gives more accurate scoring.",
    )
with col_files:
    uploaded = st.file_uploader(
        "Resumes (PDF or DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Upload one or more resumes. Add several to see them ranked against each other.",
    )
    if uploaded:
        st.caption(f"✅ {len(uploaded)} resume{'s' if len(uploaded) != 1 else ''} ready")
    else:
        st.caption("No resumes added yet.")

has_inputs = bool(job_description.strip()) and bool(uploaded)
evaluate = st.button(
    "Evaluate",
    type="primary",
    use_container_width=True,
    disabled=not has_inputs,
)
if not has_inputs:
    st.caption("Add a job description and at least one resume to enable Evaluate.")

# --- Run ------------------------------------------------------------------
if evaluate:
    if not get_api_key():
        st.error("Cannot run without a GROQ_API_KEY.")
        st.stop()

    try:
        with st.spinner("Reading the job description..."):
            jd_dict = _parse_jd_cached(job_description)
            job = JobD.model_validate(jd_dict)
    except LLMError as exc:
        st.error(f"Could not parse the job description: {exc}")
        st.stop()

    jd_json = job.model_dump_json()
    rows: list[dict] = []
    progress = st.progress(0.0, text="Evaluating resumes...")
    total = len(uploaded)

    for i, file in enumerate(uploaded, start=1):
        progress.progress(i / total, text=f"Evaluating {file.name} ({i}/{total})")
        try:
            result = _evaluate_cached(jd_json, file.name, file.getvalue())
            rows.append(
                {
                    "candidate_name": result.get("candidate_name") or file.name,
                    "score": round(result.get("score", 0.0), 1),
                    "experience_met": result.get("experience_met"),
                    "matching_skills": result.get("matching_skills", []),
                    "missing_skills": result.get("missing_skills", []),
                    "verdict": result.get("verdict", ""),
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

    st.divider()

    # --- Results ----------------------------------------------------------
    if ok_rows:
        best = ok_rows[0]
        st.success(f"🥇 Best match: **{best['candidate_name']}** — {best['score']}%")

        scores = [r["score"] for r in ok_rows]
        m1, m2, m3 = st.columns(3)
        m1.metric("Resumes evaluated", len(ok_rows))
        m2.metric("Top score", f"{max(scores):.0f}%")
        m3.metric("Average score", f"{sum(scores) / len(scores):.0f}%")

        st.subheader("Ranked candidates")
        table = [
            {
                "Rank": f"{MEDALS.get(r['rank'], '')} {r['rank']}".strip(),
                "Candidate": r["candidate_name"],
                "Score": r["score"],
                "Experience met": "✅ Yes"
                if r["experience_met"]
                else ("❌ No" if r["experience_met"] is False else "—"),
                "Matching skills": ", ".join(r["matching_skills"]),
                "Missing skills": ", ".join(r["missing_skills"]),
            }
            for r in ok_rows
        ]
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
            },
        )

        st.subheader("Details")
        for r in ok_rows:
            with st.container(border=True):
                head = f"{MEDALS.get(r['rank'], '')} #{r['rank']} — {r['candidate_name']}".strip()
                st.markdown(f"### {head}  ·  {r['score']}%")
                left, right = st.columns([2, 1])
                with left:
                    st.markdown(f"**Verdict:** {r['verdict'] or '—'}")
                    st.markdown(
                        "**✅ Matching skills:** "
                        + (", ".join(r["matching_skills"]) or "—")
                    )
                    st.markdown(
                        "**⚠️ Missing skills:** "
                        + (", ".join(r["missing_skills"]) or "—")
                    )
                with right:
                    if r["experience_met"] is True:
                        st.success("Experience ✅ met")
                    elif r["experience_met"] is False:
                        st.error("Experience ❌ not met")
                    else:
                        st.info("Experience — unknown")

        st.download_button(
            "⬇️ Download results as CSV",
            data=_results_to_csv(ok_rows + err_rows),
            file_name="resume_evaluation.csv",
            mime="text/csv",
        )

    if err_rows:
        st.subheader("Could not process")
        with st.container(border=True):
            for r in err_rows:
                st.error(f"{r['file']}: {r['error']}")

    if not ok_rows and not err_rows:
        st.info("No results.")
