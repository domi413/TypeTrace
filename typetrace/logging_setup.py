"""Logging configuration for TypeTrace."""

from __future__ import annotations

import logging
import platform
from enum import StrEnum
from typing import final

from config import Config


class LogColor(StrEnum):
    """ANSI color codes for logger."""

    RED = "\033[31m"
    RESET = "\033[0m"
    YELLOW = "\033[33m"


@final
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for specific log levels."""

    def __init__(self, **kwargs) -> None:
        """Initialize formatter with color support detection."""
        super().__init__(**kwargs)
        self.__use_colors = self._should_use_colors()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for warnings and errors."""
        original_levelname = record.levelname
        original_msg = record.msg

        if self.__use_colors:
            if record.levelno == logging.WARNING:
                record.levelname = (
                    f"{LogColor.YELLOW}{original_levelname}{LogColor.RESET}"
                )
                if isinstance(record.msg, str):
                    record.msg = f"{LogColor.YELLOW}{original_msg}{LogColor.RESET}"
            elif record.levelno >= logging.ERROR:
                record.levelname = f"{LogColor.RED}{original_levelname}{LogColor.RESET}"
                if isinstance(record.msg, str):
                    record.msg = f"{LogColor.RED}{original_msg}{LogColor.RESET}"

        result = super().format(record)
        record.levelname = original_levelname
        record.msg = original_msg

        return result

    def _should_use_colors(self) -> bool:
        """Determine if colors should be used based on platform."""
        return platform.system().lower() in ("linux", "darwin")


@final
class LoggerSetup:
    """Logger setup for TypeTrace."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    @staticmethod
    def setup_logging() -> None:
        """Configure logging based on DEBUG."""
        level: int = logging.DEBUG if Config.DEBUG else logging.INFO

        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear existing handlers
        root_logger.handlers.clear()

        root_logger.addHandler(handler)
