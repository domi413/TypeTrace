from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar
from gi.repository import Gdk, Gio, Gtk

from typetrace.controller.utils.color_utils import get_color_scheme
from typetrace.model.layouts import KEYBOARD_LAYOUTS
from gi.repository import GLib

if TYPE_CHECKING:
    from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/heatmap.ui")
class Heatmap(Gtk.Box):
    """The heatmap widget that displays a keyboard."""

    __gtype_name__ = "Heatmap"

    EXPANDED_KEYS: ClassVar[list[str]] = [
        "Backspace", "Tab", "Caps", "Enter", "Shift", "Space", "\\"
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
        self.keystroke_store = keystroke_store
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

        for setting in [
            "heatmap-begin-color",
            "heatmap-end-color",
            "heatmap-single-color",
            "use-single-color-heatmap",
            "reverse-heatmap-gradient",
            "use-accent-color",
        ]:
            self.settings.connect(
                f"changed::{setting}",
                lambda *_: self._update_colors(),
            )

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
        """Assign each displayed key the appropriate color."""
        keystrokes = self.keystroke_store.get_all_keystrokes()
        most_pressed = self.keystroke_store.get_highest_count() or 1

        color_scheme = get_color_scheme(self.settings)

        gradient_css = color_scheme.get_gradient_css()

        css_rules = [gradient_css]

        # Clear all tooltips
        for label in self.key_widgets.values():
            label.set_tooltip_text(None)

        for keystroke in keystrokes:
            if label := self.key_widgets.get(keystroke.scan_code):
                css_class = f"scancode-{keystroke.scan_code}"
                normalized_count = keystroke.count / most_pressed
                bg_color, text_color = color_scheme.calculate_color_for_key(
                    normalized_count,
                )

                css_rules.append(
                    f"""
                   .{css_class} {{
                        background-color: {bg_color};
                        color: {text_color};
                    }}
                    """,
                )
                label.set_css_classes([css_class])
                label.set_tooltip_text("0")

        if top == 0:
            self.css_provider.load_from_string("\n".join(rules))
            return

        # Verwende eine Mindestschwelle für top
        top = max(top, 5)

        for keystroke in keys:
            label = self.key_widgets.get(keystroke.scan_code)
            if not label:
                continue
            css_class = f"scancode-{keystroke.scan_code}"
            normalized = min(keystroke.count / top, 1.0)
            bg, fg = self._calculate_color(normalized)
            rules.append(f"""
            .{css_class} {{
              background-color: {bg};
              color: {fg};
            }}""")
            label.set_css_classes([css_class])
            label.set_tooltip_text(str(keystroke.count))

        self.css_provider.load_from_string("\n".join(rules))

    def _on_zoom_clicked(self, amount: int) -> None:
        new_size = max(self.settings.get_int("key-size") + amount, 40)
        self.settings.set_int("key-size", new_size)
        for label in self.key_widgets.values():
            label.set_size_request(new_size, new_size)

    def on_new_keystroke(self, keystroke):
        """Update heatmap when a new keystroke is received."""
        GLib.idle_add(self.update)

