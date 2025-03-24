"""Database export handler implementations."""

from __future__ import annotations

import csv
import os
import sqlite3
import subprocess
from typing import Any, final, override

from gi.repository import Adw, Gio, Gtk

from typetrace.preferences.database.base import DatabaseHandler


@final
class DatabaseExportHandler(DatabaseHandler):
    """Handler for database export operations."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        self.parent_dialog = parent_dialog

    @override
    def create_row(self) -> Adw.ActionRow:
        """See base class."""
        export_row = Adw.ActionRow(
            title="Export Database",
            subtitle="Export the database as CSV or SQL",
        )

        # Create a menu button with export options
        menu_button = Gtk.MenuButton(
            icon_name="document-save-symbolic",
            valign=Gtk.Align.CENTER,
        )

        # Create menu model for the dropdown
        menu = Gio.Menu()
        menu.append("Export as CSV", "app.export-csv")
        menu.append("Export as SQL", "app.export-sql")

        # Set the menu for the button
        menu_button.set_menu_model(menu)

        # Add actions to the parent window's action group
        action_group = Gio.SimpleActionGroup()

        # Create the CSV export action
        csv_action = Gio.SimpleAction.new("export-csv", None)
        csv_action.connect("activate", self._on_export_csv)
        action_group.add_action(csv_action)

        # Create the SQL export action
        sql_action = Gio.SimpleAction.new("export-sql", None)
        sql_action.connect("activate", self._on_export_sql)
        action_group.add_action(sql_action)

        # Insert the action group with a prefix
        self.parent_dialog.insert_action_group("app", action_group)

        export_row.add_suffix(menu_button)
        return export_row

    def _on_export_csv(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle click on the export as CSV option.

        Args:
            action: The action that was activated
            parameter: The parameter for the action

        """
        try:
            from typetrace.model.keystrokes import KeystrokeStore

            # Get database path
            db_store = KeystrokeStore()
            db_path = db_store.db_path

            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Export Database as CSV",
                transient_for=self.parent_dialog,
                action=Gtk.FileChooserAction.SAVE,
            )

            # Add buttons
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.OK)

            # Set default filename (same as DB name but with .csv extension)
            default_name = os.path.basename(db_path).replace(".db", ".csv")
            dialog.set_current_name(default_name)

            # Add filters
            csv_filter = Gtk.FileFilter()
            csv_filter.set_name("CSV files")
            csv_filter.add_pattern("*.csv")
            dialog.add_filter(csv_filter)

            # Run the dialog
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                csv_path = dialog.get_filename()

                # Ensure CSV extension
                if not csv_path.endswith(".csv"):
                    csv_path += ".csv"

                # Connect to the database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Execute query to fetch all data
                cursor.execute("SELECT scan_code, count, key_name FROM keystrokes")
                rows = cursor.fetchall()

                # Write to CSV file
                with open(csv_path, "w", newline="") as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(["scan_code", "count", "key_name"])
                    csv_writer.writerows(rows)

                conn.close()

                # Show success message
                success_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Export Successful",
                    body=f"Database exported to CSV file:\n{csv_path}",
                )
                success_dialog.add_response("ok", "OK")
                success_dialog.present()

            dialog.destroy()

        except Exception as e:
            # Handle any errors
            error_dialog = Adw.MessageDialog(
                transient_for=self.parent_dialog,
                heading="Export Error",
                body=f"Failed to export database as CSV: {str(e)}",
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()

    def _on_export_sql(self, action: Gio.SimpleAction, parameter: Any) -> None:
        """Handle click on the export as SQL option.

        Args:
            action: The action that was activated
            parameter: The parameter for the action

        """
        try:
            from typetrace.model.keystrokes import KeystrokeStore

            # Get database path
            db_store = KeystrokeStore()
            db_path = db_store.db_path

            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Export Database as SQL",
                transient_for=self.parent_dialog,
                action=Gtk.FileChooserAction.SAVE,
            )

            # Add buttons
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.OK)

            # Set default filename (same as DB name but with .sql extension)
            default_name = os.path.basename(db_path).replace(".db", ".sql")
            dialog.set_current_name(default_name)

            # Add filters
            sql_filter = Gtk.FileFilter()
            sql_filter.set_name("SQL files")
            sql_filter.add_pattern("*.sql")
            dialog.add_filter(sql_filter)

            # Run the dialog
            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                sql_path = dialog.get_filename()

                # Ensure SQL extension
                if not sql_path.endswith(".sql"):
                    sql_path += ".sql"

                # Export using sqlite3 command line (dumps schema and data)
                result = subprocess.run(
                    ["sqlite3", db_path, ".dump"], capture_output=True, text=True, check=True
                )

                # Write output to the SQL file
                with open(sql_path, "w") as f:
                    f.write(result.stdout)

                # Show success message
                success_dialog = Adw.MessageDialog(
                    transient_for=self.parent_dialog,
                    heading="Export Successful",
                    body=f"Database exported to SQL file:\n{sql_path}",
                )
                success_dialog.add_response("ok", "OK")
                success_dialog.present()

            dialog.destroy()

        except Exception as e:
            # Handle any errors
            error_dialog = Adw.MessageDialog(
                transient_for=self.parent_dialog,
                heading="Export Error",
                body=f"Failed to export database as SQL: {str(e)}",
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
