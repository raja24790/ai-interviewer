from __future__ import annotations

import logging
from datetime import datetime

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from .db import init_db, get_engine
from .deps import get_settings
from .models import InterviewSession
from .routers import interview, report, stt
from .schemas import HealthResponse
from .utils.logging import get_logger
from .db import session_scope

logger = get_logger("app", logging.INFO)


@asynccontextmanager
def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s in %s mode", settings.app_name, settings.environment)
    init_db()
    yield
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    if settings.force_https:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):  # pragma: no cover - simple passthrough
        return JSONResponse(status_code=429, content={'detail': 'Rate limit exceeded'})

    app.add_middleware(SlowAPIMiddleware)

    report_dir = settings.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/reports", StaticFiles(directory=str(report_dir), check_dir=False), name="reports")

    avatar_dir = settings.avatar_dir
    avatar_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/avatar", StaticFiles(directory=str(avatar_dir), check_dir=False), name="avatar")

    app.include_router(interview.router)
    app.include_router(stt.router)
    app.include_router(report.router)

    # Add Prometheus instrumentation
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse()

    @app.get("/health/detailed")
    async def detailed_health_check() -> dict:
        """Detailed health check with component status."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "components": {},
        }

        # Check database
        try:
            engine = get_engine()
            with session_scope() as db:
                # Simple query to check DB connection
                db.query(InterviewSession).limit(1).all()
            health_status["components"]["database"] = {
                "status": "healthy",
                "type": "sqlite" if "sqlite" in settings.database_url else "postgresql",
            }
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check storage directories
        try:
            storage_healthy = all(
                d.exists()
                for d in [
                    settings.data_dir,
                    settings.audio_dir,
                    settings.transcript_dir,
                    settings.report_dir,
                    settings.log_dir,
                ]
            )
            health_status["components"]["storage"] = {
                "status": "healthy" if storage_healthy else "unhealthy",
                "directories": {
                    "data": str(settings.data_dir),
                    "audio": str(settings.audio_dir),
                    "transcripts": str(settings.transcript_dir),
                    "reports": str(settings.report_dir),
                    "logs": str(settings.log_dir),
                },
            }
            if not storage_healthy:
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Check LLM provider configuration
        health_status["components"]["llm"] = {
            "provider": settings.llm_provider,
            "status": "configured"
            if settings.llm_provider == "mock"
            or (settings.llm_provider == "openai" and settings.openai_api_key)
            or settings.llm_provider == "ollama"
            else "not_configured",
        }

        return health_status

    return app


def get_app() -> FastAPI:
    return create_app()


app = create_app()
