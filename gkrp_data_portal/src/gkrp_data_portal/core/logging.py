"""Logging configuration utilities."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    """Configure root logging.

    LOG_LEVEL is read from the environment and defaults to INFO.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
