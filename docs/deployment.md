# Deployment Guide

This document outlines production-ready deployment options for the AI Interviewer platform.

## Local Docker Compose

Use the default `docker-compose.yml` for local validation:

```bash
docker compose up --build
```

Backends run on `http://localhost:8000`, frontend on `http://localhost:3000`.

## Production Docker Compose

The included `docker-compose.prod.yml` adds an Nginx reverse proxy for TLS termination and shared hosting.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Ensure environment variables are provided via `.env` or the hosting platform.

## Nginx Proxy

`deploy/nginx.conf` terminates HTTPS and routes requests:

* `https://<host>` → Next.js frontend
* `https://<host>/api` → FastAPI backend (proxy pass to `backend:8000`)
* `wss://<host>/stt/stream` → WebSocket speech streaming

Update certificate paths (or use Certbot / managed TLS) before production launch.

## Cloudflare Tunnel

1. Install the `cloudflared` CLI.
2. Authenticate and create a tunnel pointing to the local proxy port (default 443).
3. Configure hostname routes for `/` (frontend) and `/api` (backend).

## Railway / Render

Deploy the backend and frontend as separate services:

* Backend – Docker build using `backend/Dockerfile`. Expose port 8000.
* Frontend – `frontend/Dockerfile` or managed Next.js build. Configure `NEXT_PUBLIC_API_BASE` to point to the backend URL.
* Optional – Deploy the proxy container for unified domains if the host does not provide routing.

## Environment Hardening

* Set `FORCE_HTTPS=true` to enable automatic HTTPS redirects.
* Populate `ALLOWED_ORIGINS` with trusted domains to lock down CORS.
* Configure `JWT_SECRET_KEY` and rotate regularly.
* Ensure `/data` volume is backed up and write-accessible.
* Monitor `/data/logs/*.log` and consider shipping to a centralized log platform.

## Data Retention

Audio, transcripts, reports, and avatar assets live under `/data`. The retention policy (`RETENTION_DAYS`) purges stale sessions automatically. Adjust according to compliance requirements.
