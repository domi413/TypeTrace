import sqlite3
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio
import pytest

from typetrace.controller.window import TypetraceWindow
from typetrace.model.database_manager import DatabaseManager


@pytest.fixture
def temp_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "test_typetrace.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS keystrokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_code INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            date DATE NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(scan_code, date),
        )
        """
    )
    conn.commit()
    return conn


@pytest.fixture
def settings() -> Gio.Settings:
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        "_install/share/glib-2.0/schemas",
        parent=None,
        trusted=False,
    )
    schema = schema_source.lookup("edu.ost.typetrace", recursive=False)
    assert schema is not None, "GSettings schema 'edu.ost.typetrace' not found"
    return Gio.Settings.new_full(schema, None, None)


@pytest.fixture
def window(temp_db: sqlite3.Connection, settings: Gio.Settings) -> TypetraceWindow:
    db_manager = DatabaseManager()
    db_manager.db_connection = temp_db
    win = TypetraceWindow(settings=settings, db_manager=db_manager)
    yield win
    win.close()


def test_backend_frontend_integration(
    window: TypetraceWindow,
    temp_db: sqlite3.Connection,
) -> None:
    """Test backend (KeystrokeStore) and frontend (TypetraceWindow) integration."""
    keystroke = {
        "scan_code": 30,
        "key_name": "a",
        "date": "2025-04-18",
    }
    window.keystroke_store.store_keystroke(keystroke)

    cursor = temp_db.cursor()
    cursor.execute(
        "SELECT scan_code, key_name, date, count FROM keystrokes WHERE scan_code = ?",
        (keystroke["scan_code"],),
    )
    result = cursor.fetchone()
    temp_db.close()

    assert result is not None, "Keystroke should be stored in the database"
    assert result == (30, "a", "2025-04-18", 1), "Keystroke data should be correct"
    assert window.heatmap is not None, "Heatmap should be initialized"
    assert window.verbose is not None, "Verbose should be initialized"
