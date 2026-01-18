"""Logging configuration utilities (Loguru-based)."""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Redirect standard logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the frame where the logging call originated (skip logging module frames)
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def _parse_level(level_name: str) -> str:
    """Normalize/validate level name for Loguru."""
    name = (level_name or "INFO").upper()
    # Loguru supports: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
    allowed = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
    return name if name in allowed else "INFO"


def configure_logging() -> None:
    """Configure application logging via Loguru.

    Environment variables:
      - LOG_LEVEL: default INFO
      - LOG_FILE: optional path to file sink
    """
    level = _parse_level(os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # 1) Remove default Loguru handler(s) and re-add with our formatting
    logger.remove()

    # Console sink
    logger.add(
        sys.stdout,
        level=level,
        backtrace=False,   # set True if you want richer tracebacks in dev
        diagnose=False,    # set True in dev; False in prod for performance/safety
        enqueue=True,      # safe for multi-thread / async usage
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "{message}"
        ),
    )

    # Optional file sink
    if log_file:
        logger.add(
            log_file,
            level=level,
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
        )

    # 2) Intercept stdlib logging and route to Loguru
    logging.root.handlers = [_InterceptHandler()]
    logging.root.setLevel(logging.getLevelName(level))

    # Ensure all existing loggers propagate to root (so they get intercepted)
    for logger_name in list(logging.root.manager.loggerDict.keys()):
        std_logger = logging.getLogger(logger_name)
        std_logger.handlers = []
        std_logger.propagate = True

    # 3) Reduce noise if desired (optional; uncomment as needed)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger.info("Logging configured (level={})", level)
