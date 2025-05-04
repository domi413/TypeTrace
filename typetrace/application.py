"""Typetrace frontend application."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Callable

from gi.repository import Adw, Gio

from typetrace.config import DatabasePath
from typetrace.controller.preferences import Preferences
from typetrace.controller.window import TypetraceWindow
from typetrace.logging_setup import LoggerSetup
from typetrace.model.database_manager import DatabaseManager
from typetrace.model.keystrokes import KeystrokeStore

logger = logging.getLogger(__name__)


class Application(Adw.Application):
    """The main application singleton class."""

    def __init__(self, application_id: str, version: str) -> None:
        """Initialize the application with default settings."""
        LoggerSetup.setup_logging()
        logger.debug(
            "Initializing application with ID: %s, version: %s",
            application_id,
            version,
        )
        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.version = version
        try:
            self.settings = Gio.Settings.new("edu.ost.typetrace")
            logger.debug("GSettings initialized for schema: edu.ost.typetrace")
        except Exception:
            logger.exception("Failed to initialize GSettings")
            raise

        try:
            self.db_conn = sqlite3.connect(DatabasePath.DB_PATH)
            logger.debug("Database connection established to: %s", DatabasePath.DB_PATH)
            self.keystroke_store = KeystrokeStore(self.db_conn)
            self.db_manager = DatabaseManager()
        except Exception:
            logger.exception("Failed to initialize database components")
            raise

        self._setup_actions()
        logger.debug("Application actions set up")

    def do_activate(self) -> None:
        """Activate the application.

        Raises the application's main window, creating it if necessary.
        """
        logger.debug("Activating application")
        win = self.props.active_window
        if not win:
            try:
                win = TypetraceWindow(
                    self.db_manager,
                    self.keystroke_store,
                    self.settings,
                    application=self,
                )
                logger.debug("TypetraceWindow created")
            except Exception:
                logger.exception("Failed to create TypetraceWindow")
                raise
        else:
            logger.debug("Using existing active window")
        try:
            win.present()
            logger.debug("Window presented")
        except Exception:
            logger.exception("Failed to present window")
            raise

    def do_shutdown(self) -> None:
        """Clean up resources when the application shuts down."""
        logger.debug("Shutting down application")
        try:
            self.db_conn.close()
            logger.debug("Database connection closed")
        except Exception:
            logger.exception("Failed to close database connection")
        try:
            Gio.Application.do_shutdown(self)
            logger.debug("Application shutdown completed")
        except Exception:
            logger.exception("Failed during application shutdown")

    def _setup_actions(self) -> None:
        """Set up application actions and their shortcuts."""
        logger.debug("Setting up application actions")
        actions = [
            ("quit", self.quit, ["<primary>q"]),
            ("about", self.on_about_action),
            ("preferences", self.on_preferences_action),
        ]
        for args in actions:
            self.create_action(*args)

    def on_about_action(self, *_: Any) -> None:
        """Display the about dialog with application information."""
        logger.debug("Opening about dialog")
        try:
            about = Adw.AboutDialog(
                application_name="TypeTrace",
                application_icon="edu.ost.typetrace",
                website="https://github.com/domi413/TypeTrace",
                version=self.version,
                developers=[
                    "David Yves Bachmann",
                    "Dominik Bühler",
                    "Gioele Petrillo",
                    "Ivan Knöfler",
                    "Mustafa Alali",
                ],
            )
            about.present(self.props.active_window)
            logger.debug("About dialog presented")
        except Exception:
            logger.exception("Failed to present about dialog")
            raise

    def on_preferences_action(self, *_: Any) -> None:
        """Show the application preferences dialog."""
        logger.debug("Opening preferences dialog")
        try:
            pref_dialog = Preferences(
                parent_window=self.props.active_window,
                db_manager=self.db_manager,
                keystroke_store=self.keystroke_store,
                settings=self.settings,
            )
            pref_dialog.present(self.props.active_window)
            logger.debug("Preferences dialog presented")
        except Exception:
            logger.exception("Failed to present preferences dialog")
            raise

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
        logger.debug("Creating action: %s", name)
        try:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)
            logger.debug("Action '%s' added", name)
            if shortcuts:
                self.set_accels_for_action(f"app.{name}", shortcuts)
                logger.debug("Set shortcuts for action '%s': %s", name, shortcuts)
        except Exception:
            logger.exception("Failed to create or configure action '%s'", name)
            raise
