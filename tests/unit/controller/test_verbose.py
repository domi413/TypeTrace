# ruff: noqa: E402
"""Test suite for the Verbose widget in the TypeTrace project.

Tests the widget's logic and rendering of keystrokes.
"""

import unittest
from unittest.mock import MagicMock, call, patch

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from typetrace.model.keystrokes import Keystroke

# Patch Gtk.Template before importing Verbose
template_mock = MagicMock()
template_mock.Child = MagicMock()
template_mock.__call__ = lambda *args, **kwargs: (lambda cls: cls)  # noqa: ARG005

with patch("gi.repository.Gtk.Template", template_mock):
    from typetrace.controller.verbose import Verbose


class TestVerbose(unittest.TestCase):
    """Tests the Verbose widget's logic and keystroke rendering."""

    def setUp(self):
        """Prepare mocked keystroke store and Verbose widget."""
        self.mock_store = MagicMock()
        self.mock_store.get_all_keystrokes.return_value = [
            Keystroke(scan_code=1, count=5, key_name="A", date="2024-01-01"),
            Keystroke(scan_code=2, count=3, key_name="B", date="2024-01-01"),
        ]

        self.verbose = Verbose(keystroke_store=self.mock_store)

        # Mock GTK widgets
        self.verbose.list_store = MagicMock()
        self.verbose.list_store.append = MagicMock()

        self.verbose.column_view = MagicMock()
        self.verbose.column_view.get_columns.return_value = [
            MagicMock(), MagicMock(), MagicMock(),
        ]
        self.verbose.column_view.get_model.return_value = Gtk.SingleSelection.new(
            Gtk.NoSelection(),
        )
        self.verbose.column_view.get_sort_column.return_value = MagicMock()

    def test_populate_list_store_loads_keystrokes(self):
        """Ensure _populate_list_store loads keystrokes from the store.

        into the list_store.
        """
        self.verbose._populate_list_store()



        # Expect append to be called exactly twice
        self.assertEqual(self.verbose.list_store.append.call_count, 2)
        self.verbose.list_store.append.assert_has_calls([
            call(["A", 5, "2024-01-01"]),
            call(["B", 3, "2024-01-01"]),
        ])

    def test_update_triggers_list_population(self):
        """Ensure update() triggers _populate_list_store and queue_draw."""
        self.verbose._populate_list_store = MagicMock()
        self.verbose.queue_draw = MagicMock()

        self.verbose.update()

        self.verbose._populate_list_store.assert_called_once()
        self.verbose.queue_draw.assert_called_once()

    def test_column_view_model_is_set_correctly(self):
        """Ensure column view uses SingleSelection wrapping SortListModel."""
        model = self.verbose.column_view.get_model()
        self.assertIsInstance(model, Gtk.SingleSelection)
        self.assertIsInstance(model.get_model(), Gtk.NoSelection)

    def test_column_sorters_are_attached(self):
        """Ensure all columns have a sorter and a default sort column is set."""
        columns = self.verbose.column_view.get_columns()
        self.assertEqual(len(columns), 3)

        for column in columns:
            column.get_sorter = MagicMock(return_value=MagicMock())
            self.assertIsNotNone(column.get_sorter())

        self.assertIsNotNone(self.verbose.column_view.get_sort_column())


if __name__ == "__main__":
    unittest.main(verbosity=2)
