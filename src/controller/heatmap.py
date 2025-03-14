"""The heatmap widget that displays a keyboard."""

from gi.repository import Gtk

from ..model.keystrokes import KeystrokesModel  # noqa: TID252
from ..model.layouts import KEYBOARD_LAYOUTS  # noqa: TID252


@Gtk.Template(resource_path="/edu/ost/typetrace/view/heatmap.ui")
class Heatmap(Gtk.Box):
    """The heatmap widget that displays a keyboard."""

    __gtype_name__ = "Heatmap"

    keyboard_container = Gtk.Template.Child("keyboard_container")

    def __init__(self, model: KeystrokesModel, **kwargs) -> None:
        """Initialize the heatmap widget.

        Args:
            model: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.model: KeystrokesModel = model
        self.key_buttons: dict[int, tuple] = {}  # Keyed by scancode now
        self._build_keyboard()
        self._update_heatmap()

    def color_keys(self) -> None:
        """Public method to refresh the heatmap."""
        self._update_heatmap()

    def _build_keyboard(self) -> None:
        """Build the keyboard layout dynamically using scancodes."""
        arrow_icons = {
            "Left": "go-previous-symbolic",
            "Up": "go-up-symbolic",
            "Down": "go-down-symbolic",
            "Right": "go-next-symbolic",
        }
        expanded_keys = ["Backspace", "Tab", "Caps", "Enter", "Shift", "Space", "\\"]

        for row_count, row in enumerate(KEYBOARD_LAYOUTS["de_CH"]):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            self.keyboard_container.append(box)

            for scancode, key_label in row:
                button = Gtk.Button()
                if key_label in arrow_icons:
                    button.set_icon_name(arrow_icons[key_label])
                else:
                    button.set_label(key_label)
                if key_label in expanded_keys or row_count == 0:
                    button.set_hexpand(True)
                provider = Gtk.CssProvider()
                style_context = button.get_style_context()
                style_context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
                self.key_buttons[scancode] = (button, provider)  # Store by scancode
                box.append(button)

    def _update_heatmap(self) -> None:
        """Color the keys based on model data using scancodes."""
        keystrokes = self.model.get_all_keystrokes()
        total_presses = self.model.get_total_presses()

        if total_presses == 0:
            return  # Avoid division by zero

        for keystroke in keystrokes:
            scancode = keystroke.scan_code
            if scancode in self.key_buttons:
                button, provider = self.key_buttons[scancode]
                usage_ratio = keystroke.count / total_presses
                border_color = self._get_colors(usage_ratio)
                css = f"button {{ border: 2pt solid {border_color}; }}"
                provider.load_from_data(css.encode("utf-8"))

    def _get_colors(self, usage_ratio: float) -> str:
        """Calculate border-color based on usage ratio."""
        alpha = min(1.0, usage_ratio * 10)  # Red color with alpha increasing from 0 to 1
        return f"rgba({255}, {0}, {0}, {alpha})"
