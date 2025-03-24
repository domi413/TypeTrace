"""Main preferences dialog for TypeTrace application."""

from __future__ import annotations

from gi.repository import Adw, Gtk

from typetrace.preferences.appearance import AppearancePreferencesGroup
from typetrace.preferences.database.database import DatabasePreferencesGroup
from typetrace.preferences.keyboard import KeyboardPreferencesGroup


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences window for the TypeTrace application."""

    def __init__(self, parent: Gtk.Window) -> None:
        """Initialize the preferences window.

        Args:
            parent: The parent window for this dialog

        """
        super().__init__(
            title="Preferences",
            transient_for=parent,
            destroy_with_parent=True,
            modal=True,
        )
        self._create_interface()

    def _create_interface(self) -> None:
        """Build the preferences interface with available settings."""
        general_page = Adw.PreferencesPage(
            title="General",
            icon_name="preferences-system-symbolic",
        )
        self.add(general_page)

        # Add sections to the page
        general_page.add(AppearancePreferencesGroup(self))
        general_page.add(DatabasePreferencesGroup(self))
        general_page.add(KeyboardPreferencesGroup(self))
