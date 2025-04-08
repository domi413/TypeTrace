"""The heatmap widget that displays a keyboard."""

from typing import ClassVar

from gi.repository import Adw, Gdk, Gtk

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

    keyboard_container = Gtk.Template.Child()
    refresh_button = Gtk.Template.Child()

    def __init__(
        self,
        keystroke_store: KeystrokeStore,
        layout: str = "en_US",
        beg_color: tuple[float, float, float] | None = None,
        end_color: tuple[float, float, float] = (0.7, 0.3, 0.9),
    ) -> None:
        """Initialize the heatmap widget.

        Args:
            keystroke_store: Access to keystrokes.
            layout: Keyboard layout to use.
            beg_color: RGB tuple (0.0 to 1.0) for the lowest frequency. If None, use theme color.
            end_color: RGB tuple (0.0 to 1.0) for the highest frequency.

        """
        super().__init__()
        self.keystroke_store: KeystrokeStore = keystroke_store
        self.layout = layout
        self.beg_color = beg_color
        self.end_color = end_color
        self.key_widgets: dict[int, Gtk.Label] = {}  # Keyed by scancode

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Get the style manager and connect to theme change signal
        self.style_manager = Adw.StyleManager.get_default()
        self.style_manager.connect("notify::dark", self._on_theme_changed)

        self.refresh_button.connect("clicked", lambda *_: self._update_colors())

        self._build_keyboard()
        self._update_colors()

    def _on_theme_changed(self, *args):
        """Called when the theme changes between light and dark."""
        # Reset beg_color to None to force it to be recalculated based on the new theme
        self.beg_color = None
        self._update_colors()

    def _get_theme_background_color(self) -> tuple[float, float, float]:
        """Get the appropriate background color based on the current theme."""
        is_dark = self.style_manager.get_dark()
        if is_dark:
            return (0.2, 0.2, 0.2)  # Dark theme background (dark gray)
        return (0.95, 0.95, 0.95)  # Light theme background (light gray)

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
        return label

    def _update_colors(self) -> None:
        keystrokes = self.keystroke_store.get_all_keystrokes()
        most_pressed = self.keystroke_store.get_highest_count()
        if not most_pressed:
            return

        if self.beg_color is None:
            # Get theme's background color using a CSS provider
            style_manager = Adw.StyleManager.get_default()
            is_dark = style_manager.get_dark()

            if is_dark:
                # Dark theme background color (approximate)
                self.beg_color = (0.2, 0.2, 0.2)  # Dark gray
            else:
                # Light theme background color (approximate)
                self.beg_color = (0.95, 0.95, 0.95)  # Light gray

        beg_r, beg_g, beg_b = [int(x * 255) for x in self.beg_color]
        end_r, end_g, end_b = [int(x * 255) for x in self.end_color]
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
                bg_color, text_color = self._calculate_color(normalized_count)
                css_rules.append(f"""
                .{css_class} {{
                    background-color: {bg_color.to_string()};
                    color: {text_color};
                }}""")
                label.set_css_classes([css_class])
                label.set_tooltip_text(str(keystroke.count))

        self.css_provider.load_from_string("\n".join(css_rules))

    def _calculate_color(self, normalized: float) -> tuple[Gdk.RGBA, str]:
        """Calculate heatmap color and contrast text color based on normalized count.

        Args:
            normalized: A float between 0.0 and 1.0.

        Returns:
            A tuple containing:
                - Gdk.RGBA: The calculated background color (Blue -> Yellow -> Red).
                - str: The calculated text color ('white' or 'black') for contrast.

        """
        r = self.beg_color[0] + normalized * (self.end_color[0] - self.beg_color[0])
        g = self.beg_color[1] + normalized * (self.end_color[1] - self.beg_color[1])
        b = self.beg_color[2] + normalized * (self.end_color[2] - self.beg_color[2])
        bg_color = Gdk.RGBA(red=r, green=g, blue=b, alpha=1.0)
        luminance = 0.3 * r + 0.6 * g + 0.1 * b  # Luminance formula provides brightness
        text_color = "white" if luminance < 0.5 else "black"  # noqa: PLR2004
        return bg_color, text_color
