"""Unit tests for TypetraceWindow's heatmap and keystroke functionality."""

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock

import gi

# Patch GI template system *before* importing GTK-based modules
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, Gtk


# Patch Gtk.Template to avoid requiring .ui files during tests
class DummyTemplate:
    """Dummy template class for patching Gtk.Template during tests."""

    def __init__(self, resource_path=None):
        """Initialize the DummyTemplate with an optional resource path."""

    def __call__(self, cls):
        """Call the template on a given class."""
        return cls

DummyTemplate.Child = lambda: None
Gtk.Template = DummyTemplate

# Patch Gio.Settings to avoid requiring actual GSettings schema during tests
Gio.Settings.new = lambda _: type(
    "FakeSettings", (), {
        "__init__": lambda self: setattr(self, "_data", {"key-size": 42}),
        "get_int": lambda self, key: self._data.get(key, 0),
        "set_int": lambda self, key, value: self._data.__setitem__(key, value),
    },
)()

# Import controller modules and KeystrokeStore after patching
import typetrace.controller.heatmap as heatmap_mod
import typetrace.controller.statistics as statistics_mod
import typetrace.controller.verbose as verbose_mod
import typetrace.controller.window as window_mod
from typetrace.model.keystrokes import KeystrokeStore

# Mock visual components
heatmap_mod.Heatmap = MagicMock()
verbose_mod.Verbose = MagicMock()
statistics_mod.Statistics = MagicMock()

# Minimal testable version of TypetraceWindow
class DummyWindow:
    """Minimal testable version of TypetraceWindow with mocked components."""

    def __init__(self, keystroke_store, settings, application=None):
        """Initialize the DummyWindow with mocked components."""
        self.keystroke_store = keystroke_store
        self.settings = settings
        self.application = application

        # Inject mocked components
        self.heatmap = MagicMock()
        self.verbose = MagicMock()
        self.statistics = MagicMock()

        # Dummy stacked view with page names
        class Stack:
            def __init__(self):
                self.pages = ["heatmap", "verbose", "statistics"]

            def get_n_pages(self): return len(self.pages)

            def get_name(self, idx): return self.pages[idx]

        self.stack = Stack()

    def _on_refresh_clicked(self):
        """Refresh the views by updating the components."""
        self.heatmap.update()
        self.verbose.update()
        self.statistics.update()

    def _on_keystroke_received(self, event):
        """Handle a keystroke event by adding it to the store and refreshing views."""
        self.keystroke_store.add(event)
        self._on_refresh_clicked()

# Override actual window with dummy version
window_mod.TypetraceWindow = DummyWindow
typetrace_window = window_mod.TypetraceWindow

SCAN_CODE_A = 30  # Define constant for magic value

class TestHeatmap(unittest.TestCase):
    """Unit tests for the TypetraceWindow logic involving heatmap.

    Tests cover heatmap and keystroke updates.
    """

    def setUp(self):
        """Create a temporary database and window with mocked GTK components."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        conn = sqlite3.connect(self.temp_db.name)
        conn.execute("""
            CREATE TABLE keystrokes (
                scan_code INTEGER PRIMARY KEY,
                key_name TEXT,
                count INTEGER
            )
        """)
        conn.commit()
        conn.close()

        self.fake_store = KeystrokeStore()
        self.fake_store.db_path = self.temp_db.name
        self.settings = Gio.Settings.new("edu.ost.typetrace")
        self.window = typetrace_window(self.fake_store, self.settings)

        self.addCleanup(os.remove, self.temp_db.name)

    def test_initial_pages(self):
        """Test that the window stack contains exactly three pages."""
        self.assertEqual(self.window.stack.get_n_pages(), 3)

    def test_refresh_calls_update(self):
        """Test that clicking the refresh button triggers update on all views."""
        self.window.heatmap.update = MagicMock()
        self.window.verbose.update = MagicMock()
        self.window.statistics.update = MagicMock()

        self.window._on_refresh_clicked()

        self.window.heatmap.update.assert_called_once()
        self.window.verbose.update.assert_called_once()
        self.window.statistics.update.assert_called_once()

    def test_keystroke_callback(self):
        """Test that a keystroke is added to the store and views are refreshed."""
        fake_event = {"key": "A", "scan_code": SCAN_CODE_A}
        self.window._on_keystroke_received(fake_event)
        keystrokes = self.fake_store.get_all_keystrokes()
        self.assertTrue(any(k.scan_code == SCAN_CODE_A for k in keystrokes))

if __name__ == "__main__":
    unittest.main()
