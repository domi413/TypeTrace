"""Configuration settings for TypeTrace."""

from __future__ import annotations

import os
from enum import IntEnum
from pathlib import Path
from typing import Final, TypedDict, final

import appdirs


@final
class Config:
    """Constants and global settings for TypeTrace."""

    # Constants
    PROJECT_VERSION: Final[str] = os.getenv("TYPETRACE_VERSION")

    PROJECT_NAME: Final[str] = "TypeTrace"
    APP_NAME: Final[str] = PROJECT_NAME.lower()
    DB_NAME: Final[str] = PROJECT_NAME + ".db"

    BUFFER_SIZE: Final[int] = 50
    BUFFER_TIMEOUT: Final[float] = 60.0

    IS_FLATPAK: Final[bool] = "FLATPAK_ID" in os.environ

    AUTOSTART_TARGET_DIR: Final[Path] = Path.home() / ".config" / "autostart"
    AUTOSTART_TARGET_FILE: Final[Path] = (
        AUTOSTART_TARGET_DIR / "edu.ost.typetrace.desktop"
    )
    AUTOSTART_SOURCE: Final[Path] = (
        Path.home()
        / "@datadir@" # This is changed by meson depending on install prefix
        / "applications"
        / "edu.ost.typetrace-backend.desktop"
    )

    # Global settings
    DEBUG: bool = False

    @classmethod
    def resolve_db_path(cls) -> Path:
        """Determine the database path using appdirs for cross-platform support."""
        data_dir = appdirs.user_data_dir(cls.APP_NAME)
        db_path = Path(data_dir) / cls.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path


class DatabasePath:
    """Constant for database path."""

    DB_PATH: Final[Path] = Config.resolve_db_path()


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
    date: str
