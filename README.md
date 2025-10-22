########################################
# README.md
########################################


# AI Interviewer (Prod-Ready Prototype)


**Stack**: Next.js (frontend), FastAPI (backend), faster-whisper (STT), client-side attention & phone detection via TensorFlow.js (FaceMesh + COCO-SSD), optional local LLM (Ollama) or API LLM, server TTS via `edge-tts` (or browser SpeechSynthesis).


**Key guarantees for a production-grade prototype**
- Strict TypeScript on frontend; Pydantic schemas on backend
- WebSocket session channel for real-time events (attention, question/answer)
- STT chunks with VAD and retry logic
- Pluggable LLM provider (Ollama / OpenAI-compatible / local GGUF via llama.cpp server)
- Deterministic scoring rubric + JSON report export
- Containerized with Docker Compose; stateless services + persistent volume for media/logs
- CORS hardened, rate limits, auth token per session


## Quick Start


```bash
# 1) Copy env and edit
cp .env.sample .env
# 2) Build & run
docker compose up --build
# 3) Open the app
# Frontend: http://localhost:3000
# Backend docs: http://localhost:8000/docs
```


### Requirements (host)
- Docker & Docker Compose
- (Optional) Ollama installed on host if you choose `LLM_PROVIDER=ollama`


### Environment


```
# .env
# Back-end
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
STORAGE_DIR=/data
LLM_PROVIDER=ollama # options: ollama | openai | none
OLLAMA_MODEL=llama3:8b
OPENAI_BASE_URL=
OPENAI_API_KEY=
TTS_VOICE=en-US-AriaNeural # used by edge-tts
SESSION_SECRET=change-me
RATE_LIMIT_PER_MIN=120


# Front-end
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_BASE=ws://localhost:8000
```


---
