"""Model layer for accessing keystrokes data from the TypeTrace database."""

from __future__ import annotations

import sqlite3

from backend.cli import CLI
from gi.repository import GObject


class Keystroke(GObject.Object):
    """Class to model keystrokes."""

    __gtype_name__ = "Keystroke"

    scan_code: int = GObject.Property(type=int, default=0)
    count: int = GObject.Property(type=int, default=0)
    key_name: str = GObject.Property(type=str, default="")

    def __init__(self, scan_code: int, count: int, key_name: str) -> None:
        """Initialize the Keystroke object."""
        super().__init__()
        self.scan_code = scan_code
        self.count = count
        self.key_name = key_name


class KeystrokeStore(GObject.Object):
    """Model for interacting with the keystrokes table in the database."""

    __gtype_name__ = "KeystrokeStore"

    refreshed = GObject.Signal("refreshed", return_type=None, arg_types=())

    def __init__(self) -> None:
        """Initialize the model with the database path."""
        super().__init__()
        self.db_path = CLI.resolve_db_path()

    def refresh(self) -> None:
        """Refresh the data from the database and emit the refreshed signal."""
        self.refreshed.emit()

    def get_all_keystrokes(self) -> list[Keystroke]:
        """Retrieve all keystrokes with their counts and names."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT 
                    k.scan_code, 
                    COALESCE(SUM(kl.key_count), 0) AS total_count, 
                    k.key_name 
                FROM keystrokes k
                LEFT JOIN keystroke_logs kl ON k.keystroke_id = kl.keystroke_id
                GROUP BY k.keystroke_id, k.key_name
                """)
                rows = cursor.fetchall()

                # Convert rows to Keystroke objects
                return [
                    Keystroke(
                        scan_code=row[0],
                        count=row[1],
                        key_name=row[2],
                    )
                    for row in rows
                ]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def get_total_presses(self) -> int:
        """Get the total number of key presses across all keystrokes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(key_count) FROM keystroke_logs")
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0

    def get_highest_count(self) -> int:
        """Retrieve the count of the most-used keystroke."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(key_count) FROM keystroke_logs")
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
