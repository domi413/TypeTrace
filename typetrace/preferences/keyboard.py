"""Keyboard preferences for TypeTrace application."""

from __future__ import annotations

from typing import final, override

from gi.repository import Adw, Gtk

from typetrace.preferences.base import BasePreferencesGroup


@final
class KeyboardPreferencesGroup(BasePreferencesGroup):
    """Group for keyboard-related preferences."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        super().__init__(parent_dialog, title="Keyboard")
        self._initialize_rows()

    @override
    def _initialize_rows(self) -> None:
        """See base class."""
        self.add(self._create_keyboard_layout_selector())

    def _create_keyboard_layout_selector(self) -> Adw.ComboRow:
        """Create the keyboard layout selection combo row.

        Returns:
            The configured keyboard layout selector combo row

        """
        layout_row = Adw.ComboRow(
            title="Keyboard Layout",
            subtitle="Select your preferred keyboard layout",
        )
        layout_model = Gtk.StringList()
        # Add dummy entries as placeholders
        layout_model.append("QWERTY")
        layout_model.append("AZERTY")
        layout_row.set_model(layout_model)
        layout_row.set_selected(0)  # Default to QWERTY
        layout_row.connect("notify::selected", self._on_change)
        return layout_row

    def _on_change(self, combo_row: Adw.ComboRow, pspec: object) -> None:
        """Handle layout selection changes.

        Args:
            combo_row: The combo row that changed
            pspec: The parameter specification

        """
        selected_layout = combo_row.get_selected()
        layout_name = combo_row.get_model().get_string(selected_layout)
        print(f"Keyboard layout changed to: {layout_name}")
        # In a real implementation, this would update the application's keyboard layout
