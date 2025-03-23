"""Logging configuration for TypeTrace."""

from __future__ import annotations

import logging
from enum import StrEnum

from backend.config import Config


class LogColor(StrEnum):
    """ANSI color codes for logger."""

    YELLOW = "\033[33m"
    RED = "\033[31m"
    RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for specific log levels."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for warnings and errors."""
        original_levelname = record.levelname
        original_msg = record.msg

        if record.levelno == logging.WARNING:
            record.levelname = f"{LogColor.YELLOW}{original_levelname}{LogColor.RESET}"
            if isinstance(record.msg, str):
                record.msg = f"{LogColor.YELLOW}{original_msg}{LogColor.RED}"
        elif record.levelno >= logging.ERROR:
            record.levelname = f"{LogColor.RED}{original_levelname}{LogColor.RESET}"
            if isinstance(record.msg, str):
                record.msg = f"{LogColor.RED}{original_msg}{LogColor.RESET}"

        result = super().format(record)
        record.levelname = original_levelname
        record.msg = original_msg

        return result


class LoggerSetup:
    """Logger setup for TypeTrace."""

    @staticmethod
    def setup_logging() -> None:
        """Configure logging based on debug mode."""
        level: int = logging.DEBUG if Config.DEBUG else logging.INFO

        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove any existing handlers to avoid duplicate logs
        for hdlr in root_logger.handlers[:]:
            root_logger.removeHandler(hdlr)

        root_logger.addHandler(handler)
