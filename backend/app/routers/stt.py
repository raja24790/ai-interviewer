from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from ..schemas import TranscriptAppendRequest
from ..services.auth import decode_token, require_token
from ..services.storage import read_transcript, write_transcript
from ..utils.logging import get_logger

router = APIRouter(prefix="/stt", tags=["speech"])
logger = get_logger("stt")


@router.post("/append")
async def append_transcript(
    payload: TranscriptAppendRequest,
    token_session: Annotated[str, Depends(require_token)],
) -> dict[str, str]:
    if token_session != payload.session_id:
        raise HTTPException(status_code=403, detail="Token does not match session")

    transcript = read_transcript(payload.session_id) or {"entries": []}
    transcript.setdefault("entries", []).append(
        {
            "question_index": payload.question_index,
            "text": payload.text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )
    write_transcript(payload.session_id, transcript)
    logger.debug("Transcript appended for session=%s", payload.session_id)
    return {"status": "ok"}


@router.websocket("/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str) -> None:  # pragma: no cover - websocket
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    if payload.sub != session_id:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            transcript = read_transcript(session_id) or {"entries": []}
            transcript.setdefault("entries", []).append(
                {
                    "question_index": 0,
                    "text": data,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
            )
            write_transcript(session_id, transcript)
            await websocket.send_json({"status": "ok"})
    except WebSocketDisconnect:
        logger.info("Websocket disconnected for session=%s", session_id)
