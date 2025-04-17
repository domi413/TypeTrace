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
    PROJECT_VERSION: Final[str] = "0.1.0 (alpha)"

    PROJECT_NAME: Final[str] = "TypeTrace"
    APP_NAME: Final[str] = PROJECT_NAME.lower()
    DB_NAME: Final[str] = PROJECT_NAME + ".db"

    BUFFER_SIZE: Final[int] = 50
    BUFFER_TIMEOUT: Final[float] = 60.0

    IS_FLATPAK: Final[bool] = "FLATPAK_ID" in os.environ

    AUTOSTART_TARGET_DIR: Final[Path] = Path.home() / ".config" / "autostart"
    AUTOSTART_TARGET_FILE: Final[Path] = (
        AUTOSTART_TARGET_DIR / "typetrace-backend.desktop"
    )
    AUTOSTART_SOURCE: Final[Path] = (
        Path.home()
        / ".local"
        / "share"
        / ("flatpak/exports/share" if IS_FLATPAK else "")
        / "applications"
        / "typetrace-backend.desktop"
    )

    # Global settings
    DEBUG: bool = False

    # DB path
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


@final
class SQLStatistics:
    """SQL queries for frontend database operations."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    GET_ALL_KEYSTROKES = """
        SELECT scan_code, SUM(count) as total_count, key_name,
        MAX(date) as latest_date
        FROM keystrokes
        GROUP BY scan_code, key_name
        ORDER BY total_count DESC
    """

    GET_TOTAL_PRESSES = "SELECT SUM(count) FROM keystrokes"

    GET_HIGHEST_COUNT = """
        SELECT MAX(total_count) FROM (
            SELECT SUM(count) as total_count
            FROM keystrokes
            GROUP BY scan_code, key_name
        )
    """

    GET_KEYSTROKES_BY_DATE = """
        SELECT scan_code, count, key_name, date FROM keystrokes
        WHERE date = ?
    """

    GET_DAILY_KEYSTROKE_COUNTS = """
        SELECT date, SUM(count) as total_count
        FROM keystrokes
        WHERE date >= date('now', '-6 days')
        GROUP BY date
        ORDER BY date
    """

    CLEAR_KEYSTROKES = "DELETE FROM keystrokes"


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
