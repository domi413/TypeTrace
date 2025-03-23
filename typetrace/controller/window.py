"""Window module for the Typetrace application."""

from gi.repository import Adw, Gtk

from typetrace.model.keystrokes import KeystrokeStore

from .heatmap import Heatmap
from .verbose import Verbose


@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window class for Typetrace.

    Provides the user interface for the application.
    """

    __gtype_name__ = "TypetraceWindow"

    view_switcher = Gtk.Template.Child("view_switcher")
    stack = Gtk.Template.Child("stack")

    def __init__(self, **kwargs) -> None:
        """Initialize the application window.

        Args:
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store = KeystrokeStore()
        heatmap_page = self.stack.add_titled(
            Heatmap(keystroke_store=self.keystroke_store),
            "heatmap",
            "Heatmap",
        )
        heatmap_page.set_icon_name("input-keyboard-symbolic")
        verbose_page = self.stack.add_titled(
            Verbose(keystroke_store=self.keystroke_store),
            "verbose",
            "Verbose",
        )
        verbose_page.set_icon_name("text-x-generic-symbolic")
        self.view_switcher.set_stack(self.stack)
