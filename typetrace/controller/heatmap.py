"""The heatmap widget that displays a keyboard."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from gi.repository import Gdk, Gio, Gtk

from typetrace.model.layouts import KEYBOARD_LAYOUTS

if TYPE_CHECKING:
    from typetrace.model.keystrokes import KeystrokeStore


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

    keyboard_container = Gtk.Template.Child()

    zoom_in_button = Gtk.Template.Child()
    zoom_out_button = Gtk.Template.Child()

    def __init__(
        self,
        settings: Gio.Settings,
        keystroke_store: KeystrokeStore,
        layout: str = "en_US",
    ) -> None:
        """Initialize the heatmap widget.

        Args:
            settings: Gio settings used to persist and apply preferences.
            keystroke_store: Access to keystrokes.
            layout: Keyboard layout to use.

        """
        super().__init__()
        self.settings = settings
        self.keystroke_store: KeystrokeStore = keystroke_store
        self.layout = layout
        self.key_widgets: dict[int, Gtk.Label] = {}  # Keyed by scancode

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.zoom_in_button.connect("clicked", lambda *_: self._on_zoom_clicked(5))
        self.zoom_out_button.connect("clicked", lambda *_: self._on_zoom_clicked(-5))

        self.settings.connect(
            "changed::heatmap-begin-color",
            lambda *_: self._update_colors(),
        )
        self.settings.connect(
            "changed::heatmap-end-color",
            lambda *_: self._update_colors(),
        )

        self._build_keyboard()
        self._update_colors()

    def update(self) -> None:
        """Update the heatmap to reflect current data."""
        self._update_colors()

    def _build_keyboard(self) -> None:
        """Build the keyboard layout dynamically using scancodes."""
        for row_count, row in enumerate(KEYBOARD_LAYOUTS[self.layout]):
            box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                spacing=5,
            )
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
        size = self.settings.get_int("key-size")
        label.set_size_request(size, size)
        return label

    def _get_color_tuple_from_settings(self, key: str) -> tuple[float, float, float]:
        """Get RGB color tuple from settings.

        Args:
            key: The settings key to get color from.

        Returns:
            A tuple of RGB values with each value between 0.0 and 1.0.

        """
        color_str = self.settings.get_string(key)

        if color_str.startswith("rgb("):
            r, g, b = map(int, color_str[4:-1].split(","))
            return (r / 255.0, g / 255.0, b / 255.0)

        return (0.0, 0.0, 1.0) if key == "heatmap-begin-color" else (1.0, 0.0, 0.0)

    def _update_colors(self) -> None:
        """Assign each displayed key the appropriate color."""
        keystrokes = self.keystroke_store.get_all_keystrokes()
        most_pressed = self.keystroke_store.get_highest_count()
        if not most_pressed:
            return

        beg_color = self._get_color_tuple_from_settings("heatmap-begin-color")
        end_color = self._get_color_tuple_from_settings("heatmap-end-color")

        beg_r, beg_g, beg_b = [int(x * 255) for x in beg_color]
        end_r, end_g, end_b = [int(x * 255) for x in end_color]

        gradient_css = f"""
        .gradient-bar {{
            background: linear-gradient(to right,
                rgb({beg_r}, {beg_g}, {beg_b}),
                rgb({end_r}, {end_g}, {end_b}));
        }}
        """

        css_rules = [gradient_css]
        for keystroke in keystrokes:
            if label := self.key_widgets.get(keystroke.scan_code):
                css_class = f"scancode-{keystroke.scan_code}"
                normalized_count = keystroke.count / most_pressed
                bg_color, text_color = self._calculate_color(
                    normalized_count,
                    beg_color,
                    end_color,
                )
                css_rules.append(f"""
                .{css_class} {{
                    background-color: {bg_color};
                    color: {text_color};
                }}""")
                label.set_css_classes([css_class])
                label.set_tooltip_text(str(keystroke.count))

        self.css_provider.load_from_string("\n".join(css_rules))

    def _calculate_color(
        self,
        normalized: float,
        beg_color: tuple[float, float, float],
        end_color: tuple[float, float, float],
    ) -> tuple[str, str]:
        """Calculate heatmap color and contrast text color based on normalized count.

        Args:
            normalized: A float between 0.0 and 1.0.
            beg_color: RGB tuple for the lowest frequency color.
            end_color: RGB tuple for the highest frequency color.

        Returns:
            A tuple containing:
                - str: The calculated background color (Blue -> Yellow -> Red).
                - str: The calculated text color ('white' or 'black') for contrast.

        """
        r = beg_color[0] + normalized * (end_color[0] - beg_color[0])
        g = beg_color[1] + normalized * (end_color[1] - beg_color[1])
        b = beg_color[2] + normalized * (end_color[2] - beg_color[2])
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)
        bg_color = f"rgb({r_int}, {g_int}, {b_int})"
        luminance = 0.3 * r + 0.6 * g + 0.1 * b  # Luminance formula provides brightness
        text_color = "white" if luminance < 0.5 else "black"  # noqa: PLR2004
        return bg_color, text_color

    def _on_zoom_clicked(self, amount: int) -> None:
        size = max(self.settings.get_int("key-size") + amount, 40)
        self.settings.set_int("key-size", size)
        for label in self.key_widgets.values():
            label.set_size_request(size, size)
