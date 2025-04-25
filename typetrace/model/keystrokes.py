"""Model layer for accessing keystroke data from the TypeTrace database."""

from __future__ import annotations

import logging
import sqlite3

from gi.repository import GObject

from typetrace.config import DatabasePath
from typetrace.model.layouts import KEYBOARD_LAYOUTS
from typetrace.sql import SQLQueries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_scan_code(key: str, layout: str) -> int:
    """Get the scan code for a given key name and keyboard layout.

    Args:
    ----
        key: The name of the key (e.g., "KEY_A").
        layout: The keyboard layout (e.g., "en_US").

    Returns:
    -------
        The scan code for the key, or 0 if not found.

    """
    for row in KEYBOARD_LAYOUTS.get(layout, []):
        for scan_code, key_name in row:
            if key in (key_name, f"KEY_{key_name}"):
                return scan_code
    return 0


class Keystroke(GObject.Object):
    """Represents a single keystroke with its scan code, count, name, and date."""

    __gtype_name__ = "Keystroke"

    scan_code = GObject.Property(type=int, default=0)
    count = GObject.Property(type=int, default=0)
    key_name = GObject.Property(type=str, default="")
    date = GObject.Property(type=str, default="")

    def __init__(
        self, scan_code: int, count: int, key_name: str, date: str = "",
    ) -> None:
        """Initialize a Keystroke object.

        Args:
        ----
            scan_code: The scan code of the key.
            count: The number of times the key was pressed.
            key_name: The name of the key (e.g., "KEY_A").
            date: The date of the keystroke in ISO format (YYYY-MM-DD), optional.

        """
        super().__init__()
        self.scan_code = scan_code
        self.count = count
        self.key_name = key_name.replace("KEY_", "")
        self.date = date


class KeystrokeStore:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self) -> None:
        """Initialize the KeystrokeStore with the database path."""
        self.db_path = DatabasePath.DB_PATH

    def add(self, event: dict) -> bool:
        """Add a keystroke event to the database.

        Args:
        ----
            event: A dictionary containing the keystroke event data.
                  Expected keys include "key" (str or list of str) and optionally "scan_code".

        Returns:
        -------
            True if the keystroke was added successfully, False otherwise.

        """
        keys = event.get("key", [])
        if isinstance(keys, str):
            keys = [keys]

        for key in keys:
            # Ignore mouse clicks first
            if key in ["BTN_LEFT", "BTN_MOUSE", "BTN_RIGHT"]:
                logger.info("Ignoring mouse click: %s", key)
                continue
            # Get the scan_code from layouts.py
            scan_code = event.get("scan_code", get_scan_code(key, "en_US"))
            if scan_code == 0:
                logger.warning("No scan_code found for %s, skipping...", key)
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
                logger.info(
                    "Keystroke added successfully: %s (scan_code=%d)",
                    key,
                    scan_code,
                )
            except sqlite3.Error:
                logger.exception("Error adding keystroke")
                return False
        return True

    def get_all_keystrokes(self) -> list[Keystroke]:
        """Retrieve all keystrokes from the database.

        Returns
        -------
            A list of Keystroke objects representing all keystrokes.

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(SQLQueries.GET_ALL_KEYSTROKES)
                rows = cursor.fetchall()
            return [
                Keystroke(scan_code=r[0], count=r[1], key_name=r[2], date="")
                for r in rows
            ]
        except sqlite3.Error:
            logger.exception("Error retrieving keystrokes")
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
        except sqlite3.Error:
            return 0
        else:
            return result or 0

    def get_keystrokes_by_date(self, date: str) -> list[Keystroke]:
        """Retrieve keystrokes for a specific date.

        Args:
        ----
            date: Date in ISO format (YYYY-MM-DD)

        Returns:
        -------
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

        Returns
        -------
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
