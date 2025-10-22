# Setup Guide

This document describes how to bootstrap the AI Interviewer stack for local development and production validation.

## Prerequisites

* **Python 3.11** or newer
* **Node.js 20** or newer
* **Docker 24** or newer (for containerized workflows)
* `yarn` package manager

## Backend Environment

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy `.env.example` (create one if necessary) to `.env` and adjust values (OpenAI key, Ollama host, JWT secret, etc.).
4. Run migrations/initialization:
   ```bash
   python -m backend.app.main
   ```
   The application automatically provisions SQLite tables on startup.

### Validating key services

* **LLM integration** – Configure `LLM_PROVIDER` in the environment (`openai`, `ollama`, or `mock`). Use `mock` for offline development.
* **faster-whisper** – Run a quick smoke test:
  ```bash
  python - <<'PY'
  from faster_whisper import WhisperModel
  model = WhisperModel('small', device='cpu')
  segments, _ = model.transcribe('sample.wav')
  for s in segments:
      print(s.text)
  PY
  ```
* **Health endpoint** – `curl http://localhost:8000/health` should return `{"status":"ok"}`.

## Frontend Environment

1. Install dependencies and build the Next.js client:
   ```bash
   cd frontend
   yarn install
   yarn build
   ```
2. Local development server: `yarn dev` (uses `NEXT_PUBLIC_API_BASE` to reach the backend).

## Docker Compose

The root `docker-compose.yml` starts FastAPI, Next.js, and supporting services. Validate end-to-end with:

```bash
docker compose up --build
```

This spins up the backend on `:8000`, frontend on `:3000`, and the optional Nginx proxy (see `docker-compose.prod.yml`).

## Troubleshooting

* If the frontend cannot reach the API, confirm `NEXT_PUBLIC_API_BASE` and CORS origins in `.env`.
* Ensure Ollama or OpenAI credentials are reachable before enabling live AI grading.
* Logs rotate automatically into `/data/logs`. Inspect `app.log`, `llm.log`, and `scoring.log` for runtime issues.
