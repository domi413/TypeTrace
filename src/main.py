"""Typetrace application entry point module."""

from __future__ import annotations

import sys
from typing import Any, Callable

import gi
from gi.repository import Adw, Gio

from .controller.window import TypetraceWindow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class TypetraceApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self) -> None:
        """Initialize the application with default settings."""
        super().__init__(
            application_id="edu.ost.typetrace",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

    def do_activate(self) -> None:
        """Activate the application.

        Raises the application's main window, creating it if necessary.
        """
        win = self.props.active_window
        if not win:
            win = TypetraceWindow(application=self)
        win.present()

    def on_about_action(self, *_: Any) -> None:
        """Display the about dialog with application information."""
        about = Adw.AboutDialog(
            application_name="typetrace",
            application_icon="edu.ost.typetrace",
            developer_name="Unknown",
            version="0.1.0",
            developers=["Unknown"],
            copyright="© 2025 Unknown",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, _widget: Any, _: Any) -> None:
        """Show the application preferences dialog."""
        print("app.preferences action activated")

    def create_action(
        self,
        name: str,
        callback: Callable[..., Any],
        shortcuts: list[str] | None = None,
    ) -> None:
        """Add an application action with optional keyboard shortcuts.

        Args:
            name: The name of the action to create
            callback: The function to call when the action is activated
            shortcuts: List of keyboard accelerators for the action

        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main() -> int:
    """Run the application.

    Creates and starts the main application instance.

    Returns:
        The application exit code

    """
    app = TypetraceApplication()
    return app.run(sys.argv)
