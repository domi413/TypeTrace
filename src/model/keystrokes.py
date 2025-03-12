"""Model layer for accessing keystrokes data from the TypeTrace database."""

from __future__ import annotations
from dataclasses import dataclass
import sqlite3

from backend.cli import resolve_db_path  # Shared path resolution


@dataclass
class Keystroke:
    scan_code: int
    count: int
    key_name: str | None  # key_name can be optional or unknown


class KeystrokesModel:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self):
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
