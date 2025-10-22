from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class InterviewSession(SQLModel, table=True):
    session_id: str = Field(primary_key=True)
    role: str
    questions: list[str] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class InterviewReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    summary: str
    scores: dict[str, Any] = Field(sa_column=Column(JSON))
    pdf_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AttentionSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    state: str = "unknown"
    score: Optional[float] = None
    last_event: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
