# Incomplete testing
"""The heatmap widget that displays a keyboard."""

from typing import ClassVar

from gi.repository import Gdk, Gtk

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
        beg_color: tuple[float, float, float] = (0.0, 0.0, 1.0),
        end_color: tuple[float, float, float] = (1.0, 0.0, 0.0),
    ) -> None:
        """Initialize the heatmap widget.

        Args:
            keystroke_store: Access to keystrokes.
            layout: Keyboard layout to use.
            beg_color: RGB tuple (0.0 to 1.0) for the lowest frequency.
            end_color: RGB tuple (0.0 to 1.0) for the highest frequency.

        """
        super().__init__()
        self.keystroke_store: KeystrokeStore = keystroke_store
        self.layout = layout
        self.beg_color = beg_color
        self.end_color = end_color
        self.key_widgets: dict[int, Gtk.Label] = {}

        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.refresh_button.connect("clicked", lambda *_: self._update_colors())

        self._build_keyboard()
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
