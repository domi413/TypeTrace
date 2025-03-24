"""Database import handler implementations."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from typing import Any, final, override

from gi.repository import Adw, Gio, Gtk

from typetrace.preferences.database.base import DatabaseHandler


@final
class DatabaseImportHandler(DatabaseHandler):
    """Handler for database import operations."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        self.parent_dialog = parent_dialog

    @override
    def create_row(self) -> Adw.ActionRow:
        """See base class."""
        import_row = Adw.ActionRow(
            title="Import Database",
            subtitle="Import database from a file",
        )

        # Create a menu button with import options
        menu_button = Gtk.MenuButton(
            icon_name="document-open-symbolic",
            valign=Gtk.Align.CENTER,
        )

        # Create menu model for the dropdown
        menu = Gio.Menu()
        menu.append("Import from SQL File", "app.import-sql")
        menu.append("Import from DB File", "app.import-db")

        # Set the menu for the button
        menu_button.set_menu_model(menu)

        # Add actions to the parent window's action group
        action_group = Gio.SimpleActionGroup()

        # Create the SQL import action
        sql_action = Gio.SimpleAction.new("import-sql", None)
        sql_action.connect("activate", self._on_import_sql_clicked)
        action_group.add_action(sql_action)

        # Create the DB import action
        db_action = Gio.SimpleAction.new("import-db", None)
        db_action.connect("activate", self._on_import_db_clicked)
        action_group.add_action(db_action)

        # Insert the action group with a prefix
        self.parent_dialog.insert_action_group("app", action_group)

        import_row.add_suffix(menu_button)
        return import_row

    def _on_import_sql_clicked(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle click on the import from SQL option.

        Args:
            action: The action that was activated
            parameter: The parameter for the action

        """
        try:
            from typetrace.model.keystrokes import KeystrokeStore

            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Import Database from SQL File",
                transient_for=self.parent_dialog,
                action=Gtk.FileChooserAction.OPEN,
            )

            # Add buttons
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Open", Gtk.ResponseType.OK)

            # Add filters
            sql_filter = Gtk.FileFilter()
            sql_filter.set_name("SQL files")
            sql_filter.add_pattern("*.sql")
            dialog.add_filter(sql_filter)

            # Run the dialog
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                sql_path = dialog.get_filename()
                dialog.destroy()

                # Get target database path
                db_store = KeystrokeStore()
                db_path = db_store.db_path

                # Show confirmation dialog
                confirm_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Replace Current Database",
                    body="This will replace your current database with the imported one.\n\nYour current data will be lost. Continue?",
                    default_response="cancel",
                    close_response="cancel",
                )

                # Add action buttons
                confirm_dialog.add_response("cancel", "Cancel")
                confirm_dialog.add_response("import", "Import")
                confirm_dialog.set_response_appearance("import", Adw.ResponseAppearance.SUGGESTED)

                # Present dialog and wait for response
                confirm_dialog.connect(
                    "response", self._on_import_sql_confirmation, sql_path, db_path
                )
                confirm_dialog.present()
            else:
                dialog.destroy()

        except Exception as e:
            # Handle any errors
            error_dialog = Adw.MessageDialog(
                transient_for=self.parent_dialog,
                heading="Import Error",
                body=f"Failed to import from SQL file: {str(e)}",
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def _on_import_sql_confirmation(
        self, dialog: Adw.MessageDialog, response: str, sql_path: str, db_path: str
    ) -> None:
        """Handle confirmation for SQL import.

        Args:
            dialog: The dialog that triggered the response
            response: The dialog response
            sql_path: Path to the SQL file to import
            db_path: Path to the target database
        """
        if response == "import":
            try:
                # Create a temporary database to import into first (to validate)
                with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
                    temp_db_path = temp_db.name

                # Import SQL into the temporary database
                # This ensures the SQL is valid before replacing the actual database
                with open(sql_path, "r") as sql_file:
                    sql_content = sql_file.read()

                # Create new database from SQL
                conn = sqlite3.connect(temp_db_path)
                conn.executescript(sql_content)
                conn.close()

                # Validate the imported database has the expected structure
                conn = sqlite3.connect(temp_db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT scan_code, count, key_name FROM keystrokes LIMIT 1")
                    # If this doesn't raise an exception, the table structure is correct
                except sqlite3.OperationalError:
                    # Table structure is incorrect
                    conn.close()
                    os.unlink(temp_db_path)
                    raise ValueError(
                        "The SQL file does not contain a valid TypeTrace database structure."
                    )

                conn.close()

                # Backup the current database
                backup_path = f"{db_path}.bak"
                if os.path.exists(db_path):
                    import shutil

                    shutil.copy2(db_path, backup_path)

                # Replace the actual database with the validated imported one
                import shutil

                shutil.copy2(temp_db_path, db_path)

                # Clean up
                os.unlink(temp_db_path)

                # Show success message
                success_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Import Successful",
                    body=f"Database successfully imported from SQL file. A backup of your previous database was saved to {backup_path}",
                )
                success_dialog.add_response("ok", "OK")
                success_dialog.present()

            except Exception as e:
                # Handle any errors
                error_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Import Error",
                    body=f"Failed to import database: {str(e)}",
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

    def _on_import_db_clicked(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle click on the import from DB file option.

        Args:
            action: The action that was activated
            parameter: The parameter for the action
        """
        try:
            from typetrace.model.keystrokes import KeystrokeStore

            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Import Database from DB File",
                transient_for=self.parent_dialog,
                action=Gtk.FileChooserAction.OPEN,
            )

            # Add buttons
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Open", Gtk.ResponseType.OK)

            # Add filters
            db_filter = Gtk.FileFilter()
            db_filter.set_name("SQLite Database files")
            db_filter.add_pattern("*.db")
            db_filter.add_pattern("*.sqlite")
            db_filter.add_pattern("*.sqlite3")
            dialog.add_filter(db_filter)

            # Run the dialog
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                import_db_path = dialog.get_filename()
                dialog.destroy()

                # Get target database path
                db_store = KeystrokeStore()
                db_path = db_store.db_path

                # Show confirmation dialog
                confirm_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Replace Current Database",
                    body="This will replace your current database with the imported one.\n\nYour current data will be lost. Continue?",
                    default_response="cancel",
                    close_response="cancel",
                )

                # Add action buttons
                confirm_dialog.add_response("cancel", "Cancel")
                confirm_dialog.add_response("import", "Import")
                confirm_dialog.set_response_appearance("import", Adw.ResponseAppearance.SUGGESTED)

                # Present dialog and wait for response
                confirm_dialog.connect(
                    "response", self._on_import_db_confirmation, import_db_path, db_path
                )
                confirm_dialog.present()
            else:
                dialog.destroy()

        except Exception as e:
            # Handle any errors
            error_dialog = Adw.MessageDialog(
                transient_for=self.parent_dialog,
                heading="Import Error",
                body=f"Failed to import from DB file: {str(e)}",
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def _on_import_db_confirmation(
        self, dialog: Adw.MessageDialog, response: str, import_db_path: str, db_path: str
    ) -> None:
        """Handle confirmation for DB import.

        Args:
            dialog: The dialog that triggered the response
            response: The dialog response
            import_db_path: Path to the DB file to import
            db_path: Path to the target database
        """
        if response == "import":
            try:
                # Validate the imported database has the expected structure
                conn = sqlite3.connect(import_db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT scan_code, count, key_name FROM keystrokes LIMIT 1")
                    # If this doesn't raise an exception, the table structure is correct
                except sqlite3.OperationalError:
                    # Table structure is incorrect
                    conn.close()
                    raise ValueError(
                        "The database file does not contain a valid TypeTrace database structure."
                    )

                conn.close()

                # Backup the current database
                backup_path = f"{db_path}.bak"
                if os.path.exists(db_path):
                    import shutil

                    shutil.copy2(db_path, backup_path)

                # Replace the current database with the imported one
                import shutil

                shutil.copy2(import_db_path, db_path)

                # Show success message
                success_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Import Successful",
                    body=f"Database successfully imported. A backup of your previous database was saved to {backup_path}",
                )
                success_dialog.add_response("ok", "OK")
                success_dialog.present()

            except Exception as e:
                # Handle any errors
                error_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Import Error",
                    body=f"Failed to import database: {str(e)}",
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
