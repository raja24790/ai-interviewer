import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.getenv("LOG_DIR", "/data/logs")
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str, level=logging.INFO):
    """Return a configured logger. Multiple calls return the same logger instance (no duplicate handlers)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    handler = RotatingFileHandler(
        f"{LOG_DIR}/{name}.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
