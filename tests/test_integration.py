#Incomplete Testing
import pytest
import sqlite3
import tempfile
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import GLib, Gtk, Adw, Gio
from typetrace.controller.window import TypetraceWindow
from typetrace.model.keystrokes import KeystrokeStore
from typetrace.model.database_manager import DatabaseManager

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database with a keystrokes table."""
    db_path = tmp_path / "test_typetrace.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keystrokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_code INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            date DATE NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(scan_code, date)
        )
    """)
    conn.commit()
    conn.close()
    return db_path

@pytest.fixture
def settings():
    """Create GSettings for the tests."""
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        "_install/share/glib-2.0/schemas", None, False
    )
    schema = schema_source.lookup("edu.ost.typetrace", False)
    assert schema is not None, "GSettings schema 'edu.ost.typetrace' not found"
    return Gio.Settings.new_full(schema, None, None)

@pytest.fixture
def window(temp_db, settings):
    """Create a TypetraceWindow with a real database."""
    db_manager = DatabaseManager()
    db_manager.db_path = temp_db
    keystroke_store = KeystrokeStore(db_path=temp_db)
    window = TypetraceWindow(keystroke_store, settings)
    yield window
    window.close()

def test_backend_frontend_integration(window, temp_db):
    """Test the integration between backend (KeystrokeStore) and frontend (TypetraceWindow)."""
    # Simulate a keystroke and store it in the database
    keystroke = {
        "scan_code": 30,
        "key_name": "a",
        "date": "2025-04-18"
    }
    window.keystroke_store.store_keystroke(keystroke)

    # Check if the keystroke is stored in the database
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT scan_code, key_name, date, count FROM keystrokes WHERE scan_code = ?",
        (keystroke["scan_code"],)
    )
    result = cursor.fetchone()
    conn.close()
    assert result is not None, "Keystroke should be stored in the database"
    assert result == (30, "a", "2025-04-18", 1), "Keystroke data should be correct"

    # Check if widgets in the frontend are initialized
    assert window.heatmap is not None, "Heatmap should be initialized"
    assert window.verbose is not None, "Verbose should be initialized"
