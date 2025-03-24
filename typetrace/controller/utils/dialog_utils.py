"""Utilities for dialogs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gi.repository import Adw, Gio, Gtk


def show_toast(window: Gtk.Window, message: str, timeout: int = 3) -> None:
    """Display a toast notification."""
    toast = Adw.Toast.new(message)
    toast.set_timeout(timeout)
    window.add_toast(toast)


def show_error_dialog(
    window: Gtk.Window,
    text: str,
    secondary_text: str | None = None,
) -> None:
    """Display an error dialog using Adw.AlertDialog."""
    dialog = Adw.AlertDialog(
        heading=text,
        body=secondary_text or "",
    )
    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    dialog.present(window)


def open_file_save_dialog(
    parent: Gtk.Window,
    title: str,
    initial_name: str,
    callback: Callable[[Path], None],
) -> None:
    """Open a save file dialog."""
    dialog = Gtk.FileChooserNative.new(
        title,
        parent,
        Gtk.FileChooserAction.SAVE,
        "_Save",
        "_Cancel",
    )
    dialog.set_current_name(initial_name)

    def on_response(d: Gtk.FileChooserNative, response_id: str) -> None:
        if response_id == Gtk.ResponseType.ACCEPT:
            file = d.get_file()
            callback(Path(file.get_path()))
        d.destroy()

    dialog.connect("response", on_response)
    dialog.show()


def open_file_open_dialog(
    parent: Gtk.Window,
    title: str,
    filters: Gio.ListStore,
    callback: Callable[[Path], None],
) -> None:
    """Open a file chooser dialog."""
    dialog = Gtk.FileChooserNative.new(
        title,
        parent,
        Gtk.FileChooserAction.OPEN,
        "_Open",
        "_Cancel",
    )
    for file_filter in filters:
        dialog.add_filter(file_filter)

    def on_response(d: Gtk.FileChooserNative, response_id: str) -> None:
        if response_id == Gtk.ResponseType.ACCEPT:
            file = d.get_file()
            callback(Path(file.get_path()))
        d.destroy()

    dialog.connect("response", on_response)
    dialog.show()


def show_confirmation_dialog(
    parent: Gtk.Window,
    text: str,
    secondary_text: str,
    callback: Callable[[], None],
) -> None:
    """Show a confirmation dialog using Adw.AlertDialog."""
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
        if response_id == "yes":
            callback()

    dialog.connect("response", on_response)
    dialog.present(parent)
