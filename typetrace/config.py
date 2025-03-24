"""Configuration settings for TypeTrace."""

from pathlib import Path
from typing import Final

import appdirs


def resolve_db_path() -> Path:
    """Determine the database path using appdirs for cross-platform support."""
    app_name = PROJECT_NAME.lower()
    data_dir = appdirs.user_data_dir(app_name)
    db_path = Path(data_dir) / DB_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path.absolute().as_posix()

# Constants
PROJECT_VERSION: Final[str] = "0.1.0"
PROJECT_NAME: Final[str] = "TypeTrace"
DB_NAME: Final[str] = "TypeTrace.db"
DB_PATH: Final[str] = resolve_db_path()

# Global settings
DEBUG: bool = False
