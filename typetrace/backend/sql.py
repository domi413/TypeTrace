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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_code INTEGER NOT NULL,
        key_name TEXT NOT NULL,
        date DATE NOT NULL,
        count INTEGER DEFAULT 0,
        UNIQUE(scan_code, date)
    )
    """

    INSERT_OR_UPDATE_KEYSTROKE = """
    INSERT INTO keystrokes (scan_code, key_name, date, count)
    VALUES (:scan_code, :key_name, :date, 1)
    ON CONFLICT(scan_code, date) DO UPDATE SET
        count = count + 1,
        key_name = :key_name
    """

    GET_KEYSTROKES_BY_DATE = """
    SELECT key_name, count
    FROM keystrokes
    WHERE date = :date
    ORDER BY count DESC
    """
