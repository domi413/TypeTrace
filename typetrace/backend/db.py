"""Database operations for TypeTrace."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import final

from .config import KeyEvent
from .sql import SQLQueries


@final
class DatabaseManager:
    """Database manager for handling TypeTrace database operations."""

    @staticmethod
    @contextmanager
    def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection to the SQLite database.

        Args:
            db_path (Path): Path to the SQLite database file.

        Yields:
            sqlite3.Connection: A connection to the database.

        """
        conn = sqlite3.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def initialize_database(db_path: Path) -> None:
        """Initialize the database by creating necessary tables.

        Args:
            db_path (Path): Path to the SQLite database file.

        """
        with DatabaseManager.get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(SQLQueries.CREATE_TABLE)
            conn.commit()

    @staticmethod
    def update_keystroke_counts(db_path: Path, events: list[KeyEvent]) -> None:
        """Update keystroke counts in the database.

        Args:
            db_path (Path): Path to the SQLite database file.
            events (list[KeyEvent]): List of key events to update in the database.

        """
        with DatabaseManager.get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(SQLQueries.INSERT_KEYSTROKE, events)
            conn.commit()

    @staticmethod
    def write_to_database(db_path: Path, events: list[KeyEvent]) -> None:
        """Write keystroke events to the database.

        Args:
            db_path (Path): Path to the SQLite database file.
            events (list[KeyEvent]): List of key events to write to the database.

        """
        DatabaseManager.update_keystroke_counts(db_path, events)
