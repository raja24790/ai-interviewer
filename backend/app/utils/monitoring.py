"""Monitoring and observability utilities."""
from __future__ import annotations

import time
from functools import wraps
from typing import Callable

from prometheus_client import Counter, Histogram, Gauge
from ..utils.logging import get_logger

logger = get_logger("monitoring")

# Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

interview_sessions_created = Counter(
    "interview_sessions_created_total",
    "Total interview sessions created",
    ["role"],
)

interview_sessions_active = Gauge(
    "interview_sessions_active",
    "Number of active interview sessions",
)

attention_events_recorded = Counter(
    "attention_events_recorded_total",
    "Total attention events recorded",
    ["state"],
)

tts_generations_total = Counter(
    "tts_generations_total",
    "Total TTS generations",
    ["voice"],
)

tts_generation_duration_seconds = Histogram(
    "tts_generation_duration_seconds",
    "TTS generation duration in seconds",
    ["voice"],
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["provider", "status"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider"],
)

pdf_reports_generated = Counter(
    "pdf_reports_generated_total",
    "Total PDF reports generated",
)


def track_time(metric: Histogram, labels: dict | None = None):
    """Decorator to track execution time of a function."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


import asyncio
