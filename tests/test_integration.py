"""Integration tests for the TypeTrace application."""

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
    """Create a temporary in-memory SQLite database for testing."""
    db_path = tmp_path / "test_typetrace.db"
    conn = sqlite3.connect(db_path)

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS keystrokes (
            scan_code INTEGER,
            key TEXT,
            date TEXT,
            count INTEGER,
            UNIQUE(scan_code, date)
        );
        """
    )
    conn.commit()
    return conn


@pytest.fixture
def settings() -> Gio.Settings:
    """Load GSettings schema for testing."""
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        "_install/share/glib-2.0/schemas",
        Gio.SettingsSchemaSource.get_default(),
        False,
    )
    schema = schema_source.lookup("edu.ost.typetrace", recursive=False)
    assert schema is not None, "GSettings schema 'edu.ost.typetrace' not found"
    return Gio.Settings.new_full(schema, None, None)


@pytest.fixture
def window(temp_db: sqlite3.Connection, settings: Gio.Settings) -> TypetraceWindow:
    """Create a TypetraceWindow instance with mocked dependencies."""
    db_manager = DatabaseManager()
    db_manager.db_connection = temp_db
    return TypetraceWindow(db_manager=db_manager, settings=settings)


def test_keystroke_storage(window: TypetraceWindow, temp_db: sqlite3.Connection):
    """Test that a keystroke is stored correctly and UI is initialized."""
    window.db_manager.insert_keystroke(30, "a", "2025-04-18")

    result = temp_db.execute(
        "SELECT * FROM keystrokes WHERE scan_code = 30"
    ).fetchone()

    temp_db.close()

    assert result is not None, "Keystroke should be stored in the database"
    assert result == (30, "a", "2025-04-18", 1), "Keystroke data should be correct"
    assert window.heatmap is not None, "Heatmap should be initialized"
    assert window.verbose is not None, "Verbose should be initialized"
