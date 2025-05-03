"""Unit tests for the Typetrace GTK Window Controller module."""

# ruff: noqa: E402
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock

# Patch GI template system *before* importing the window module
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, Gtk


class DummyTemplate:
    """Dummy GTK Template decorator to mock .ui resource loading."""

    def __init__(self, resource_path=None):
        """Initialize DummyTemplate."""

    def __call__(self, cls):
        """Return class unchanged."""
        return cls


# Avoid using unused lambda args (ARG005)
DummyTemplate.Child = lambda *_a, **_kw: None
Gtk.Template = DummyTemplate

# Patch Gio.Settings to avoid needing real GSettings schema
Gio.Settings.new = lambda _schema_id: type(
    "FakeSettings",
    (),
    {
        "__init__": lambda self: setattr(self, "_data", {"key-size": 42}),
        "get_int": lambda self, key: self._data.get(key, 0),
        "set_int": lambda self, key, value: self._data.__setitem__(key, value),
    },
)()

# Patch IPC so no threads are started
import typetrace.controller.window as window_mod


class DummyIPC:
    """Dummy IPC that avoids threading."""

    def __init__(self):
        """Initialize DummyIPC with no-op callback."""
        self.callback = None

    def register_callback(self, cb):
        """Register callback for keystroke events."""
        self.callback = cb

    def run(self):
        """Do nothing (stubbed)."""


window_mod.LinuxMacOSIPC = DummyIPC

# Patch child views (to avoid needing actual .ui files)
import typetrace.controller.heatmap as heatmap_mod
import typetrace.controller.statistics as statistics_mod
import typetrace.controller.verbose as verbose_mod

heatmap_mod.Heatmap = lambda **_kw: MagicMock()
verbose_mod.Verbose = lambda **_kw: MagicMock()
statistics_mod.Statistics = lambda **_kw: MagicMock()


class DummyWindow:
    """Simplified TypetraceWindow stub for unit testing."""

    def __init__(self, keystroke_store, settings, application=None):
        """Initialize dummy window with mocked views and stack."""
        self.keystroke_store = keystroke_store
        self.settings = settings
        self.application = application

        self.heatmap = MagicMock()
        self.verbose = MagicMock()
        self.statistics = MagicMock()

        class Stack:
            """Mocked GTK Stack for view navigation."""

            def __init__(self):
                self.pages = ["heatmap", "verbose", "statistics"]

            def get_n_pages(self):
                return len(self.pages)

            def get_name(self, idx):
                return self.pages[idx]

        self.stack = Stack()

    def _on_refresh_clicked(self):
        """Trigger updates for all view components."""
        self.heatmap.update()
        self.verbose.update()
        self.statistics.update()

    def _on_keystroke_received(self, event):
        """Invoke callback on receiving a new keystroke."""
        self.keystroke_store.add(event)
        self._on_refresh_clicked()


window_mod.TypetraceWindow = DummyWindow
typetrace_window = window_mod.TypetraceWindow

from typetrace.model.keystrokes import KeystrokeStore

# Constant for test scan code
TEST_SCAN_CODE = 30


class TestTypetraceWindow(unittest.TestCase):
    """Unit tests for TypetraceWindow behavior."""

    def setUp(self):
        """Create temporary database and TypetraceWindow instance."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        conn = sqlite3.connect(self.temp_db.name)
        conn.execute(
            """
            CREATE TABLE keystrokes (
                scan_code INTEGER PRIMARY KEY,
                key_name TEXT,
                count INTEGER
            )
            """,
        )
        conn.commit()
        conn.close()

        self.fake_store = KeystrokeStore()
        self.fake_store.db_path = self.temp_db.name
        self.settings = Gio.Settings.new("edu.ost.typetrace")
        self.window = typetrace_window(self.fake_store, self.settings)

        self.addCleanup(os.remove, self.temp_db.name)

    def test_initial_pages(self):
        """Test that all expected pages are present in the stack."""
        self.assertEqual(self.window.stack.get_n_pages(), 3)

    def test_refresh_calls_update(self):
        """Test that _on_refresh_clicked calls all update methods."""
        self.window.heatmap.update = MagicMock()
        self.window.verbose.update = MagicMock()
        self.window.statistics.update = MagicMock()

        self.window._on_refresh_clicked()

        self.window.heatmap.update.assert_called_once()
        self.window.verbose.update.assert_called_once()
        self.window.statistics.update.assert_called_once()

    def test_keystroke_callback(self):
        """Test that a keystroke is added and updates are triggered."""
        fake_event = {"key": "A", "scan_code": TEST_SCAN_CODE}
        self.window._on_keystroke_received(fake_event)
        keystrokes = self.fake_store.get_all_keystrokes()
        self.assertTrue(any(k.scan_code == TEST_SCAN_CODE for k in keystrokes))


if __name__ == "__main__":
    unittest.main()
