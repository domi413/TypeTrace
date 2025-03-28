"""Configuration settings for TypeTrace."""

from __future__ import annotations

from enum import IntEnum
from pathlib import Path
from typing import Final, TypedDict, final

import appdirs


@final
class Config:
    """Constants and global settings for TypeTrace."""

    # Constants
    PROJECT_VERSION: Final[str] = "0.1.0 (alpha)"

    PROJECT_NAME: Final[str] = "TypeTrace"
    APP_NAME: Final[str] = PROJECT_NAME.lower()
    DB_NAME: Final[str] = PROJECT_NAME + ".db"

    BUFFER_SIZE: Final[int] = 50
    BUFFER_TIMEOUT: Final[float] = 60.0

    # Global settings
    DEBUG: bool = False

    @staticmethod
    def resolve_db_path() -> Path:
        """Determine the database path using appdirs for cross-platform support."""
        data_dir = appdirs.user_data_dir(Config.APP_NAME)
        db_path = Path(data_dir) / Config.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        return db_path


class ExitCodes(IntEnum):
    """Standard exit codes for the application."""

    SUCCESS = 0
    PERMISSION_ERROR = 1
    RUNTIME_ERROR = 2
    DATABASE_ERROR = 3
    PLATFORM_ERROR = 4


class Event(TypedDict):
    """Type definition for event data."""

    scan_code: int
    name: str | tuple[str, ...]
