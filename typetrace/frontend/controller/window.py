"""Window module for the Typetrace application."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gi.repository import Adw, Gio, GLib, Gtk

from typetrace.frontend.controller.heatmap import Heatmap
from typetrace.frontend.controller.statistics import Statistics
from typetrace.frontend.controller.utils import dialog_utils
from typetrace.frontend.controller.verbose import Verbose
from typetrace.frontend.service.backend_connector import BackendConnector

if TYPE_CHECKING:
    from typetrace.frontend.model.db_filehandler import DatabaseFileHandler
    from typetrace.frontend.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window class for Typetrace.

    Provides the user interface for the application.
    """

    __gtype_name__ = "TypetraceWindow"

    toast_overlay = Gtk.Template.Child()

    view_switcher = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    backend_toggle = Gtk.Template.Child()

    def __init__(
        self,
        db_filehandler: DatabaseFileHandler,
        keystroke_store: KeystrokeStore,
        settings: Gio.Settings,
        **kwargs,
    ) -> None:
        """Initialize the application window.

        Args:
            **kwargs: Keyword arguments passed to the parent constructor
            db_filehandler: DB File operations
            keystroke_store: Access to keystrokes
            settings: GSettings used to persist preferences of a user

        """
        super().__init__(**kwargs)
        self._backend_connector = BackendConnector()
        self._backend_connector.connect("backend-available", self._on_available)
        self._backend_connector.connect("backend-unavailable", self._on_unavailable)
        self._backend_connector.connect("db-updated", self._update_view)

        self.backend_toggle.connect("clicked", self._on_backend_label_clicked)
        self.is_backend_running = False

        self.db_manager = db_filehandler
        self.keystroke_store = keystroke_store
        self.heatmap = Heatmap(keystroke_store=keystroke_store, settings=settings)
        self.verbose = Verbose(keystroke_store=keystroke_store)
        self.statistics = Statistics(keystroke_store=keystroke_store)
        self.keystroke_store.connect("changed", self._update_view)
        self.db_manager.connect("changed", self._update_view)

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
        statistics_page.set_icon_name("view-grid-symbolic")
        self.view_switcher.set_stack(self.stack)

        GLib.idle_add(self._backend_connector.check_and_activate_async)

    def _update_view(self, _: Any) -> None:
        """Handle refresh button click."""
        keystrokes = self.keystroke_store.get_all_keystrokes()
        self.heatmap.update(keystrokes)
        self.verbose.update(keystrokes)
        self.statistics.update()

    def _on_available(self, _: Any) -> None:
        """Call when the backend becomes available."""
        dialog_utils.show_toast(self.toast_overlay, "Backend service connected.")
        self.backend_toggle.set_label("Backend running")
        self.backend_toggle.set_css_classes(["backend-status-running", "flat"])
        self.is_backend_running = True

    def _on_unavailable(self, _: Any, reason: str) -> None:
        """Call when the backend becomes unavailable."""
        dialog_utils.show_toast(
            self.toast_overlay,
            f"Backend service disconnected: {reason}",
        )
        self.backend_toggle.set_label("Backend stopped")
        self.backend_toggle.set_css_classes(["backend-status-stopped", "flat"])
        self.is_backend_running = False

    def _on_backend_label_clicked(self, _: Any) -> None:
        """Call when the backend becomes unavailable."""
        if self.is_backend_running:
            GLib.idle_add(self._backend_connector.request_quit_async)
        else:
            GLib.idle_add(self._backend_connector.check_and_activate_async)

    def do_close_request(self) -> bool:
        """Handle window close request."""
        self._backend_connector.shutdown()
        return Adw.ApplicationWindow.do_close_request(self)
