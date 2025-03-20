"""The heatmap widget that displays a keyboard."""

from typing import ClassVar

from gi.repository import Gtk

from typetrace.model.keystrokes import KeystrokesModel
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

    keyboard_container = Gtk.Template.Child("keyboard_container")

    def __init__(self, model: KeystrokesModel, layout: str = "en_US", **kwargs) -> None:
        """Initialize the heatmap widget.

        Args:
            model: Access to keystrokes models
            layout: Keyboard layout to use
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.model: KeystrokesModel = model
        self.layout = layout
        self.key_widgets: dict[int, Gtk.Label] = {}  # Keyed by scancode
        self._build_keyboard()
        self._update_colors()

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
        label.set_size_request(40, 30)

        if key_label in self.EXPANDED_KEYS:
            label.set_hexpand(True)

        return label

    def _update_colors(self) -> None:
        keystrokes = self.model.get_all_keystrokes()
        most_pressed = self.model.get_highest_count()
        if most_pressed == 0:
            return

        for keystroke in keystrokes:
            scancode = keystroke.scan_code
            if scancode in self.key_widgets:
                label = self.key_widgets[scancode]
                usage_ratio = keystroke.count / most_pressed
                style_context = label.get_style_context()
                for cls in ["low-usage", "mid-usage", "high-usage"]:
                    style_context.remove_class(cls)
                if usage_ratio < 0.33:
                    style_context.add_class("low-usage")
                elif usage_ratio < 0.66:
                    style_context.add_class("mid-usage")
                else:
                    style_context.add_class("high-usage")
                label.set_tooltip_text(str(keystroke.count))

    def _get_colors(self, usage_ratio: float) -> str:
        """Calculate color based on usage ratio."""
        ratio = max(0.0, min(1.0, usage_ratio))
        return f"rgba({int(255 * ratio)}, {0}, {int(255 * (1 - ratio))}, 0.6)"
