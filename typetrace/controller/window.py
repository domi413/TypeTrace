"""Window module for the Typetrace application."""

from gi.repository import Adw, Gio, Gtk

from typetrace.controller.heatmap import Heatmap
from typetrace.controller.statistics import Statistics
from typetrace.controller.verbose import Verbose
from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window class for Typetrace.

    Provides the user interface for the application.
    """

    __gtype_name__ = "TypetraceWindow"

    refresh_button = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(
        self,
        keystroke_store: KeystrokeStore,
        settings: Gio.Settings,
        **kwargs,
    ) -> None:
        """Initialize the application window.

        Args:
            **kwargs: Keyword arguments passed to the parent constructor
            keystroke_store: Access to keystrokes
            settings: GSettings used to persist preferences of a user

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store
        self.heatmap = Heatmap(keystroke_store=keystroke_store, settings=settings)
        self.verbose = Verbose(keystroke_store=keystroke_store)
        self.statistics = Statistics(keystroke_store=keystroke_store)
        self.refresh_button.connect("clicked", lambda *_: self._on_refresh_clicked())

        heatmap_page = self.stack.add_titled(
            self.heatmap,
            "heatmap",
            "Heatmap",
        )
        heatmap_page.set_icon_name("input-keyboard-symbolic")
        verbose_page = self.stack.add_titled(
            self.verbose,
            "verbose",
            "Verbose",
        )
        verbose_page.set_icon_name("view-list-symbolic")
        statistics_page = self.stack.add_titled(
            self.statistics,
            "statistics",
            "Statistics",
        )
        statistics_page.set_icon_name("image-filter-symbolic")
        self.view_switcher.set_stack(self.stack)

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        keystrokes = self.keystroke_store.get_all_keystrokes()
        self.heatmap.update(keystrokes)
        self.verbose.update(keystrokes)
        self.statistics.update()
