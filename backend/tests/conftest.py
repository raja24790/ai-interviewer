import asyncio
import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("LOG_DIR", "/tmp/ai-interviewer-test-logs")
Path(os.environ["LOG_DIR"]).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    base = tmp_path / "runtime"
    (base / "audio").mkdir(parents=True, exist_ok=True)
    (base / "transcripts").mkdir(parents=True, exist_ok=True)
    (base / "reports").mkdir(parents=True, exist_ok=True)
    (base / "avatar").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("DATA_DIR", str(base))
    monkeypatch.setenv("AUDIO_DIR", str(base / "audio"))
    monkeypatch.setenv("TRANSCRIPT_DIR", str(base / "transcripts"))
    monkeypatch.setenv("REPORT_DIR", str(base / "reports"))
    monkeypatch.setenv("AVATAR_DIR", str(base / "avatar"))
    monkeypatch.setenv("LOG_DIR", str(base / "logs"))
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    db_path = base / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from backend.app import db, deps  # pylint: disable=import-outside-toplevel
    from backend.app.main import create_app  # pylint: disable=import-outside-toplevel

    deps.get_settings.cache_clear()
    db._engine = None  # type: ignore[attr-defined]

    application = create_app()
    db.init_db()  # Create database tables for test
    yield application

    deps.get_settings.cache_clear()
    db._engine = None  # type: ignore[attr-defined]


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
