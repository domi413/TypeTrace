"""Model layer for accessing keystrokes data from the TypeTrace database."""

from __future__ import annotations

import sqlite3

from gi.repository import GObject

from typetrace.config import DatabasePath, SQLStatistics


class Keystroke(GObject.Object):
    """Class to model keystrokes."""

    __gtype_name__ = "Keystroke"

    scan_code: int = GObject.Property(type=int, default=0)
    count: int = GObject.Property(type=int, default=0)
    key_name: str = GObject.Property(type=str, default="")
    date: str = GObject.Property(type=str, default="")

    def __init__(self, scan_code: int, count: int, key_name: str, date: str) -> None:
        """Initialize the Keystroke object."""
        super().__init__()
        self.scan_code = scan_code
        self.count = count
        self.key_name = key_name.replace("KEY_", "")
        self.date = date


class KeystrokeStore:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self) -> None:
        """Initialize the model with the database path."""
        self.db_path = DatabasePath.DB_PATH

    def get_all_keystrokes(self) -> list[Keystroke]:
        """Retrieve all keystrokes with their counts and names.

        Returns aggregated data across all dates.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLStatistics.GET_ALL_KEYSTROKES)
                rows = cursor.fetchall()

                # Convert rows to Keystroke objects
                return [
                    Keystroke(
                        scan_code=row[0],
                        count=row[1],
                        key_name=row[2],
                        date=row[3],
                    )
                    for row in rows
                ]
        except sqlite3.Error:
            return []

    def get_total_presses(self) -> int:
        """Get the total number of key presses across all keystrokes and all dates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLStatistics.GET_TOTAL_PRESSES)
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error:
            return 0

    def get_highest_count(self) -> int:
        """Retrieve the highest total count of any keystroke across all dates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLStatistics.GET_HIGHEST_COUNT)
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error:
            return 0

    def get_keystrokes_by_date(self, date: str) -> list[Keystroke]:
        """Retrieve keystrokes for a specific date.

        Args:
            date: Date in ISO format (YYYY-MM-DD)

        Returns:
            List of Keystroke objects for the specified date

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    SQLStatistics.GET_KEYSTROKES_BY_DATE,
                    (date,),
                )
                rows = cursor.fetchall()

                # Convert rows to Keystroke objects
                return [
                    Keystroke(
                        scan_code=row[0],
                        count=row[1],
                        key_name=row[2],
                        date=row[3],
                    )
                    for row in rows
                ]
        except sqlite3.Error:
            return []

    def clear(self) -> bool:
        """Remove all entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLStatistics.CLEAR_KEYSTROKES)
                conn.commit()
        except sqlite3.Error:
            return False
        else:
            return True

    # Note: refactor every 'with' in this file to only use one connection
    def get_daily_keystroke_counts(self) -> list[dict]:
        """Get daily keystroke counts for the past 7 days.

        Returns:
            List of dictionaries with date and count for each day

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLStatistics.GET_DAILY_KEYSTROKE_COUNTS)
                rows = cursor.fetchall()

                return [
                    {
                        "date": row[0],
                        "count": row[1],
                    }
                    for row in rows
                ]
        except sqlite3.Error:
            return []
