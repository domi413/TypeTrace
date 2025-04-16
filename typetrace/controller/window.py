"""Window module for the Typetrace application."""

from gi.repository import Adw, Gio, GLib, Gtk

from typetrace.controller.heatmap import Heatmap
from typetrace.controller.utils import dialog_utils
from typetrace.controller.verbose import Verbose
from typetrace.model.keystrokes import KeystrokeStore
from typetrace.service.backend_connector import BackendConnector


@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window class for Typetrace.

    Provides the user interface for the application.
    """

    __gtype_name__ = "TypetraceWindow"

    toast_overlay = Gtk.Template.Child()

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
        self._backend_connector = BackendConnector()
        self._backend_connector.connect("backend-available", self._on_available)
        self._backend_connector.connect("backend-unavailable", self._on_unavailable)

        self.refresh_button.connect("clicked", lambda *_: self._on_refresh_clicked())
        self.refresh_button.set_sensitive(False)

        self.heatmap = Heatmap(keystroke_store=keystroke_store, settings=settings)
        self.verbose = Verbose(keystroke_store=keystroke_store)

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
        verbose_page.set_icon_name("text-x-generic-symbolic")
        self.view_switcher.set_stack(self.stack)

        GLib.idle_add(self._backend_connector.check_and_activate_async)

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        self.heatmap.update()
        self.verbose.update()

    # --- Signal Handlers for BackendConnector ---

    def _on_available(self, _: any) -> None:
        """Call when the backend becomes available."""
        dialog_utils.show_toast(self.toast_overlay, "Backend service connected.")
        self.refresh_button.set_sensitive(True)

    def _on_unavailable(self, _: any, reason: str) -> None:
        """Call when the backend becomes unavailable."""
        dialog_utils.show_toast(
            self.toast_overlay,
            f"Backend service disconnected: {reason}",
        )
        self.refresh_button.set_sensitive(False)

    # --- Window Lifecycle ---

    def do_close_request(self) -> bool:
        """Handle window close request."""
        # Tell the connector to clean up
        self._backend_connector.shutdown()
        return super().do_close_request()
