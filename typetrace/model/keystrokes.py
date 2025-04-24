"""Model layer for accessing keystroke data from the TypeTrace database."""

from __future__ import annotations
import sqlite3
from gi.repository import GObject
from typetrace.config import DatabasePath
from typetrace.sql import SQLQueries


class Keystroke(GObject.Object):
    __gtype_name__ = "Keystroke"

    scan_code = GObject.Property(type=int, default=0)
    count     = GObject.Property(type=int, default=0)
    key_name  = GObject.Property(type=str, default="")
    date      = GObject.Property(type=str, default="")

    def __init__(self, scan_code: int, count: int, key_name: str, date: str = "") -> None:
        super().__init__()
        self.scan_code = scan_code
        self.count     = count
        self.key_name  = key_name.replace("KEY_", "")
        self.date      = date


class KeystrokeStore:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self) -> None:
        self.db_path = DatabasePath.DB_PATH

    def add(self, event: dict) -> bool:
        keys = event.get("key", [])
        if isinstance(keys, str):
            keys = [keys]

        for key in keys:
            # Ignore mouse clicks first
            if key in ["BTN_LEFT", "BTN_MOUSE", "BTN_RIGHT"]:
                print(f"Ignoring mouse click: {key}")
                continue
            # Get the scan_code from layouts.py
            scan_code = event.get("scan_code", get_scan_code(key, "en_US"))
            if scan_code == 0:
                print(f"Warning: No scan_code found for {key}, skipping...")
                continue
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT INTO keystrokes (scan_code, key_name, count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(scan_code) DO UPDATE SET
                            count = count + 1,
                            key_name = ?
                        """,
                        (scan_code, key, key),
                    )
                    conn.commit()
                print(f"Keystroke added successfully: {key} (scan_code={scan_code})")
            except sqlite3.Error as e:
                print(f"Error adding keystroke: {e}")
                return False
        return True

    def get_all_keystrokes(self) -> list[Keystroke]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.GET_ALL_KEYSTROKES)
                rows = cursor.fetchall()
            return [
                Keystroke(scan_code=r[0], count=r[1], key_name=r[2], date="")
                for r in rows
            ]
        except sqlite3.Error as e:
            print(f"Error retrieving keystrokes: {e}")
            return []

    def get_total_presses(self) -> int:
        """Get the total number of key presses across all keystrokes and all dates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.GET_TOTAL_PRESSES)
                result = cursor.fetchone()[0]
                return result if result is not None else 0
        except sqlite3.Error:
            return 0

    def get_highest_count(self) -> int:
        """Retrieve the highest total count of any keystroke across all dates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.GET_HIGHEST_COUNT)
                result = cursor.fetchone()[0]
            return result or 0
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
                    SQLQueries.GET_KEYSTROKES_BY_DATE,
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
                cursor.execute(SQLQueries.CLEAR_KEYSTROKES)
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
                cursor.execute(SQLQueries.GET_DAILY_KEYSTROKE_COUNTS)
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
