from __future__ import annotations

import json
from typing import Any

import httpx

from ..deps import SettingsType, get_settings
from ..utils.logging import get_logger

logger = get_logger("llm")


async def _ask_openai(prompt: str, settings: SettingsType) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "You are an expert interview evaluator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    message = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not message:
        raise RuntimeError("OpenAI response missing content")
    return message


async def _ask_ollama(prompt: str, settings: SettingsType) -> str:
    url = f"{settings.ollama_host.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": "You are an expert interview evaluator."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    message = data.get("message", {}).get("content")
    if not message and "choices" in data:
        message = data["choices"][0]["message"]["content"]
    if not message:
        raise RuntimeError("Ollama response missing content")
    return message


async def ask_llm(prompt: str, settings: SettingsType | None = None) -> str:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    logger.info("Dispatching prompt via provider=%s", provider)

    if provider == "openai":
        return await _ask_openai(prompt, settings)
    if provider == "ollama":
        return await _ask_ollama(prompt, settings)

    # default mock for development/testing
    logger.warning("Using mock LLM provider; returning heuristic result")
    if "Grade this interview answer" in prompt:
        fake = {
            "clarity": 4,
            "relevance": 4,
            "structure": 4,
            "conciseness": 4,
            "confidence": 4,
            "commentary": "Mock evaluation. Configure an LLM provider for real grading.",
        }
        return json.dumps(fake)

    return "Mock response: provide a valid LLM provider for richer insights."
