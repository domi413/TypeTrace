"""The heatmap widget that displays a keyboard."""

from gi.repository import Gtk

from ..model.keystrokes import KeystrokesModel  # noqa: TID252

KEYBOARD_LAYOUT = [
    ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
    ["~", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"],
    ["Ctrl", "Alt", "Space", "Alt", "Ctrl", "Left", "Up", "Down", "Right"],
]


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
        self.key_buttons: tuple[str, str] = {}
        self._build_keyboard()
        self._update_heatmap()

    def color_keys(self) -> None:
        """Public method to refresh the heatmap."""
        self._update_heatmap()

    def _build_keyboard(self) -> None:
        """Build the keyboard layout dynamically."""
        arrow_icons = {
            "Left": "go-previous-symbolic",
            "Up": "go-up-symbolic",
            "Down": "go-down-symbolic",
            "Right": "go-next-symbolic",
        }
        expanded_keys = ["Backspace", "Tab", "Caps", "Enter", "Shift", "Space", "\\"]

        for row_count, row in enumerate(KEYBOARD_LAYOUT):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            self.keyboard_container.append(box)

            for key in row:
                button = Gtk.Button()
                if key in arrow_icons:
                    button.set_icon_name(arrow_icons[key])
                else:
                    button.set_label(key)
                if key in expanded_keys or row_count == 0:
                    button.set_hexpand(True)
                provider = Gtk.CssProvider()
                style_context = button.get_style_context()
                style_context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
                self.key_buttons[key.upper()] = (button, provider)
                box.append(button)

    def _update_heatmap(self) -> None:
        """Color the keys based on model data."""
        keystrokes = self.model.get_all_keystrokes()
        total_presses = self.model.get_total_presses()

        if total_presses == 0:
            return  # Avoid division by zero

        for keystroke in keystrokes:
            model_key = keystroke.key_name.upper()
            ui_key = self._map_model_to_ui_key(model_key)
            if ui_key and ui_key in self.key_buttons:
                button, provider = self.key_buttons[ui_key]
                usage_ratio = keystroke.count / total_presses
                border_color = self._get_colors(usage_ratio)
                css = f"button {{ border: 2pt solid {border_color}; }}"
                provider.load_from_data(css.encode("utf-8"))

    def _get_colors(self, usage_ratio: float) -> str:
        """Calculate border-color based on usage ratio."""
        alpha = min(1.0, usage_ratio * 10)  # Red color with alpha increasing from 0 to 1
        return f"rgba({255}, {0}, {0}, {alpha})"

    def _map_model_to_ui_key(self, model_key: str) -> str:
        """Map evdev key names (KEY_A, KEY_CTRL) to UI labels (A, CTRL)."""
        if not model_key.startswith("KEY_"):
            return None
        key = model_key[4:]

        if len(key) == 1 and key.isalnum():
            return key

        special_mappings = {
            "ESC": "ESC",
            "BACKSPACE": "BACKSPACE",
            "TAB": "TAB",
            "CAPSLOCK": "CAPS",
            "ENTER": "ENTER",
            "SHIFT": "SHIFT",
            "LEFTSHIFT": "SHIFT",
            "RIGHTSHIFT": "SHIFT",
            "CTRL": "CTRL",
            "LEFTCTRL": "CTRL",
            "RIGHTCTRL": "CTRL",
            "ALT": "ALT",
            "LEFTALT": "ALT",
            "RIGHTALT": "ALT",
            "SPACE": "SPACE",
            "LEFT": "LEFT",
            "UP": "UP",
            "DOWN": "DOWN",
            "RIGHT": "RIGHT",
            "GRAVE": "~",
            "MINUS": "-",
            "EQUAL": "=",
            "LEFTBRACE": "[",
            "RIGHTBRACE": "]",
            "BACKSLASH": "\\",
            "SEMICOLON": ";",
            "APOSTROPHE": "'",
            "COMMA": ",",
            "DOT": ".",
            "SLASH": "/",
        }
        return special_mappings.get(key)
