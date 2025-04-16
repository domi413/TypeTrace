"""Nah."""

from __future__ import annotations

import contextlib
from typing import Callable

from gi.repository import Gio, GLib, GObject

# Define D-Bus details (ensure these match backend/dbus_service.py and the .service file)
BACKEND_DBUS_NAME = "edu.ost.typetrace.backend"
BACKEND_DBUS_PATH = "/edu/ost/typetrace/backend"
BACKEND_DBUS_INTERFACE = "edu.ost.typetrace.backend"


class BackendConnector(GObject.Object):
    """Manages the connection and communication with the backend D-Bus service.

    Emits signals 'backend-available' and 'backend-unavailable'.
    """

    __gsignals__ = {  # noqa: RUF012
        "backend-available": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "backend-unavailable": (GObject.SignalFlags.RUN_FIRST, None, (str,)),  # reason
    }

    def __init__(self) -> None:
        """Initialize the BackendConnector."""
        super().__init__()
        self._proxy: Gio.DBusProxy | None = None
        self._proxy_signal_handlers = []
        self._cancellable = Gio.Cancellable()  # To cancel ongoing async operations
        self._is_available = False  # Cache the last known status

    @property
    def is_available(self) -> bool:
        """Returns the last known availability status of the backend."""
        return self._is_available

    def check_and_activate_async(self) -> None:
        """Asynchronously attempts to connect to and activate the backend service.

        Emits 'backend-available' or 'backend-unavailable' on completion.
        """
        if self._proxy:
            # If proxy exists, verify owner
            if self._proxy.get_name_owner():
                self._set_availability(True)  # Assume available if owner exists
                # Optionally ping async here for certainty
            else:
                # Proxy exists but is stale
                self._cleanup_proxy()
                self._set_availability(False, "Connection lost")
                # Retry getting proxy below
            # If we already determined it's available, no need to recreate proxy
            if self.is_available:
                return

        Gio.DBusProxy.new_for_bus(
            bus_type=Gio.BusType.SESSION,
            flags=Gio.DBusProxyFlags.NONE,
            info=None,
            name=BACKEND_DBUS_NAME,
            object_path=BACKEND_DBUS_PATH,
            interface_name=BACKEND_DBUS_INTERFACE,
            cancellable=self._cancellable,
            callback=self._on_proxy_created,
            user_data=None,
        )

    def _on_proxy_created(self, source_object, res, user_data) -> None:
        """Use callback for async D-Bus proxy creation."""
        try:
            proxy = Gio.DBusProxy.new_for_bus_finish(res)
            self._proxy = proxy
            self._connect_proxy_signals()
            # Ping async to be sure it's truly responsive after creation
            self.ping_async(self._on_initial_ping_result)

        except GLib.Error as e:
            self._proxy = None
            self._set_availability(False, f"Connection failed: {e.message}")

    def _connect_proxy_signals(self) -> None:
        """Connect to signals on the valid D-Bus proxy."""
        if not self._proxy:
            return
        # Disconnect any previous handlers first
        self._disconnect_proxy_signals()
        # Connect new handlers
        handler_id = self._proxy.connect("g-signal", self._on_backend_signal)
        self._proxy_signal_handlers.append(handler_id)
        handler_id = self._proxy.connect(
            "notify::g-name-owner",
            self._on_backend_owner_changed,
        )
        self._proxy_signal_handlers.append(handler_id)

    def _disconnect_proxy_signals(self) -> None:
        """Disconnects signals previously connected to the proxy."""
        if self._proxy and self._proxy_signal_handlers:
            for handler_id in self._proxy_signal_handlers:
                with contextlib.suppress(TypeError):
                    # Can happen if proxy became invalid
                    self._proxy.disconnect(handler_id)
            self._proxy_signal_handlers = []

    def _cleanup_proxy(self) -> None:
        """Disconnects signals and releases the proxy object."""
        self._disconnect_proxy_signals()
        self._proxy = None

    def _on_backend_signal(self, proxy, sender_name, signal_name, parameters) -> None:
        """Handle signals emitted by the backend service itself."""
        # Handle specific signals if the backend emits any useful ones

    def _on_backend_owner_changed(self, proxy, pspec) -> None:
        """Handle notification when the D-Bus name owner changes."""
        if not self._proxy:
            return  # Should not happen if signal is connected

        owner = self._proxy.get_name_owner()
        if owner:
            # Might have become available again after a restart
            if not self._is_available:
                self.ping_async(self._on_reconnect_ping_result)
        else:
            self._cleanup_proxy()
            self._set_availability(False, "Service stopped or crashed")

    def _set_availability(self, available: bool, reason: str = "") -> None:
        """Update availability status and emits the appropriate signal."""
        if available != self._is_available:
            self._is_available = available
            if available:
                self.emit("backend-available")
            else:
                self.emit("backend-unavailable", reason or "Reason unknown")
        elif available:
            # If status is still available, just log confirmation perhaps
            pass

    def ping_async(self, callback: Callable[[bool, str], None] | None = None) -> None:
        """Asynchronously pings the backend.

        Args:
            callback: Optional function to call with result (bool: success, str: error_msg)

        """
        if not self._proxy:
            if callback:
                callback(False, "No connection")
            return

        self._proxy.call(
            "Ping",
            None,  # No arguments
            Gio.DBusCallFlags.NONE,
            500,  # Timeout 500ms
            self._cancellable,
            self._on_ping_response,
            callback,  # Pass the original callback as user_data
        )

    def _on_ping_response(self, source_object, res, user_data) -> None:
        """Use callback for the async ping response."""
        original_callback = user_data
        success = False
        error_msg = ""
        try:
            result = source_object.call_finish(res)
            if result:
                success = True
                # If ping succeeds, confirm availability
                self._set_availability(True)
            else:
                error_msg = "Ping returned no result"
                self._set_availability(False, error_msg)
        except GLib.Error as e:
            error_msg = e.message
            # If ping fails, assume unavailable
            self._cleanup_proxy()  # Ping failure often means proxy is dead
            self._set_availability(False, f"Ping failed: {error_msg}")

        if original_callback:
            original_callback(success, error_msg)

    # --- Callbacks passed to ping_async ---
    def _on_initial_ping_result(self, success: bool, error_msg: str) -> None:
        """Handle result of ping right after proxy creation."""
        if success:
            self._set_availability(True)
        else:
            self._cleanup_proxy()
            self._set_availability(False, f"Initial ping failed: {error_msg}")

    def _on_reconnect_ping_result(self, success: bool, error_msg: str) -> None:
        """Handle result of ping after owner reappeared."""
        if success:
            self._set_availability(True)
        else:
            pass
            # Owner appeared but service isn't responsive? Strange.
            # Don't necessarily set to unavailable yet, maybe transient issue.

    def request_quit_async(self) -> None:
        """Asynchronously sends the Quit signal to the backend."""
        if not self._proxy:
            return

        self._proxy.call(
            "Quit",
            None,
            Gio.DBusCallFlags.NO_AUTO_START,  # Don't restart if it's already stopping
            500,  # Timeout
            self._cancellable,
            self._on_quit_response,
            None,
        )

    def _on_quit_response(self, source_object, res, user_data) -> None:
        """Use callback for the async quit response."""
        try:
            source_object.call_finish(res)
        except GLib.Error:
            # This might happen if backend quits *before* replying, which is fine.
            pass
        finally:
            # Assume backend is gone after requesting quit
            self._cleanup_proxy()
            self._set_availability(False, "Quit requested")

    def shutdown(self) -> None:
        """Cancel ongoing operations and cleans up."""
        self._cancellable.cancel()
        self._cleanup_proxy()
