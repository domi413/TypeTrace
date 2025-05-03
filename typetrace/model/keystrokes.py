"""Model layer for accessing keystroke data from the TypeTrace database."""

from __future__ import annotations

import logging
import sqlite3

from gi.repository import GObject

from typetrace.config import DatabasePath
from typetrace.model.layouts import get_scan_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Keystroke(GObject.Object):
    """Represents a single keystroke with its scan code, count, name, and date."""

    __gtype_name__ = "Keystroke"

    scan_code = GObject.Property(type=int, default=0)
    count     = GObject.Property(type=int, default=0)
    key_name  = GObject.Property(type=str, default="")
    date      = GObject.Property(type=str, default="")

    def __init__(
        self: Keystroke,
        scan_code: int,
        count: int,
        key_name: str,
        date: str = "",
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
        self.count     = count
        self.key_name  = key_name.replace("KEY_", "")
        self.date      = date

class KeystrokeStore:
    """Model for interacting with the keystrokes table in the database."""

    def __init__(self: KeystrokeStore) -> None:
        """Initialize the KeystrokeStore with the database path."""
        self.db_path = DatabasePath.DB_PATH

    def add(self: KeystrokeStore, event: dict) -> bool:
        """Add a keystroke event to the database.

        Args:
        ----
            event: A dictionary containing the keystroke event data.
                   Expected keys include:
                   - "key": str or list of str
                   - "scan_code": optional

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

    def get_all_keystrokes(self: KeystrokeStore) -> list[Keystroke]:
        """Retrieve all keystrokes from the database.

        Returns
        -------
            A list of Keystroke objects representing all keystrokes.

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT scan_code, count, key_name
                      FROM keystrokes
                     ORDER BY count DESC
                    """,
                )
                rows = cursor.fetchall()
            return [
                Keystroke(scan_code=r[0], count=r[1], key_name=r[2], date="")
                for r in rows
            ]
        except sqlite3.Error:
            logger.exception("Error retrieving keystrokes")
            return []

    def get_highest_count(self: KeystrokeStore) -> int:
        """Retrieve the highest total count of any keystroke.

        Returns
        -------
            The highest count, or 0 if there are no keystrokes or an error occurs.

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT MAX(count) FROM keystrokes
                    """,
                )
                result = cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
        else:
            return result or 0

    def clear(self: KeystrokeStore) -> bool:
        """Remove all entries from the keystrokes table.

        Returns
        -------
            True if the table was cleared successfully, False otherwise.

        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM keystrokes")
                conn.commit()
        except sqlite3.Error:
            return False
        else:
            return True
