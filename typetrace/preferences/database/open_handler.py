"""Database open folder handler implementation."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import final, override

from gi.repository import Adw, Gtk

from typetrace.preferences.database.base import DatabaseHandler


@final
class DatabaseOpenHandler(DatabaseHandler):
    """Handler for opening database folder."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        self.parent_dialog = parent_dialog

    @override
    def create_row(self) -> Adw.ActionRow:
        """See base class."""
        open_folder_row = Adw.ActionRow(
            title="Open Database Location",
            subtitle="Open the folder containing the database file",
        )
        folder_button = Gtk.Button(
            icon_name="folder-symbolic",
            valign=Gtk.Align.CENTER,
        )
        folder_button.connect("clicked", self._on_open_folder_clicked)
        open_folder_row.add_suffix(folder_button)
        return open_folder_row

    def _on_open_folder_clicked(self, button: Gtk.Button) -> None:
        """Handle click on the open folder button.

        Args:
            button: The button that was clicked

        """
        try:
            from typetrace.model.keystrokes import KeystrokeStore

            # Get database path
            db_path = KeystrokeStore().db_path
            db_folder = os.path.dirname(db_path)

            # Open folder based on platform
            system = platform.system()

            if system == "Windows":
                os.startfile(db_folder)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", db_folder])
            else:  # Linux and other Unix-like
                subprocess.run(["xdg-open", db_folder])

        except Exception as e:
            # Handle any errors
            error_dialog = Adw.MessageDialog(
                transient_for=self.parent_dialog,
                heading="Error",
                body=f"Failed to open database location: {str(e)}",
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
