"""Structured logging configuration for the application.

Sets up a consistent logging format across all modules.  In development,
logs are human-readable.  The log level is driven entirely by
``settings.log_level`` so it can be overridden per environment without
touching source code.

Usage anywhere in the app:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Something happened", extra={"user_id": 42})
"""

import logging
import sys
from typing import Any

from app.core.config import settings

# ── Log record format ─────────────────────────────────────────────────────────
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Configure the root logger for the application.

    Call this once at application startup (inside ``create_application``).
    Subsequent ``logging.getLogger(__name__)`` calls in any module will
    automatically inherit this configuration.

    Behaviour:
    - Logs to stdout so container runtimes (Docker, Cloud Run) capture them.
    - Level is read from ``settings.log_level`` (default: INFO).
    - Suppresses noisy third-party loggers to WARNING.
    """
    log_level: int = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if called more than once (e.g., in tests)
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Quieten verbose third-party libraries
    for noisy in ("uvicorn.access", "multipart", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging is configured first.

    Args:
        name: Typically ``__name__`` from the calling module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)
