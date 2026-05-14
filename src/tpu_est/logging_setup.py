"""Configure structured JSON logging for the TPU estimation worker."""

import logging
from collections.abc import Mapping
from typing import Final

import structlog

_LOG_LEVELS: Final[Mapping[str, int]] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog to emit one JSON object per line to stdout."""
    normalized_level = level.upper()
    logging_level = _LOG_LEVELS.get(normalized_level)
    if logging_level is None:
        supported_levels = ", ".join(_LOG_LEVELS)
        raise ValueError(f"Unknown logging level {level!r}; expected one of: {supported_levels}")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
