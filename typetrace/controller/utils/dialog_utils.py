"""Utilities for creating and managing common GTK/Adwaita dialogs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gi.repository import Adw, Gio, Gtk


class DialogUtils:
    """Provides static helper methods for common dialog interactions."""

    @staticmethod
    def show_toast(window: Gtk.Window, message: str, timeout: int = 3) -> None:
        """Display an Adwaita toast notification anchored to a window.

        Args:
            window: The parent Gtk.Window to attach the toast to.
            message: The text message to display in the toast.
            timeout: Duration in seconds the toast remains visible (0 for indefinite).
                     Defaults to 3 seconds.

        """
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        window.add_toast(toast)

    @staticmethod
    def show_error_dialog(
        window: Gtk.Window,
        text: str,
        secondary_text: str | None = None,
    ) -> None:
        """Display a modal error dialog using Adw.AlertDialog.

        Args:
            window: The parent Gtk.Window for the dialog.
            text: The primary heading text for the error message.
            secondary_text: Optional detailed body text for the error.

        """
        dialog = Adw.AlertDialog(
            heading=text,
            body=secondary_text or "",
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        dialog.present(window)

    @staticmethod
    def open_file_save_dialog(
        parent: Gtk.Window,
        title: str,
        initial_name: str,
        callback: Callable[[Path], None],
    ) -> None:
        """Open a native 'Save As...' file chooser dialog using Gtk.FileChooserNative.

        Args:
            parent: The parent Gtk.Window for the dialog.
            title: The title displayed in the dialog window.
            initial_name: The suggested filename to save as.
            callback: A function to call with the chosen Path object if the user
                      confirms the save action. Called only on acceptance.

        """
        dialog = Gtk.FileChooserNative.new(
            title,
            parent,
            Gtk.FileChooserAction.SAVE,
            "_Save",
            "_Cancel",
        )
        dialog.set_current_name(initial_name)

        def on_response(d: Gtk.FileChooserNative, response_id: str) -> None:
            """Handle dialog response."""
            if response_id == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                if file:
                    callback(Path(file.get_path()))
            d.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    @staticmethod
    def open_file_open_dialog(
        parent: Gtk.Window,
        title: str,
        filters: Gio.ListStore[Gtk.FileFilter],
        callback: Callable[[Path], None],
    ) -> None:
        """Open a native 'Open File...' file chooser dialog using Gtk.FileChooserNative.

        Args:
            parent: The parent Gtk.Window for the dialog.
            title: The title displayed in the dialog window.
            filters: A Gio.ListStore containing Gtk.FileFilter objects to apply.
            callback: A function to call with the chosen Path object if the user
                      selects a file and confirms. Called only on acceptance.

        """
        dialog = Gtk.FileChooserNative.new(
            title,
            parent,
            Gtk.FileChooserAction.OPEN,
            "_Open",
            "_Cancel",
        )
        # Add filters from the ListStore
        for file_filter in filters:
            if isinstance(file_filter, Gtk.FileFilter):
                 dialog.add_filter(file_filter)

        def on_response(d: Gtk.FileChooserNative, response_id: str) -> None:
            """Handle dialog response."""
            if response_id == Gtk.ResponseType.ACCEPT:
                file = d.get_file()
                if file:
                    callback(Path(file.get_path()))
            d.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    @staticmethod
    def show_confirmation_dialog(
        parent: Gtk.Window,
        text: str,
        secondary_text: str,
        callback: Callable[[], None],
    ) -> None:
        """Show a modal confirmation dialog using Adw.AlertDialog with 'Yes'/'No'.

        The 'Yes' button has a destructive appearance.

        Args:
            parent: The parent Gtk.Window for the dialog.
            text: The primary heading text for the confirmation question.
            secondary_text: Additional body text explaining the action.
            callback: A function to call if the user clicks 'Yes'.
                      Not called if the user clicks 'No' or closes the dialog.

        """
        dialog = Adw.AlertDialog(
            heading=text,
            body=secondary_text,
        )
        dialog.add_response("no", "No")
        dialog.add_response("yes", "Yes")
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("no")
        dialog.set_close_response("no")

        def on_response(_dialog: Adw.AlertDialog, response_id: str) -> None:
            """Handle dialog response."""
            if response_id == "yes":
                callback()

        dialog.connect("response", on_response)
        dialog.present(parent)
