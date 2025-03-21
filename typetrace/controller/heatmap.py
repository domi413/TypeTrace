"""The heatmap widget that displays a keyboard."""

from typing import ClassVar
from pathlib import Path
import shutil
from gi.repository import Gtk, GLib, Gio

from typetrace.model.keystrokes import KeystrokeStore
from typetrace.model.layouts import KEYBOARD_LAYOUTS


@Gtk.Template(resource_path="/edu/ost/typetrace/view/heatmap.ui")
class Heatmap(Gtk.Box):
    """The heatmap widget that displays a keyboard."""

    __gtype_name__ = "Heatmap"

    EXPANDED_KEYS: ClassVar[list[str]] = [
        "Backspace",
        "Tab",
        "Caps",
        "Enter",
        "Shift",
        "Space",
        "\\",
    ]

    USAGE_THRESHOLDS: ClassVar[dict[str, float]] = {
        "low": 0.33,
        "mid": 0.66,
    }

    keyboard_container = Gtk.Template.Child("keyboard_container")
    refresh_button = Gtk.Template.Child("refresh_button")

    def __init__(self, keystroke_store: KeystrokeStore, layout: str = "en_US", **kwargs) -> None:
        """Initialize the heatmap widget.

        Args:
            keystroke_store: Access to keystrokes
            layout: Keyboard layout to use
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store: KeystrokeStore = keystroke_store
        self.layout = layout
        self.key_widgets: dict[int, Gtk.Label] = {}  # Keyed by scancode

        self.refresh_button.connect("clicked", self._on_export_clicked)

        self._build_keyboard()
        self._update_colors()

    def _on_export_clicked(self, button: Gtk.Button) -> None:
        """Handle export button click."""
        src_path = Path(GLib.get_user_data_dir()) / "typetrace" / "TypeTrace.db"

        dialog = Gtk.FileDialog.new()
        dialog.set_title("Export data")
        dialog.set_initial_name("TypeTrace.db")

        # Set default folder to Downloads
        initial_folder = Gio.File.new_for_path(
            GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        )
        dialog.set_initial_folder(initial_folder)

        dialog.save(self.get_root(), None, self._on_file_chooser_response, src_path)

    def _on_file_chooser_response(
        self, dialog: Gtk.FileDialog, result: Gio.AsyncResult, src_path: Path
    ) -> None:
        """Handle the file chooser dialog response."""
        try:
            file = dialog.save_finish(result)
            if file:
                dst_path = Path(file.get_path())
                shutil.copy2(src_path, dst_path)

                success_dialog = Gtk.MessageDialog(
                    transient_for=self.get_root(),
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Data Exported Successfully",
                    secondary_text=f"Saved to: {dst_path}",
                )
                success_dialog.connect("response", lambda d, r: d.destroy())
                success_dialog.present()
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.get_root(),
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Export Failed",
                secondary_text=str(e),
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()

    def color_keys(self) -> None:
        """Public method to refresh the heatmap."""
        self._update_colors()

    def _build_keyboard(self) -> None:
        """Build the keyboard layout dynamically using scancodes."""
        for row_count, row in enumerate(KEYBOARD_LAYOUTS[self.layout]):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            if row_count == 0:
                box.set_homogeneous(True)
            self.keyboard_container.append(box)

            for scancode, key_label in row:
                label = self._create_key_widget(key_label)
                self.key_widgets[scancode] = label
                box.append(label)

    def _create_key_widget(self, key_label: str) -> Gtk.Label:
        """Create a single key widget with the appropriate properties."""
        label = Gtk.Label(label=key_label)
        label.set_hexpand(True) if key_label in self.EXPANDED_KEYS else None
        return label

    def _update_colors(self) -> None:
        keystrokes = self.keystroke_store.get_all_keystrokes()
        most_pressed = self.keystroke_store.get_highest_count()
        if not most_pressed:
            return

        for keystroke in keystrokes:
            if label := self.key_widgets.get(keystroke.scan_code):
                usage_ratio = keystroke.count / most_pressed
                self._get_key_color(label, usage_ratio)
                label.set_tooltip_text(str(keystroke.count))

    def _get_key_color(self, label: Gtk.Label, usage_ratio: float) -> str:
        """Assign color class based on usage ratio."""
        style_context = label.get_style_context()
        style_context.remove_class("low-usage mid-usage high-usage")
        class_name = (
            "low-usage"
            if usage_ratio < self.USAGE_THRESHOLDS["low"]
            else "mid-usage"
            if usage_ratio < self.USAGE_THRESHOLDS["mid"]
            else "high-usage"
        )
        style_context.add_class(class_name)
