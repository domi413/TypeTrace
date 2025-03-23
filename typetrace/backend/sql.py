"""SQL queries for TypeTrace database operations."""

from typing import final


@final
class SQLQueries:
    """SQL queries for TypeTrace database operations."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    BEGIN_TRANSACTION = "BEGIN TRANSACTION"

    CREATE_KEYSTROKES_TABLE = """
    CREATE TABLE IF NOT EXISTS keystrokes (
        scan_code INTEGER PRIMARY KEY,
        count INTEGER DEFAULT 0,
        key_name TEXT
    )
    """

    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS keystrokes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keycode TEXT NOT NULL,
        timestamp REAL NOT NULL
    )
    """

    INSERT_OR_UPDATE_KEYSTROKE = """
    INSERT INTO keystrokes (scan_code, count, key_name)
    VALUES (:scan_code, 1, :key_name)
    ON CONFLICT(scan_code) DO UPDATE SET
        count = count + 1,
        key_name = :key_name
    """
