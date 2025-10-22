from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import SettingsType, get_settings
from ..models import AttentionSnapshot, InterviewSession
from ..schemas import AttentionSnapshotResponse, InterviewStartRequest, InterviewStartResponse, TokenResponse
from ..services.auth import create_access_token
from ..services.storage import purge_expired
from ..utils.logging import get_logger
from ..db import session_scope

router = APIRouter(prefix="/interview", tags=["interview"])
logger = get_logger("interview")


QUESTION_BANK = {
    "general": [
        "Tell me about yourself.",
        "Describe a challenging project you worked on.",
        "How do you handle tight deadlines?",
        "What motivates you at work?",
        "Where do you see yourself in five years?",
    ],
    "engineering": [
        "Explain the SOLID principles.",
        "How do you ensure code quality in a large codebase?",
        "Describe a time you improved system performance.",
        "What is your approach to incident response?",
        "How do you mentor junior engineers?",
    ],
}


@router.post("/start", response_model=InterviewStartResponse)
async def start_interview(
    payload: InterviewStartRequest,
    settings: Annotated[SettingsType, Depends(get_settings)],
) -> InterviewStartResponse:
    purge_expired(settings=settings)
    role = payload.role.lower()
    questions = QUESTION_BANK.get(role, QUESTION_BANK["general"])

    session_id = secrets.token_hex(16)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.jwt_exp_minutes)
    with session_scope() as db:
        db.add(
            InterviewSession(
                session_id=session_id,
                role=role,
                questions=list(questions),
                expires_at=expires_at,
            )
        )
        db.commit()

    token = create_access_token(session_id=session_id, settings=settings)
    logger.info("Session %s started for role=%s", session_id, role)
    return InterviewStartResponse(
        session_id=session_id,
        questions=list(questions),
        token=TokenResponse(access_token=token),
    )


@router.get("/{session_id}/attention", response_model=AttentionSnapshotResponse)
async def get_attention_snapshot(session_id: str) -> AttentionSnapshotResponse:
    with session_scope() as db:
        snapshot = (
            db.query(AttentionSnapshot)
            .filter(AttentionSnapshot.session_id == session_id)
            .order_by(AttentionSnapshot.created_at.desc())
            .first()
        )
    if not snapshot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attention data not found")
    return AttentionSnapshotResponse(state=snapshot.state, score=snapshot.score, last_event=snapshot.last_event)
