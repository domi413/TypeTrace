"""Appearance preferences for TypeTrace application."""

from __future__ import annotations

from typing import final, override

from gi.repository import Adw, Gtk

from typetrace.preferences.base import BasePreferencesGroup


@final
class AppearancePreferencesGroup(BasePreferencesGroup):
    """Group for appearance-related preferences."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        super().__init__(parent_dialog, title="Appearance")
        self._initialize()

    @override
    def _initialize(self) -> None:
        """See base class."""
        self.add(self._create_theme_switcher())

    def _create_theme_switcher(self) -> Adw.ComboRow:
        """Create the theme selection combo row.

        Returns:
            The configured theme switcher combo row

        """
        theme_row = Adw.ComboRow(
            title="Theme", subtitle="Application color scheme preference"
        )
        theme_model = Gtk.StringList()
        theme_model.append("System")
        theme_model.append("Light")
        theme_model.append("Dark")
        theme_row.set_model(theme_model)
        theme_row.set_selected(0)  # Default to system
        theme_row.connect("notify::selected", self._on_change)
        return theme_row

    def _on_change(self, combo_row: Adw.ComboRow, pspec: object) -> None:
        """Handle theme selection changes.

        Args:
            combo_row: The combo row that changed
            pspec: The parameter specification

        """
        selected_theme = combo_row.get_selected()
        theme_name = combo_row.get_model().get_string(selected_theme)
        print(f"Theme changed to: {theme_name}")
        # In a real implementation, this would update the application's theme
