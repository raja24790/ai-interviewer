"""Text-to-Speech service using edge-tts (Microsoft Edge TTS)."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from ..utils.logging import get_logger

logger = get_logger("tts")

# Voice options for different languages
VOICE_MAP = {
    "en-US-AriaNeural": "en-US",
    "en-US-GuyNeural": "en-US",
    "en-GB-SoniaNeural": "en-GB",
    "en-GB-RyanNeural": "en-GB",
    "es-ES-ElviraNeural": "es-ES",
    "fr-FR-DeniseNeural": "fr-FR",
    "de-DE-KatjaNeural": "de-DE",
    "it-IT-ElsaNeural": "it-IT",
    "pt-BR-FranciscaNeural": "pt-BR",
    "ja-JP-NanamiNeural": "ja-JP",
    "ko-KR-SunHiNeural": "ko-KR",
    "zh-CN-XiaoxiaoNeural": "zh-CN",
}


async def text_to_speech(
    text: str,
    output_path: Path | str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
) -> Path:
    """
    Convert text to speech using edge-tts.

    Args:
        text: The text to convert to speech
        output_path: Path where the audio file will be saved
        voice: Voice name (e.g., "en-US-AriaNeural")
        rate: Speech rate adjustment (e.g., "+10%", "-20%")
        volume: Volume adjustment (e.g., "+10%", "-10%")

    Returns:
        Path to the generated audio file

    Raises:
        RuntimeError: If edge-tts is not installed or TTS generation fails
    """
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError(
            "edge-tts is not installed. Install it with: pip install edge-tts"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Generating TTS for text (length=%d) with voice=%s", len(text), voice)

        # Create the TTS communicator
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)

        # Save to file
        await communicate.save(str(output_path))

        logger.info("TTS audio saved to %s (size=%d bytes)", output_path, output_path.stat().st_size)
        return output_path

    except Exception as e:
        logger.error("TTS generation failed: %s", e)
        raise RuntimeError(f"Failed to generate speech: {e}") from e


async def list_voices(language: str | None = None) -> list[dict]:
    """
    List available TTS voices.

    Args:
        language: Optional language filter (e.g., "en-US", "es-ES")

    Returns:
        List of voice information dictionaries

    Raises:
        RuntimeError: If edge-tts is not installed
    """
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError(
            "edge-tts is not installed. Install it with: pip install edge-tts"
        )

    try:
        voices = await edge_tts.list_voices()

        # Filter by language if specified
        if language:
            voices = [v for v in voices if v.get("Locale", "").startswith(language)]

        return voices

    except Exception as e:
        logger.error("Failed to list voices: %s", e)
        raise RuntimeError(f"Failed to list voices: {e}") from e


def text_to_speech_sync(
    text: str,
    output_path: Path | str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    volume: str = "+0%",
) -> Path:
    """
    Synchronous wrapper for text_to_speech.

    Args:
        text: The text to convert to speech
        output_path: Path where the audio file will be saved
        voice: Voice name (e.g., "en-US-AriaNeural")
        rate: Speech rate adjustment (e.g., "+10%", "-20%")
        volume: Volume adjustment (e.g., "+10%", "-10%")

    Returns:
        Path to the generated audio file

    Raises:
        RuntimeError: If edge-tts is not installed or TTS generation fails
    """
    return asyncio.run(text_to_speech(text, output_path, voice, rate, volume))


async def generate_question_audio(
    question: str,
    question_index: int,
    output_dir: Path,
    voice: str = "en-US-AriaNeural",
) -> Path:
    """
    Generate audio for an interview question.

    Args:
        question: The question text
        question_index: Index of the question (for filename)
        output_dir: Directory to save the audio file
        voice: Voice name to use

    Returns:
        Path to the generated audio file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"question_{question_index:02d}.mp3"
    output_path = output_dir / filename

    # Skip if already exists
    if output_path.exists():
        logger.info("Question audio already exists: %s", output_path)
        return output_path

    await text_to_speech(question, output_path, voice=voice)
    return output_path


async def generate_all_questions_audio(
    questions: list[str],
    output_dir: Path,
    voice: str = "en-US-AriaNeural",
) -> list[Path]:
    """
    Generate audio files for all interview questions.

    Args:
        questions: List of question texts
        output_dir: Directory to save audio files
        voice: Voice name to use

    Returns:
        List of paths to generated audio files
    """
    tasks = [
        generate_question_audio(q, i, output_dir, voice)
        for i, q in enumerate(questions)
    ]

    audio_files = await asyncio.gather(*tasks)
    logger.info("Generated audio for %d questions in %s", len(audio_files), output_dir)
    return audio_files


# Example usage and testing
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python tts.py <text> [output_file] [voice]")
            print("\nAvailable voices:")
            try:
                voices = await list_voices()
                for v in voices[:10]:  # Show first 10
                    print(f"  - {v.get('ShortName')}: {v.get('FriendlyName')}")
            except Exception as e:
                print(f"Error listing voices: {e}")
            return

        text = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "output.mp3"
        voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-AriaNeural"

        try:
            result = await text_to_speech(text, output, voice)
            print(f"Successfully generated: {result}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(main())
