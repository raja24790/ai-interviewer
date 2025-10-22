from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..db import session_scope
from ..deps import SettingsType, get_settings
from ..models import InterviewReport, InterviewSession
from ..schemas import FinalizeReportRequest, FinalizeReportResponse, QuestionReport, ScoreBreakdown
from ..services.auth import require_token
from ..services.llm import ask_llm
from ..services.pdf_report import create_pdf
from ..services.scoring import grade_transcripts
from ..services.storage import write_transcript
from ..utils.logging import get_logger

router = APIRouter(prefix="/report", tags=["report"])
logger = get_logger("report")


@router.post("/finalize", response_model=FinalizeReportResponse)
async def finalize_report(
    payload: FinalizeReportRequest,
    token_session: Annotated[str, Depends(require_token)],
    settings: Annotated[SettingsType, Depends(get_settings)],
) -> FinalizeReportResponse:
    if token_session != payload.session_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not match session")

    with session_scope() as db:
        session = db.get(InterviewSession, payload.session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        questions = session.questions

    transcripts = [item.transcript for item in payload.transcripts]
    scores = await grade_transcripts(questions, transcripts, settings=settings)

    # Ask LLM for final summary paragraph
    prompt = (
        "Generate a concise interview summary paragraph referencing overall performance and key strengths/areas." \
        "\nReturn plain text."\
    )
    summary_prompt = (
        f"Candidate session {payload.session_id} received the following feedback: {json.dumps(scores)}.\n"
        f"Produce a 3 sentence summary."
    )
    try:
        summary_text = await ask_llm(f"{prompt}\n{summary_prompt}", settings=settings)
    except Exception:
        summary_text = "Automated summary unavailable. Review the detailed scores above."

    question_reports = [
        QuestionReport(
            question=question,
            transcript=transcript,
            scores=ScoreBreakdown(**{k: v for k, v in score.items() if k in ScoreBreakdown.model_fields}),
        )
        for question, transcript, score in zip(questions, transcripts, scores)
    ]

    pdf_path = create_pdf(
        payload.session_id,
        [{"question": qr.question, "transcript": qr.transcript} for qr in question_reports],
        scores,
        payload.attention_summary,
        summary_text,
        settings=settings,
    )
    pdf_url = f"/reports/{payload.session_id}/final_report.pdf"

    report_record = InterviewReport(
        session_id=payload.session_id,
        summary=summary_text,
        scores={"questions": [score for score in scores]},
        pdf_path=str(pdf_path),
    )

    with session_scope() as db:
        db.add(report_record)
        db.commit()

    write_transcript(
        payload.session_id,
        {
            "questions": questions,
            "transcripts": [item.model_dump() for item in payload.transcripts],
            "scores": scores,
        },
        settings=settings,
    )

    logger.info("Report finalized for session=%s", payload.session_id)
    return FinalizeReportResponse(
        session_id=payload.session_id,
        pdf_url=pdf_url,
        summary=summary_text,
        questions=question_reports,
    )
