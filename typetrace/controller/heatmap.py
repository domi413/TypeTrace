"""The heatmap widget that displays a keyboard."""

from typing import ClassVar

from gi.repository import Gtk

from typetrace.model.keystrokes import KeystrokesModel
from typetrace.model.layouts import KEYBOARD_LAYOUTS


@Gtk.Template(resource_path="/edu/ost/typetrace/view/heatmap.ui")
class Heatmap(Gtk.Box):
    """The heatmap widget that displays a keyboard."""

    __gtype_name__ = "Heatmap"

    ARROW_ICONS: ClassVar[dict[str, str]] = {
        "Left": "go-previous-symbolic",
        "Up": "go-up-symbolic",
        "Down": "go-down-symbolic",
        "Right": "go-next-symbolic",
    }

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
        self.key_buttons: dict[int, tuple] = {}  # Keyed by scancode
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
                button, provider = self._create_key_button(key_label)
                self.key_buttons[scancode] = (button, provider)
                box.append(button)

    def _create_key_button(self, key_label: str) -> tuple[Gtk.Button, Gtk.CssProvider]:
        """Create a single key button with the appropriate properties."""
        button = Gtk.Button()

        if key_label in self.ARROW_ICONS:
            button.set_icon_name(self.ARROW_ICONS[key_label])
        else:
            button.set_label(key_label)

        if key_label in self.EXPANDED_KEYS:
            button.set_hexpand(True)

        provider = Gtk.CssProvider()
        style_context = button.get_style_context()
        style_context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        return button, provider

    def _update_colors(self) -> None:
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
                color = self._get_colors(usage_ratio)
                css = f"button {{ background-color: {color}; }}"
                provider.load_from_data(css.encode("utf-8"))
                button.set_tooltip_text(str(keystroke.count))

    def _get_colors(self, usage_ratio: float) -> str:
        """Calculate color based on usage ratio."""
        ratio = max(0.0, min(1.0, usage_ratio * 3))
        return f"rgb({int(255 * ratio)}, {0}, {int(255 * (1 - ratio))})"
