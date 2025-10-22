from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: str
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InterviewStartRequest(BaseModel):
    role: str = Field(default="general", description="Requested interview track")


class InterviewStartResponse(BaseModel):
    session_id: str
    questions: List[str]
    token: TokenResponse


class TranscriptAppendRequest(BaseModel):
    session_id: str
    text: str
    question_index: int = 0


class TranscriptPayload(BaseModel):
    question: str
    transcript: str
    recorded_at: datetime | None = None


class FinalizeReportRequest(BaseModel):
    session_id: str
    transcripts: List[TranscriptPayload]
    attention_summary: Optional[Dict[str, float]] = None


class ScoreBreakdown(BaseModel):
    clarity: int
    relevance: int
    structure: int
    conciseness: int
    confidence: int
    total: int
    commentary: Optional[str] = None


class QuestionReport(BaseModel):
    question: str
    transcript: str
    scores: ScoreBreakdown


class FinalizeReportResponse(BaseModel):
    session_id: str
    pdf_url: str
    summary: str
    questions: List[QuestionReport]


class AttentionSnapshotResponse(BaseModel):
    state: str = "unknown"
    score: Optional[float] = None
    last_event: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
