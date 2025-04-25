"""Class used to manipulate the database file and initialize schema."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from typetrace.config import DatabasePath


class DatabaseManager:
    """Used for manipulations concerning the database file and schema."""

    def __init__(self) -> None:
        """Construct an instance of DatabaseManager."""
        self.db_path = Path(DatabasePath.DB_PATH)

    def initialize_database(self, db_path: str | Path) -> None:
        """Create the keystrokes table if it doesn't exist.

        Args:
            db_path: Path to the SQLite database file.

        """
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS keystrokes (
                scan_code INTEGER NOT NULL,
                count     INTEGER NOT NULL,
                key_name  TEXT    NOT NULL,
                date      TEXT    NOT NULL,
                UNIQUE(scan_code, key_name, date)
            )
            """,
        )
        conn.commit()
        conn.close()

    def export_database(self, dest_path: Path) -> bool:
        """Export the database to the specified destination path."""
        try:
            shutil.copy2(self.db_path, dest_path)
        except OSError:
            return False
        else:
            return True

    def import_database(self, src_path: Path) -> bool:
        """Import database from the source path, overwriting the current one."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, self.db_path)
        except OSError:
            return False
        else:
            return True
