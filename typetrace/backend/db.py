"""Database operations for TypeTrace."""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import final

from typetrace.backend.sql import SQLQueries
from typetrace.config import Event

logger = logging.getLogger(__name__)


@final
class DatabaseManager:
    """Database manager for handling TypeTrace database operations."""

    @final
    def initialize_database(self, db_path: Path) -> None:
        """Initialize the database by creating necessary tables.

        Args:
            db_path: Path to the SQLite database file.

        """
        with self._get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(SQLQueries.CREATE_KEYSTROKES_TABLE)
            conn.commit()

            logger.debug("Database initialized at %s", db_path)

    @final
    def write_to_database(self, db_path: Path, events: list[Event]) -> None:
        """Write keystroke events to the database.

        Args:
            db_path: Path to the SQLite database file.
            events: List of key events to write to the database.

        """
        if not events:
            return

        processed_events = [
            {
                "scan_code": event["scan_code"],
                "key_name": ", ".join(event["name"])
                if isinstance(event["name"], tuple)
                else event["name"],
            }
            for event in events
        ]

        with self._get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(SQLQueries.INSERT_OR_UPDATE_KEYSTROKE, processed_events)
            conn.commit()

            logger.debug("Updated database with %d keystroke events", len(events))

    @final
    @contextmanager
    def _get_db_connection(
        self,
        db_path: Path,
    ) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection to the SQLite database.

        Args:
            db_path: Path to the SQLite database file.

        Yields:
            SQLite database connection.

        """
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(db_path)
            yield conn
        except sqlite3.OperationalError:
            logger.exception("SQLite operational error")
            raise
        except sqlite3.Error:
            logger.exception("Database error")
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except sqlite3.Error:
                    logger.warning("Error closing database connection")
