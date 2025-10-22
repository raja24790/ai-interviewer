# API Reference

Base URL defaults to `http://localhost:8000`. All protected endpoints require a JWT `Authorization: Bearer <token>` header.

## Authentication

Tokens are issued by `/interview/start` and tied to a single interview session ID.

## Endpoints

### `POST /interview/start`
Start a new interview session.

**Request body**
```json
{ "role": "general" }
```

**Response**
```json
{
  "session_id": "...",
  "questions": ["Tell me about yourself", "..."],
  "token": { "access_token": "...", "token_type": "bearer" }
}
```

### `GET /interview/{session_id}/attention`
Return the latest attention snapshot captured by the monitoring service.

**Response**
```json
{ "state": "focused", "score": 0.92, "last_event": "looking_ahead" }
```

### `POST /stt/append`
Append streamed transcript text for a session/question.

**Headers** – `Authorization: Bearer <token>`

**Request body**
```json
{
  "session_id": "abc123",
  "text": "finalized speech chunk",
  "question_index": 0
}
```

### `POST /report/finalize`
Finalize grading, generate PDF, and persist the report.

**Headers** – `Authorization: Bearer <token>`

**Request body**
```json
{
  "session_id": "abc123",
  "transcripts": [
    { "question": "Tell me about yourself", "transcript": "..." }
  ],
  "attention_summary": { "focused_ratio": 0.8, "distracted_ratio": 0.2 }
}
```

**Response**
```json
{
  "session_id": "abc123",
  "pdf_url": "/reports/abc123/final_report.pdf",
  "summary": "Candidate showed strong communication skills...",
  "questions": [
    {
      "question": "Tell me about yourself",
      "transcript": "...",
      "scores": {
        "clarity": 4,
        "relevance": 5,
        "structure": 4,
        "conciseness": 4,
        "confidence": 5,
        "total": 22,
        "commentary": "LLM insights"
      }
    }
  ]
}
```

### `GET /health`
Simple readiness probe returning `{ "status": "ok" }`.

## Static Assets

* `/reports/<session_id>/final_report.pdf` – Generated PDF report.
* `/avatar/<session_id>/qXX.mp4` – Optional avatar lip-sync videos.
