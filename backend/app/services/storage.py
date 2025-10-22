from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..deps import SettingsType, get_settings
from ..utils.logging import get_logger

logger = get_logger("storage")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def session_audio_dir(session_id: str, settings: SettingsType | None = None) -> Path:
    settings = settings or get_settings()
    return _ensure_dir(settings.audio_dir / session_id)


def session_transcript_path(session_id: str, settings: SettingsType | None = None) -> Path:
    settings = settings or get_settings()
    dir_ = _ensure_dir(settings.transcript_dir / session_id)
    return dir_ / "transcript.json"


def session_report_dir(session_id: str, settings: SettingsType | None = None) -> Path:
    settings = settings or get_settings()
    return _ensure_dir(settings.report_dir / session_id)


def session_avatar_dir(session_id: str, settings: SettingsType | None = None) -> Path:
    settings = settings or get_settings()
    return _ensure_dir(settings.avatar_dir / session_id)


def write_transcript(session_id: str, payload: dict[str, Any], settings: SettingsType | None = None) -> Path:
    path = session_transcript_path(session_id, settings=settings)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def read_transcript(session_id: str, settings: SettingsType | None = None) -> dict[str, Any] | None:
    path = session_transcript_path(session_id, settings=settings)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def purge_expired(settings: SettingsType | None = None) -> None:
    settings = settings or get_settings()
    cutoff = datetime.utcnow() - timedelta(days=settings.retention_days)
    for directory in (settings.audio_dir, settings.transcript_dir, settings.report_dir, settings.avatar_dir):
        if not directory.exists():
            continue
        for session_path in directory.iterdir():
            if not session_path.is_dir():
                continue
            if datetime.utcfromtimestamp(session_path.stat().st_mtime) < cutoff:
                logger.info("Removing expired directory %s", session_path)
                for item in session_path.glob("**/*"):
                    if item.is_file():
                        item.unlink(missing_ok=True)
                for item in sorted(session_path.glob("**/*"), reverse=True):
                    if item.is_dir():
                        item.rmdir()
                session_path.rmdir()
