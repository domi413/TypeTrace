"""Integration tests for the TypeTrace application."""

import sqlite3
from pathlib import Path

import gi
import pytest
from gi.repository import Gio

from typetrace.controller.window import TypetraceWindow
from typetrace.model.database_manager import DatabaseManager

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


@pytest.fixture()
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
        """,
    )
    conn.commit()
    return conn


@pytest.fixture()
def settings() -> Gio.Settings:
    """Load GSettings schema for testing."""
    schema_source = Gio.SettingsSchemaSource.new_from_directory(
        "_install/share/glib-2.0/schemas",
        Gio.SettingsSchemaSource.get_default(),
        False,
    )
    schema = schema_source.lookup("edu.ost.typetrace", recursive=False)
    if schema is None:
        pytest.fail("GSettings schema 'edu.ost.typetrace' not found")

    return Gio.Settings.new_full(
        schema=schema, path=None, value=None,
    )


@pytest.fixture()
def window(temp_db: sqlite3.Connection, settings: Gio.Settings) -> TypetraceWindow:
    """Create a TypetraceWindow instance with mocked dependencies."""
    db_manager = DatabaseManager()
    db_manager.db_connection = temp_db
    return TypetraceWindow(db_manager=db_manager, settings=settings)


def test_keystroke_storage(
    window: TypetraceWindow, temp_db: sqlite3.Connection
) -> None:
    """Test that a keystroke is stored correctly and UI is initialized."""
    window.db_manager.insert_keystroke(30, "a", "2025-04-18")

    result = temp_db.execute(
        "SELECT * FROM keystrokes WHERE scan_code = 30",
    ).fetchone()

    temp_db.close()

    if result is None:
        pytest.fail("Keystroke should be stored in the database")
    if result != (30, "a", "2025-04-18", 1):
        pytest.fail("Keystroke data should be correct")

    if window.heatmap is None:
        pytest.fail("Heatmap should be initialized")

    if window.verbose is None:
        pytest.fail("Verbose should be initialized")


def test_keystroke_storage_ui(window: TypetraceWindow) -> None:
    """Test that the keystroke data is properly displayed in the UI."""
    window.db_manager.insert_keystroke(30, "a", "2025-04-18")

    if window.db_manager.get_keystrokes() != [(30, "a", "2025-04-18", 1)]:
        pytest.fail("Keystroke data not found in UI")
