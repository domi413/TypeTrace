"""Logging configuration for TypeTrace."""

from __future__ import annotations

import logging

from backend.config import DEBUG


def setup_logging() -> None:
    """Configure logging based on debug mode."""
    level: int = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
