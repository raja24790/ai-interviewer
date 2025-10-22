from __future__ import annotations

import json
import math
from typing import Any, Dict

from fastapi import HTTPException

from ..deps import SettingsType, get_settings
from ..utils.logging import get_logger
from .llm import ask_llm

logger = get_logger("scoring")


def score_answer(transcript: str) -> Dict[str, int]:
    words = transcript.split()
    word_count = len(words)
    clarity = min(5, max(1, math.ceil(word_count / 35)))
    relevance = 4 if word_count > 20 else 3
    structure = 4 if any(token in transcript.lower() for token in ("first", "then", "finally")) else 3
    conciseness = 5 if word_count < 120 else 3
    confidence = 4 if transcript.endswith(".") else 3
    total = clarity + relevance + structure + conciseness + confidence
    return {
        "clarity": clarity,
        "relevance": relevance,
        "structure": structure,
        "conciseness": conciseness,
        "confidence": confidence,
        "total": total,
    }


def _normalize_scores(raw: Dict[str, Any]) -> Dict[str, int]:
    normalized: Dict[str, int] = {}
    for key in ("clarity", "relevance", "structure", "conciseness", "confidence"):
        value = raw.get(key, 3)
        try:
            value_int = int(round(float(value)))
        except (TypeError, ValueError):
            value_int = 3
        normalized[key] = max(1, min(5, value_int))
    normalized["total"] = sum(normalized.values())
    return normalized


async def ai_grade_answer(question: str, transcript: str, settings: SettingsType | None = None) -> Dict[str, Any]:
    settings = settings or get_settings()
    base_scores = score_answer(transcript)
    prompt = (
        "Grade this interview answer on clarity, relevance, structure, conciseness, confidence. "
        "Return JSON with scores 1–5 per metric and a short commentary.\n"
        f"Question: {question}\nAnswer: {transcript}"
    )
    try:
        raw = await ask_llm(prompt, settings=settings)
    except Exception as exc:  # pragma: no cover - fallback path
        logger.exception("LLM grading failed; using heuristic fallback")
        return {**base_scores, "commentary": "LLM error: using heuristic scores", "error": str(exc)}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON response; using heuristic fallback")
        return {**base_scores, "commentary": "LLM response unparsable; using heuristic scores"}

    normalized = _normalize_scores(data)
    commentary = data.get("commentary") or data.get("summary")
    return {**normalized, "commentary": commentary or "LLM provided scores."}


async def grade_transcripts(
    questions: list[str],
    transcripts: list[str],
    settings: SettingsType | None = None,
) -> list[Dict[str, Any]]:
    if len(questions) != len(transcripts):
        raise HTTPException(status_code=400, detail="Question and transcript count mismatch")
    scores: list[Dict[str, Any]] = []
    for question, transcript in zip(questions, transcripts):
        scores.append(await ai_grade_answer(question, transcript, settings=settings))
    return scores
