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

    # DB path
    @classmethod
    def resolve_db_path(cls) -> Path:
        """Determine the database path using appdirs for cross-platform support."""
        data_dir = appdirs.user_data_dir(cls.APP_NAME)
        db_path = Path(data_dir) / cls.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
