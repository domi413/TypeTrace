"""A preferences dialog that handles various settings and preferences."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from gi.repository import Adw, Gio, Gtk

from typetrace.config import Config, DatabasePath
from typetrace.controller.utils import desktop_utils, dialog_utils
from typetrace.controller.utils.color_utils import parse_color_string

if TYPE_CHECKING:
    from pathlib import Path

    from typetrace.model.database_manager import DatabaseManager
    from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/preferences.ui")
class Preferences(Adw.PreferencesDialog):
    """A dialog for managing application preferences."""

    __gtype_name__ = "Preferences"

    import_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    locate_button = Gtk.Template.Child()
    autostart_row = Gtk.Template.Child()
    heatmap_begin_color_button = Gtk.Template.Child()
    heatmap_end_color_button = Gtk.Template.Child()
    single_color_switch = Gtk.Template.Child()
    end_color_box = Gtk.Template.Child()
    begin_color_label = Gtk.Template.Child()
    reverse_gradient_switch = Gtk.Template.Child()

    def __init__(
        self,
        parent_window: Gtk.Window,
        db_manager: DatabaseManager,
        keystroke_store: KeystrokeStore,
        settings: Gio.Settings,
    ) -> None:
        """Initialize the preferences dialog with a parent window and database manager.

        Args:
            parent_window: The main application window, used as parent for dialogs.
            db_manager: Manages database import/export operations.
            keystroke_store: Manages access to and clearing of keystroke data.
            settings: Application settings.

        """
        super().__init__()
        self.parent_window = parent_window

        self.settings = settings
        self.db_manager = db_manager
        self.keystroke_store = keystroke_store

        begin_dialog = Gtk.ColorDialog(title="Select Begin Color", modal=True)
        end_dialog = Gtk.ColorDialog(title="Select End Color", modal=True)

        self.heatmap_begin_color_button.set_dialog(begin_dialog)
        self.heatmap_end_color_button.set_dialog(end_dialog)

        self.autostart_row.set_active(desktop_utils.is_autostart_enabled())
        self.autostart_row.connect("notify::active", self._on_autostart_toggled)

        self.import_button.connect("clicked", self._on_import_clicked)
        self.export_button.connect("clicked", self._on_export_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)
        self.locate_button.connect("clicked", self._on_locate_clicked)

        self._init_color_buttons()
        self._setup_switch(
            self.single_color_switch,
            "use-single-color-heatmap",
            self._on_single_color_toggled,
        )
        self._setup_switch(
            self.reverse_gradient_switch,
            "reverse-heatmap-gradient",
            self._on_reverse_gradient_toggled,
        )

        self.heatmap_begin_color_button.connect(
            "notify::rgba",
            lambda button, _param: self._handle_color_change(
                button,
                "heatmap-begin-color",
            ),
        )
        self.heatmap_end_color_button.connect(
            "notify::rgba",
            lambda button, _param: self._handle_color_change(
                button,
                "heatmap-end-color",
            ),
        )

        is_single_color = self.settings.get_boolean("use-single-color-heatmap")
        self.end_color_box.set_visible(not is_single_color)
        self.reverse_gradient_switch.set_visible(is_single_color)
        self.begin_color_label.set_label("Color" if is_single_color else "Begin")

    def _init_color_buttons(self) -> None:
        """Initialize color buttons with current settings."""
        begin_color = parse_color_string(
            self.settings.get_string("heatmap-begin-color"),
        )
        end_color = parse_color_string(
            self.settings.get_string("heatmap-end-color"),
        )

        self.heatmap_begin_color_button.set_rgba(begin_color)
        self.heatmap_end_color_button.set_rgba(end_color)

    def _setup_switch(
        self,
        switch: Adw.SwitchRow,
        setting_key: str,
        handler: Callable[[Adw.SwitchRow, Any], None],
    ) -> None:
        """Set up a switch and bind it to a setting.

        Args:
            switch: The switch widget to set up
            setting_key: The setting key to bind to
            handler: The callback function for notify::active signal

        """
        self.settings.bind(
            setting_key,
            switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        switch.connect(
            "notify::active",
            handler,
        )

    def _on_single_color_toggled(self, switch: Adw.SwitchRow, _: any) -> None:
        """Handle the single color switch toggle."""
        is_single_color = switch.get_active()
        self.end_color_box.set_visible(not is_single_color)
        self.reverse_gradient_switch.set_visible(is_single_color)
        self.begin_color_label.set_label("Color" if is_single_color else "Begin")

        mode = "Single color" if is_single_color else "Multi-color"
        dialog_utils.show_toast(self, f"Heatmap mode set to: {mode}")

    def _on_reverse_gradient_toggled(self, switch: Adw.SwitchRow, _: any) -> None:
        """Handle the reverse gradient switch toggle."""
        is_reversed = switch.get_active()
        direction = "Dark → Light" if is_reversed else "Light → Dark"
        dialog_utils.show_toast(self, f"Gradient direction: {direction}")

    def _handle_color_change(
        self,
        button: Gtk.ColorDialogButton,
        setting_key: str,
    ) -> None:
        """Handle color change from a color button.

        Args:
            button: The color dialog button that was changed.
            setting_key: The settings key to update.

        """
        rgba = button.get_rgba()
        color_str = (
            f"rgb({int(rgba.red * 255)},{int(rgba.green * 255)},{int(rgba.blue * 255)})"
        )
        self.settings.set_string(setting_key, color_str)
        dialog_utils.show_toast(self, "Heatmap color updated")

    def _on_autostart_toggled(self, row: Adw.SwitchRow, *_: any) -> None:
        """Handle the autostart toggle change."""
        if row.get_active():
            success, error_msg = desktop_utils.enable_autostart()
            if success:
                dialog_utils.show_toast(self, "Backend autostart enabled")
            else:
                dialog_utils.show_error_dialog(
                    self.parent_window,
                    "Failed to enable autostart",
                    secondary_text=error_msg,
                )
                row.set_active(False)
        else:
            success, error_msg = desktop_utils.disable_autostart()
            if success:
                dialog_utils.show_toast(self, "Backend autostart disabled")
            else:
                dialog_utils.show_error_dialog(
                    self.parent_window,
                    "Failed to disable autostart",
                    secondary_text=error_msg,
                )
                row.set_active(True)

    def _on_export_clicked(self, _button: Gtk.Button) -> None:
        """Handle the export button click event, opens a save dialog for export."""

        def export_callback(path: Path) -> None:
            if self.db_manager.export_database(path):
                dialog_utils.show_toast(self, "Data Exported Successfully")
            else:
                dialog_utils.show_error_dialog(self.parent_window, "Export Failed")

        dialog_utils.open_file_save_dialog(
            parent=self.parent_window,
            title="Export data",
            initial_name=Config.DB_NAME,
            callback=export_callback,
        )

    def _on_import_clicked(self, _button: Gtk.Button) -> None:
        """Handle the import button click event, opens a file chooser dialog."""

        def import_callback(path: Path) -> None:
            dialog_utils.show_confirmation_dialog(
                parent=self.parent_window,
                text="Confirm Data Import",
                secondary_text="This will override your current data, continue?",
                callback=lambda: self._perform_import(path),
            )

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Database files")
        file_filter.add_pattern("*.db")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)

        dialog_utils.open_file_open_dialog(
            parent=self.parent_window,
            title="Import data",
            filters=filters,
            callback=import_callback,
        )

    def _perform_import(self, src_path: Path) -> None:
        """Perform the database import operation after user confirmation.

        Args:
            src_path: The path to the database file for import.

        """
        if self.db_manager.import_database(src_path):
            dialog_utils.show_toast(self, "Data Imported Successfully")
        else:
            dialog_utils.show_error_dialog(self.parent_window, "Import Failed")

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        """Perform the database clear operation after user confirmation."""

        def delete_callback() -> None:
            if self.keystroke_store.clear():
                dialog_utils.show_toast(self, "Data Cleared Successfully")
            else:
                dialog_utils.show_error_dialog(self.parent_window, "Clear Failed")

        dialog_utils.show_confirmation_dialog(
            parent=self.parent_window,
            text="Confirm Database Clear",
            secondary_text="This permanently removes all recorded data, continue?",
            callback=lambda: delete_callback(),
        )

    def _on_locate_clicked(self, _button: Gtk.Button) -> None:
        """Open Filemanager where the data file is stored."""
        dialog_utils.show_folder_in_filemanager(DatabasePath.DB_PATH.parent)
