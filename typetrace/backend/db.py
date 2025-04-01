"""Database operations for TypeTrace."""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import final

from backend.sql import SQLQueries

from typetrace.config import Event

logger = logging.getLogger(__name__)


@final
class DatabaseManager:
    """Database manager for handling TypeTrace database operations."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    @staticmethod
    def initialize_database(db_path: Path) -> None:
        """Initialize the database by creating necessary tables.

        Args:
            db_path: Path to the SQLite database file.

        """
        with DatabaseManager._get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(SQLQueries.CREATE_KEYSTROKE_TABLE)
            cursor.execute(SQLQueries.CREATE_KEYSTROKE_LOGS_TABLE)
            cursor.execute(SQLQueries.CREATE_KEYSTROKE_SCAN_CODE_INDEX)
            cursor.execute(SQLQueries.CREATE_KEYSTROKE_LOGS_COMPOSITE_INDEX)
            conn.commit()

            logger.debug("Database initialized at %s", db_path)

    @staticmethod
    def write_to_database(db_path: Path, events: list[Event]) -> None:
        """Write keystroke events to the database.

        Args:
            db_path: Path to the SQLite database file.
            events: List of key events to write to the database.

        """
        if not events:
            return

        with DatabaseManager._get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(SQLQueries.BEGIN_TRANSACTION)

            for event in events:
                key_name = (
                    ", ".join(event["name"])
                    if isinstance(event["name"], tuple)
                    else event["name"]
                )

                cursor.execute(
                    SQLQueries.INSERT_KEYSTROKE,
                    {
                        "scan_code": event["scan_code"],
                        "key_name": key_name,
                    },
                )

                cursor.execute(
                    SQLQueries.GET_KEYSTROKE_ID,
                    {"scan_code": event["scan_code"]},
                )

                keystroke_id = cursor.fetchone()[0]

                cursor.execute(
                    SQLQueries.INSERT_OR_UPDATE_KEYSTROKE_LOG,
                    {
                        "keystroke_id": keystroke_id,
                    },
                )

            conn.commit()

            logger.debug("Updated database with %d keystroke events", len(events))

    @staticmethod
    @contextmanager
    def _get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection to the SQLite database.

        Args:
            db_path: Path to the SQLite database file.

        Yields:
            SQLite database connection.

        """
        conn = sqlite3.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()
