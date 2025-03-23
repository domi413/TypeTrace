"""Configuration settings for TypeTrace."""

from __future__ import annotations

from enum import IntEnum
from typing import Final, TypedDict, final


@final
class Config:
    """Constants and global settings for TypeTrace."""

    # Constants
    PROJECT_VERSION: Final[str] = "0.1.0 (alpha)"
    PROJECT_NAME: Final[str] = "TypeTrace"
    DB_NAME: Final[str] = "TypeTrace.db"
    BUFFER_SIZE: Final[int] = 50
    BUFFER_TIMEOUT: Final[float] = 60.0

    # Global settings
    DEBUG: bool = False


class ExitCodes(IntEnum):
    """Standard exit codes for the application."""

    SUCCESS = 0
    PERMISSION_ERROR = 1
    RUNTIME_ERROR = 2
    DATABASE_ERROR = 3


class KeyEvent(TypedDict):
    """Type definition for keyboard event data."""

    scan_code: int
    name: str | tuple[str, ...]
