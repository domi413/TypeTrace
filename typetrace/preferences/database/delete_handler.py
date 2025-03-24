"""Database deletion handler implementation."""

from __future__ import annotations

import os
from typing import final, override

from gi.repository import Adw, Gtk

from typetrace.preferences.database.base import DatabaseHandler


@final
class DatabaseDeleteHandler(DatabaseHandler):
    """Handler for database deletion operations."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        self.parent_dialog = parent_dialog

    @override
    def create_row(self) -> Adw.ActionRow:
        """See base class."""
        delete_row = Adw.ActionRow(
            title="Delete Database",
            subtitle="Permanently delete all typing statistics",
        )
        delete_button = Gtk.Button(
            icon_name="user-trash-symbolic",
            valign=Gtk.Align.CENTER,
            css_classes=["destructive-action"],
        )
        delete_button.connect("clicked", self._on_delete_clicked)
        delete_row.add_suffix(delete_button)
        return delete_row

    def _on_delete_clicked(self, button: Gtk.Button) -> None:
        """Handle click on the delete database button.

        Args:
            button: The button that was clicked

        """
        # Create confirmation dialog
        dialog = Adw.MessageDialog(
            transient_for=self.parent_dialog,
            heading="Delete Database",
            body="This will permanently delete all your typing statistics.\n\nThis action cannot be undone.",
            default_response="cancel",
            close_response="cancel",
        )

        # Add action buttons
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        # Connect to response signal
        dialog.connect("response", self._on_delete_confirmation_response)

        # Show dialog
        dialog.present()

    def _on_delete_confirmation_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        """Handle the response from the delete confirmation dialog.

        Args:
            dialog: The message dialog
            response: The response ID from the dialog

        """
        if response == "delete":
            try:
                from typetrace.model.keystrokes import KeystrokeStore

                # Get database path and delete the file
                db_path = KeystrokeStore().db_path
                if os.path.exists(db_path):
                    os.remove(db_path)

                    # Show success message
                    success_dialog = Adw.MessageDialog(
                        transient_for=self.parent_dialog,
                        heading="Database Deleted",
                        body="The database has been successfully deleted.",
                    )
                    success_dialog.add_response("ok", "OK")
                    success_dialog.present()
                else:
                    # Database doesn't exist
                    error_dialog = Adw.MessageDialog(
                        transient_for=self.parent_dialog,
                        heading="Error",
                        body="Database file not found.",
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
            except Exception as e:
                # Handle any errors
                error_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Error",
                    body=f"Failed to delete database: {str(e)}",
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
