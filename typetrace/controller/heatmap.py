"""The heatmap widget that displays a keyboard."""

import platform
import re
import subprocess
from typing import ClassVar

from gi.repository import Gtk

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

    keyboard_container = Gtk.Template.Child("keyboard_container")

    def __init__(
        self,
        keystroke_store: KeystrokeStore,
        **kwargs,
    ) -> None:
        """Initialize the heatmap widget.

        Args:
            keystroke_store: Access to keystrokes
            layout: Keyboard layout to use
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store: KeystrokeStore = keystroke_store
        self.layout = self._get_keyboard_layout()
        self.key_widgets: dict[int, Gtk.Label] = {}

        self._build_keyboard()
        self._update_colors()

    def _get_keyboard_layout(self) -> str:
        """Determine the current keyboard layout of the system.

        On Linux, checks /etc/vconsole.conf for KEYMAP
        On Windows and macOS, does nothing yet

        Returns:
            str: The detected keyboard layout or "en_US" as default.

        """
        match platform.system().lower():
            case "linux":
                try:
                    result = subprocess.run(
                        ["grep", "^KEYMAP=", "/etc/vconsole.conf"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode == 0:
                        # Extract keymap value using regex
                        match = re.search(r'^KEYMAP="?([^"]*)"?', result.stdout.strip())
                        if match:
                            keymap = match.group(1)

                            for layout in KEYBOARD_LAYOUTS:
                                if keymap == layout or keymap.startswith(
                                    f"{layout}-",
                                ):
                                    return layout

                except Exception:
                    print("Error detecting keyboard layout")

            case "windows":
                pass

            case "darwin":
                pass

        return "en_US"

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

        for keystroke in keystrokes:
            if label := self.key_widgets.get(keystroke.scan_code):
                percentil = round((keystroke.count / most_pressed) * 10) * 10
                self._get_key_color(label, percentil)
                label.set_tooltip_text(str(keystroke.count))

    def _get_key_color(
        self,
        label: Gtk.Label,
        percentile: int,
    ) -> None:
        """Assign color class based on percentile (rounded to 10s)."""
        style_context = label.get_style_context()

        for i in range(10, 101, 10):
            style_context.remove_class(f"usage-{i}")

        class_name = f"usage-{percentile}"
        style_context.add_class(class_name)
