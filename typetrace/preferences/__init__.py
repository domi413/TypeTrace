"""Preferences module for TypeTrace application."""

from __future__ import annotations

from gi.repository import Gtk

from typetrace.preferences.dialog import PreferencesDialog


def show_preferences_dialog(parent: Gtk.Window) -> None:
    """Show the preferences dialog.

    Args:
        parent: The parent window for the preferences dialog

    """
    dialog = PreferencesDialog(parent)
    dialog.present()
