"""Model layer for accessing keystrokes data from the TypeTrace database."""

from __future__ import annotations

import sqlite3

from gi.repository import GObject

from backend.cli import resolve_db_path  # Shared path resolution


class Keystroke(GObject.Object):
    """Class to model keystrokes."""

    scan_code: int
    count: int
    key_name: str

    def __init__(self, scan_code: int, count: int, key_name: str) -> None:
        """Initialize the Keystroke object."""
        super().__init__()
        self.scan_code = scan_code
        self.count = count
        self.key_name = key_name


class KeystrokesModel:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self) -> None:
        """Initialize the model with the database path."""
        self.db_path = resolve_db_path()

    def get_all_keystrokes(self) -> list[Keystroke]:
        """Retrieve all keystrokes with their counts and names."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT scan_code, count, key_name FROM keystrokes")
                rows = cursor.fetchall()

                # Convert rows to Keystroke objects
                return [
                    Keystroke(scan_code=row[0], count=row[1], key_name=row[2])
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
                cursor.execute("SELECT SUM(count) FROM keystrokes")
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
