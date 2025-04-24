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

# Hinweis: Wenn du den Fehler "no column named date" erhältst, überprüfe die Datenbank:
# 1. Öffne die Datenbank mit `sqlite3 /pfad/zu/deiner/datenbank.db`
# 2. Führe `.schema keystrokes` aus, um das aktuelle Schema zu sehen
# 3. Falls die Spalte `date` fehlt, führe `ALTER TABLE keystrokes ADD COLUMN date DATE;` aus
#    oder lösche die Tabelle mit `DROP TABLE keystrokes;` und erstelle sie neu mit CREATE_KEYSTROKES_TABLE