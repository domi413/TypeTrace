"""Database operations for TypeTrace."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from backend.config import DEBUG, KeyEvent
from backend.sql import (
    BEGIN_TRANSACTION,
    CREATE_KEYSTROKES_TABLE,
    INSERT_OR_UPDATE_KEYSTROKE,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Create and manage a database connection.

    Args:
        db_path: Path to the SQLite database file.

    Yields:
        SQLite database connection.

    """
    conn: sqlite3.Connection = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def initialize_database(db_path: Path) -> None:
    """Initialize the SQLite database with required schema.

    Args:
        db_path: Path to the SQLite database file.

    Raises:
        sqlite3.Error: If database initialization fails.

    """
    with get_db_connection(db_path) as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(CREATE_KEYSTROKES_TABLE)
        conn.commit()

        if DEBUG:
            logging.debug("Database initialized at %s", db_path)


def update_keystroke_counts(
    db_path: Path,
    events: list[KeyEvent],
) -> None:
    """Update keystroke counts with new events in the database.

    Args:
        db_path: Path to the SQLite database file.
        events: List of key events to process.

    Raises:
        sqlite3.Error: If database update fails.

    """
    if not events:
        return

    with get_db_connection(db_path) as conn:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(BEGIN_TRANSACTION)

        for event in events:
            scan_code: int = event["scan_code"]
            key_name: str | tuple[str, ...] = event["name"]

            if isinstance(key_name, tuple):
                key_name = ", ".join(key_name)

            cursor.execute(
                INSERT_OR_UPDATE_KEYSTROKE,
                (scan_code, key_name, key_name),
            )

        conn.commit()

        if DEBUG:
            logging.debug("Updated database with %d keystroke events", len(events))


def write_to_database(db_path: Path, events: list[KeyEvent]) -> None:
    """Write keystroke events to the database.

    Args:
        events: List of dictionaries containing key details.

    """
    update_keystroke_counts(db_path, events)
