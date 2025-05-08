"""Model layer for accessing keystrokes data from the TypeTrace database."""

from __future__ import annotations

import logging
import sqlite3
from typing import ClassVar

from config import DatabasePath
from gi.repository import GObject
from sql import SQLQueries

logger = logging.getLogger(__name__)


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


class KeystrokeStore(GObject.Object):
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize the model with the database path."""
        super().__init__()
        self.db_path = DatabasePath.DB_PATH
        self.conn = conn

    __gsignals__: ClassVar[dict] = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def get_all_keystrokes(self) -> list[Keystroke]:
        """Retrieve all keystrokes with their counts and names.

        Returns aggregated data across all dates.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQLQueries.GET_ALL_KEYSTROKES)
            rows = cursor.fetchall()
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
            logger.exception("Failed to retrieve all keystrokes")
            return []

    def get_total_presses(self) -> int:
        """Get the total number of key presses across all keystrokes and all dates."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQLQueries.GET_TOTAL_PRESSES)
            result = cursor.fetchone()[0]
        except sqlite3.Error:
            logger.exception("Failed to retrieve total key presses")
            return 0
        else:
            return result or 0

    def get_highest_count(self) -> int:
        """Retrieve the highest total count of any keystroke across all dates."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQLQueries.GET_HIGHEST_COUNT)
            result = cursor.fetchone()[0]
        except sqlite3.Error:
            logger.exception("Failed to retrieve highest keystroke count")
            return 0
        else:
            return result or 0

    def get_keystrokes_by_date(self, date: str) -> list[Keystroke]:
        """Retrieve keystrokes for a specific date.

        Args:
            date: Date in ISO format (YYYY-MM-DD)

        Returns:
            List of Keystroke objects for the specified date

        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQLQueries.GET_KEYSTROKES_BY_DATE, (date,))
            rows = cursor.fetchall()
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
            logger.exception("Failed to retrieve keystrokes for date: %s", date)
            return []

    def get_top_keystrokes(
        self,
        limit: int,
        date: str | None = None,
    ) -> list[Keystroke]:
        """Retrieve the top N keystrokes, optionally filtered by date.

        Args:
            limit: The maximum number of keystrokes to return
            date: Optional date in ISO format (YYYY-MM-DD) to filter by

        Returns:
            List of top Keystroke objects

        """
        try:
            cursor = self.conn.cursor()
            if date:
                cursor.execute(
                    SQLQueries.GET_TOP_KEYSTROKES_BY_DATE,
                    (date, limit),
                )
            else:
                cursor.execute(SQLQueries.GET_TOP_KEYSTROKES_ALL_TIME, (limit,))
            rows = cursor.fetchall()
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
            logger.exception(
                "Failed to retrieve top keystrokes for limit: %d, date: %s",
                limit,
                date or "all time",
            )
            return []

    def get_total_keystroke_count(self, date: str | None = None) -> int:
        """Get the total count of keystrokes, optionally filtered by date.

        Args:
            date: Optional date in ISO format (YYYY-MM-DD) to filter by

        Returns:
            Total keystroke count

        """
        try:
            cursor = self.conn.cursor()
            if date:
                cursor.execute(SQLQueries.GET_TOTAL_KEYSTROKE_COUNT_BY_DATE, (date,))
            else:
                cursor.execute(SQLQueries.GET_TOTAL_PRESSES)
            result = cursor.fetchone()[0]
        except sqlite3.Error:
            logger.exception(
                "Failed to retrieve total keystroke count for date: %s",
                date or "all time",
            )
            return 0
        else:
            return result or 0

    def clear(self) -> bool:
        """Remove all entries."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(SQLQueries.CLEAR_KEYSTROKES)
            self.conn.commit()
            self.emit("changed")
        except sqlite3.Error:
            logger.exception("Failed to clear keystrokes")
            return False
        else:
            return True

    def get_daily_keystroke_counts(self) -> list[dict]:
        """Get daily keystroke counts for the past 7 days.

        Returns:
            List of dictionaries with date and count for each day

        """
        try:
            cursor = self.conn.cursor()
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
            logger.exception("Failed to retrieve daily keystroke counts")
            return []
