"""Window module for the Typetrace application."""

import logging
import threading

from gi.repository import Adw, Gio, GLib, Gtk

from typetrace.backend.ipc.linux_darwin import LinuxMacOSIPC
from typetrace.controller.heatmap import Heatmap
from typetrace.controller.statistics import Statistics
from typetrace.controller.verbose import Verbose
from typetrace.model.keystrokes import KeystrokeStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window for the Typetrace application."""

    __gtype_name__ = "TypetraceWindow"

    refresh_button = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(
    self: "TypetraceWindow",
    keystroke_store: KeystrokeStore,
    settings: Gio.Settings,
    **kwargs: any,
    ) -> None:
        """Initialize the TypetraceWindow.

        Args:
        ----
            keystroke_store: The store containing keystroke data.
            settings: The GSettings object for storing application settings.
            **kwargs: Additional arguments passed to the parent class.

        """
        super().__init__(**kwargs)

        # Start backend
        logger.info("Starting backend...")
        self.backend = LinuxMacOSIPC()
        self.backend.register_callback(self._on_keystroke_received)
        self.backend_thread = threading.Thread(
            target=self.backend.run,
            daemon=True,
        )
        self.backend_thread.start()
        logger.info("Backend thread started")

        # Initialize views
        self.heatmap = Heatmap(settings=settings, keystroke_store=keystroke_store)
        self.verbose = Verbose(keystroke_store=keystroke_store)
        self.statistics = Statistics(keystroke_store=keystroke_store)
        self.refresh_button.connect("clicked", lambda *_: self._on_refresh_clicked())

        # Add tabs to the ViewStack
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

    def _on_refresh_clicked(self: "TypetraceWindow") -> None:
        """Handle refresh button click."""
        self.heatmap.update()
        self.verbose.update()
        self.statistics.update()

    def _on_keystroke_received(self: "TypetraceWindow", event: dict) -> None:
        """Handle new keystrokes from the backend."""
        logger.debug("Received event: %s", event)
        self.heatmap.keystroke_store.add(event)
        GLib.idle_add(self.heatmap.update)
        GLib.idle_add(self.verbose.update)
