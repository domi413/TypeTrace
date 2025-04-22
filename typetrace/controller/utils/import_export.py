"""Utility for import and export of the database."""

import shutil
from pathlib import Path

from typetrace.config import DatabasePath


def export_database(dest_path: Path) -> bool:
    """Export the database to the specified destination path."""
    try:
        shutil.copy2(DatabasePath.DB_PATH, dest_path)
    except OSError:
        return False
    else:
        return True

def import_database(src_path: Path) -> bool:
    """Import database from the source path, overwriting the current one."""
    try:
        DatabasePath.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, DatabasePath.DB_PATH)
    except OSError:
        return False
    else:
        return True
