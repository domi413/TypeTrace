"""Defines the Heatmap class, which represents a widget for displaying a keyboard heatmap.

The heatmap visualizes keystroke data using color gradients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from gi.repository import Gdk, Gio, GLib, Gtk

from typetrace.model.keystrokes import KeystrokeStore
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
    LUMINANCE_THRESHOLD: ClassVar[float] = 0.5  # Threshold for deciding text color based on luminance

    keyboard_container = Gtk.Template.Child()
    zoom_in_button = Gtk.Template.Child()
    zoom_out_button = Gtk.Template.Child()

    def __init__(
        self,
        settings: Gio.Settings,
        keystroke_store: KeystrokeStore,
        layout: str = "en_US",
        gradient_colors: tuple[
            tuple[float, float, float],
            tuple[float, float, float],
        ] = (
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0),
        ),
    ) -> None:
        """Initialize the Heatmap widget.

        Args:
        ----
            settings: The GSettings object for storing widget settings.
            keystroke_store: The store containing keystroke data.
            layout: The keyboard layout to display (default: "en_US").
            gradient_colors: A tuple of (beg_color, end_color) for the heatmap gradient,
                where each color is a tuple of (r, g, b) floats from 0.0 to 1.0.
                Defaults to blue ((0.0, 0.0, 1.0)) to red ((1.0, 0.0, 0.0)).

        """
        super().__init__()
        self.settings = settings
        self.keystroke_store = keystroke_store
        self.layout = layout
        self.beg_color, self.end_color = gradient_colors
        self.key_widgets: dict[int, Gtk.Label] = {}

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.zoom_in_button.connect(
            "clicked",
            lambda *_: self._on_zoom_clicked(5),
        )
        self.zoom_out_button.connect("clicked", lambda *_: self._on_zoom_clicked(-5))

        self._build_keyboard()
        self._update_colors()

    def update(self) -> None:
        """Refresh the heatmap colors."""
        self._update_colors()

    def _build_keyboard(self) -> None:
        for row_idx, row in enumerate(KEYBOARD_LAYOUTS[self.layout]):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            if row_idx == 0:
                box.set_homogeneous(True)
            self.keyboard_container.append(box)
            for scan_code, label_text in row:
                label = self._create_key_widget(label_text)
                self.key_widgets[scan_code] = label
                box.append(label)

    def _create_key_widget(self, text: str) -> Gtk.Label:
        label = Gtk.Label(label=text)
        if text in self.EXPANDED_KEYS:
            label.set_hexpand(True)
        size = self.settings.get_int("key-size")
        label.set_size_request(size, size)
        return label

    def _update_colors(self) -> None:
        keys = self.keystroke_store.get_all_keystrokes()
        top = self.keystroke_store.get_highest_count()

        b_r, b_g, b_b = (int(c * 255) for c in self.beg_color)
        e_r, e_g, e_b = (int(c * 255) for c in self.end_color)
        grad_css = f"""
        .gradient-bar {{
          background: linear-gradient(to right,
            rgb({b_r},{b_g},{b_b}),
            rgb({e_r},{e_g},{e_b})
          );
        }}"""
        rules = [grad_css]

        default_r, default_g, default_b = 239, 239, 239
        for scan_code, label in self.key_widgets.items():
            css_class = f"scancode-{scan_code}"
            label.set_css_classes([])
            if not keys:
                rules.append(
                    f"""
                .{css_class} {{
                  background-color: rgb({default_r},{default_g},{default_b});
                  color: black;
                }}""",
                )
                label.set_css_classes([css_class])
                label.set_tooltip_text("0")

        if top == 0:
            self.css_provider.load_from_string("\n".join(rules))
            return

        top = max(top, 5)

        for keystroke in keys:
            label = self.key_widgets.get(keystroke.scan_code)
            if not label:
                continue
            css_class = f"scancode-{keystroke.scan_code}"
            normalized = min(keystroke.count / top, 1.0)
            bg, fg = self._calculate_color(normalized)
            rules.append(
                f"""
            .{css_class} {{
              background-color: {bg};
              color: {fg};
            }}""",
            )
            label.set_css_classes([css_class])
            label.set_tooltip_text(str(keystroke.count))

        self.css_provider.load_from_string("\n".join(rules))

    def _calculate_color(self, normalized: float) -> tuple[str, str]:
        r = self.beg_color[0] + normalized * (self.end_color[0] - self.beg_color[0])
        g = self.beg_color[1] + normalized * (self.end_color[1] - self.beg_color[1])
        b = self.beg_color[2] + normalized * (self.end_color[2] - self.beg_color[2])
        r_i, g_i, b_i = int(r * 255), int(g * 255), int(b * 255)
        bg = f"rgb({r_i},{g_i},{b_i})"
        lum = 0.3 * r + 0.6 * g + 0.1 * b
        fg = "white" if lum < self.LUMINANCE_THRESHOLD else "black"
        return bg, fg

    def _on_zoom_clicked(self, amount: int) -> None:
        new_size = max(self.settings.get_int("key-size") + amount, 40)
        self.settings.set_int("key-size", new_size)
        for label in self.key_widgets.values():
            label.set_size_request(new_size, new_size)

    def on_new_keystroke(self) -> None:
        """Update heatmap when a new keystroke is received."""
        GLib.idle_add(self.update)
