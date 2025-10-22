from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..deps import SettingsType, get_settings
from ..utils.logging import get_logger

logger = get_logger("avatar")


def _video_path(session_id: str, question_index: int, settings: SettingsType) -> Path:
    directory = settings.avatar_dir / session_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"q{question_index:02d}.mp4"


def get_avatar_video(session_id: str, question_index: int, settings: SettingsType | None = None) -> Optional[Path]:
    settings = settings or get_settings()
    video_path = _video_path(session_id, question_index, settings)
    if video_path.exists():
        return video_path
    return None


def generate_avatar_video(
    session_id: str,
    question_index: int,
    audio_path: Path,
    settings: SettingsType | None = None,
) -> Optional[Path]:
    """Trigger Wav2Lip (or other provider) to generate the avatar video."""

    settings = settings or get_settings()
    try:
        import subprocess  # noqa: PLC0415
    except ImportError:  # pragma: no cover - subprocess always available
        subprocess = None  # type: ignore

    video_path = _video_path(session_id, question_index, settings)

    wav2lip_script = Path("/opt/wav2lip/inference.py")
    face_image = Path("/opt/wav2lip/assets/interviewer.jpg")

    if subprocess and wav2lip_script.exists() and face_image.exists():
        cmd = [
            "python",
            str(wav2lip_script),
            "--checkpoint_path",
            "/opt/wav2lip/checkpoints/wav2lip_gan.pth",
            "--face",
            str(face_image),
            "--audio",
            str(audio_path),
            "--outfile",
            str(video_path),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=300)
            if video_path.exists():
                return video_path
        except Exception as exc:  # pragma: no cover - depends on external tooling
            logger.exception("Avatar generation failed: %s", exc)
            return None

    logger.info("Avatar pipeline not configured; skipping video generation")
    return None
