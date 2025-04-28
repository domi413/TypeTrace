"""SQL queries for TypeTrace database operations."""

from typing import final


@final
class SQLQueries:
    """SQL queries for TypeTrace database operations."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    # Database setup
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

    # Backend operations
    INSERT_OR_UPDATE_KEYSTROKE = """
    INSERT INTO keystrokes (scan_code, key_name, date, count)
    VALUES (:scan_code, :key_name, :date, 1)
    ON CONFLICT(scan_code, date) DO UPDATE SET
        count = count + 1,
        key_name = :key_name
    """

    # Frontend operations
    GET_ALL_KEYSTROKES = """
    SELECT scan_code, SUM(count) as total_count, key_name,
    MAX(date) as latest_date
    FROM keystrokes
    GROUP BY scan_code, key_name
    ORDER BY total_count DESC
    """

    GET_TOP_KEYSTROKES_ALL_TIME = """
    SELECT scan_code, SUM(count) as total_count, key_name,
    MAX(date) as latest_date
    FROM keystrokes
    GROUP BY scan_code, key_name
    ORDER BY total_count DESC
    LIMIT ?
    """

    GET_TOP_KEYSTROKES_BY_DATE = """
    SELECT scan_code, count, key_name, date
    FROM keystrokes
    WHERE date = ?
    ORDER BY count DESC
    LIMIT ?
    """

    GET_TOTAL_PRESSES = "SELECT SUM(count) FROM keystrokes"

    GET_TOTAL_KEYSTROKE_COUNT_BY_DATE = """
    SELECT SUM(count) FROM keystrokes
    WHERE date = ?
    """

    GET_HIGHEST_COUNT = """
    SELECT MAX(total_count) FROM (
        SELECT SUM(count) as total_count
        FROM keystrokes
        GROUP BY scan_code, key_name
    )
    """

    GET_KEYSTROKES_BY_DATE = """
    SELECT scan_code, count, key_name, date FROM keystrokes
    WHERE date = ?
    """

    GET_DAILY_KEYSTROKE_COUNTS = """
    SELECT date, SUM(count) as total_count
    FROM keystrokes
    WHERE date >= date('now', '-6 days')
    GROUP BY date
    ORDER BY date
    """

    CLEAR_KEYSTROKES = "DELETE FROM keystrokes"
