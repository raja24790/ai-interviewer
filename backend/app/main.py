from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from .db import init_db
from .deps import get_settings
from .routers import interview, report, stt
from .schemas import HealthResponse
from .utils.logging import get_logger

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

    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse()

    return app


def get_app() -> FastAPI:
    return create_app()


app = create_app()
