"""Establishes dbus connection to backend service."""

from __future__ import annotations

import contextlib
import logging
from typing import Callable, ClassVar

from gi.repository import Gio, GLib, GObject

from typetrace.config import Config

logger = logging.getLogger(__name__)


class BackendConnector(GObject.Object):
    """Manages the connection and communication with the backend D-Bus service.

    Emits signals 'backend-available' and 'backend-unavailable'.
    """

    __gsignals__: ClassVar[dict] = {
        "backend-available": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "backend-unavailable": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "db-updated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self) -> None:
        """Initialize the BackendConnector."""
        logger.debug("Initializing BackendConnector")
        super().__init__()
        self._proxy: Gio.DBusProxy | None = None
        self._proxy_signal_handlers = []
        self._cancellable = Gio.Cancellable()  # To cancel ongoing async operations
        self._is_available = False  # Cache the last known status

    def check_and_activate_async(self) -> None:
        """Asynchronously attempts to connect to and activate the backend service.

        Emits 'backend-available' or 'backend-unavailable' on completion.
        """
        logger.debug("Starting async check and activation of backend service")
        if self._proxy:
            logger.debug("Existing proxy found, checking name owner")
            if self._proxy.get_name_owner():
                logger.debug("Proxy has valid owner, setting availability to True")
                self._set_availability(available=True)
            else:
                logger.debug("Proxy is stale, cleaning up")
                self._cleanup_proxy()
                self._set_availability("Connection lost", available=False)
            if self._is_available:
                logger.debug("Backend already available, skipping proxy creation")
                return

        logger.debug(
            "Creating new D-Bus proxy for backend: %s",
            Config.BACKEND_DBUS_NAME,
        )
        try:
            Gio.DBusProxy.new_for_bus(
                bus_type=Gio.BusType.SESSION,
                flags=Gio.DBusProxyFlags.NONE,
                info=None,
                name=Config.BACKEND_DBUS_NAME,
                object_path=Config.BACKEND_DBUS_PATH,
                interface_name=Config.BACKEND_DBUS_INTERFACE,
                cancellable=self._cancellable,
                callback=self._on_proxy_created,
                user_data=None,
            )
            logger.debug("Async D-Bus proxy creation initiated")
        except Exception:
            logger.exception("Failed to initiate D-Bus proxy creation")
            self._set_availability("Failed to initiate proxy creation", available=False)

    def _on_proxy_created(
        self,
        _source_object: Gio.DBusProxy | None,
        res: Gio.AsyncResult,
        _user_data: None,
    ) -> None:
        """Use callback for async D-Bus proxy creation."""
        logger.debug("Handling async D-Bus proxy creation callback")
        try:
            proxy = Gio.DBusProxy.new_for_bus_finish(res)
            self._proxy = proxy
            logger.debug("D-Bus proxy created successfully")
            self._connect_proxy_signals()
            logger.debug("Initiating async ping to verify backend responsiveness")
            self.ping_async(self._on_initial_ping_result)
        except GLib.Error as e:
            logger.exception("Failed to create D-Bus proxy: %s", e.message)
            self._proxy = None
            self._set_availability(f"Connection failed: {e.message}", available=False)

    def _connect_proxy_signals(self) -> None:
        """Connect to signals on the valid D-Bus proxy."""
        logger.debug("Connecting proxy signals")
        if not self._proxy:
            logger.debug("No proxy available, skipping signal connection")
            return
        # Disconnect any previous handlers first
        self._disconnect_proxy_signals()
        # Connect new handlers
        try:
            handler_id = self._proxy.connect("g-signal", self._on_backend_signal)
            self._proxy_signal_handlers.append(handler_id)
            logger.debug("Connected g-signal handler: %s", handler_id)
            handler_id = self._proxy.connect(
                "notify::g-name-owner",
                self._on_backend_owner_changed,
            )
            self._proxy_signal_handlers.append(handler_id)
            logger.debug("Connected g-name-owner handler: %s", handler_id)
        except Exception:
            logger.exception("Failed to connect proxy signals")
            self._cleanup_proxy()
            self._set_availability("Failed to connect signals", available=False)

    def _disconnect_proxy_signals(self) -> None:
        """Disconnects signals previously connected to the proxy."""
        logger.debug("Disconnecting proxy signals")
        if self._proxy and self._proxy_signal_handlers:
            for handler_id in self._proxy_signal_handlers:
                with contextlib.suppress(TypeError):
                    # Can happen if proxy became invalid
                    logger.debug("Disconnecting signal handler: %s", handler_id)
                    self._proxy.disconnect(handler_id)
            self._proxy_signal_handlers = []
            logger.debug("All proxy signal handlers disconnected")

    def _cleanup_proxy(self) -> None:
        """Disconnects signals and releases the proxy object."""
        if self._proxy:
            logger.debug("Cleaning up proxy")
            self._disconnect_proxy_signals()
            self._proxy = None
            logger.debug("Proxy released")

    def _on_backend_signal(
        self,
        _proxy: Gio.DBusProxy,
        _sender_name: str,
        signal_name: str,
        _parameters: GLib.Variant,
    ) -> None:
        """Handle signals emitted by the backend service itself."""
        logger.debug("Received backend signal: %s", signal_name)
        if signal_name == "db_updated":
            logger.debug("Emitting db-updated signal")
            self.emit("db-updated")

    def _on_backend_owner_changed(
        self,
        _proxy: Gio.DBusProxy,
        _pspec: GObject.ParamSpec,
    ) -> None:
        """Handle notification when the D-Bus name owner changes."""
        logger.debug("Backend owner changed notification received")
        if not self._proxy:
            logger.debug("No proxy available, ignoring owner change")
            return

        owner = self._proxy.get_name_owner()
        if owner:
            # Might have become available again after a restart
            logger.debug("Backend owner present: %s", owner)
            if not self._is_available:
                logger.debug("Initiating async ping to verify reconnect")
                self.ping_async(self._on_reconnect_ping_result)
        else:
            logger.debug("No backend owner, cleaning up proxy")
            self._cleanup_proxy()
            self._set_availability("Service stopped or crashed", available=False)

    def _set_availability(self, reason: str = "", *, available: bool) -> None:
        """Update availability status and emits the appropriate signal."""
        logger.debug(
            "Setting backend availability to %s, reason: %s",
            available,
            reason or "none",
        )
        if available != self._is_available:
            self._is_available = available
            if available:
                logger.debug("Emitting backend-available signal")
                self.emit("backend-available")
            else:
                logger.debug(
                    "Emitting backend-unavailable signal with reason: %s",
                    reason,
                )
                self.emit("backend-unavailable", reason or "Reason unknown")
        elif available:
            logger.debug("Backend remains available, no signal emitted")

    def ping_async(self, callback: Callable[[bool, str], None] | None = None) -> None:
        """Asynchronously pings the backend.

        Args:
            callback: Optional function to call with result (bool: success, str: error)

        """
        logger.debug("Initiating async ping to backend")
        if not self._proxy:
            logger.debug("No proxy available for ping")
            if callback:
                callback("No connection")
            return

        try:
            self._proxy.call(
                "ping",
                None,
                Gio.DBusCallFlags.NONE,
                500,  # Timeout 500ms
                self._cancellable,
                self._on_ping_response,
                callback,  # Pass the original callback as user_data
            )
            logger.debug("Async ping call initiated")
        except Exception:
            logger.exception("Failed to initiate ping call")
            if callback:
                callback("Failed to initiate ping")
            self._cleanup_proxy()
            self._set_availability("Ping initiation failed", available=False)

    def _on_ping_response(
        self,
        source_object: Gio.DBusProxy,
        res: Gio.AsyncResult,
        user_data: None,
    ) -> None:
        """Use callback for the async ping response."""
        logger.debug("Handling async ping response")
        original_callback = user_data
        error_msg = ""
        try:
            result = source_object.call_finish(res)
            if result:
                logger.debug("Ping successful, setting availability to True")
                self._set_availability(available=True)
            else:
                error_msg = "Ping returned no result"
                logger.debug("Ping failed: %s", error_msg)
                self._set_availability(error_msg, available=False)
        except GLib.Error as e:
            error_msg = e.message
            logger.exception("Ping failed: %s", error_msg)
            self._cleanup_proxy()
            self._set_availability(f"Ping failed: {error_msg}", available=False)

        if original_callback:
            logger.debug(
                "Calling ping callback with error message: %s",
                error_msg or "none",
            )
            original_callback(error_msg)

    # --- Callbacks passed to ping_async ---
    def _on_initial_ping_result(self, error_msg: str) -> None:
        """Handle result of ping right after proxy creation."""
        logger.debug("Handling initial ping result")
        if not error_msg:
            logger.debug("Initial ping successful")
            self._set_availability(available=True)
        else:
            logger.debug("Initial ping failed")

    def _on_reconnect_ping_result(self, error_msg: str) -> None:
        """Handle result of ping after owner reappeared."""
        logger.debug("Handling reconnect ping result, error: %s", error_msg or "none")
        if not error_msg:
            logger.debug("Reconnect ping successful, setting availability to True")
            self._set_availability(available=True)
        else:
            logger.debug(
                "Reconnect ping failed: %s, retaining current availability",
                error_msg,
            )

    def request_quit_async(self) -> None:
        """Asynchronously sends the Quit signal to the backend."""
        logger.debug("Initiating async quit request to backend")
        if not self._proxy:
            logger.debug("No proxy available, skipping quit request")
            return

        try:
            self._proxy.call(
                "quit",
                None,
                Gio.DBusCallFlags.NO_AUTO_START,  # Don't restart
                500,  # Timeout
                self._cancellable,
                self._on_quit_response,
                None,
            )
            logger.debug("Async quit call initiated")
        except Exception:
            logger.exception("Failed to initiate quit call")
            self._cleanup_proxy()
            self._set_availability("Quit initiation failed", available=False)

    def _on_quit_response(
        self,
        source_object: Gio.DBusProxy,
        res: Gio.AsyncResult,
        _user_data: None,
    ) -> None:
        """Use callback for the async quit response."""
        logger.debug("Handling async quit response")
        try:
            source_object.call_finish(res)
            logger.debug("Quit call completed successfully")
        except GLib.Error:
            logger.debug("Quit call failed, likely backend already terminated")
        finally:
            logger.debug("Cleaning up proxy after quit request")
            self._cleanup_proxy()
            self._set_availability("Quit requested", available=False)

    def shutdown(self) -> None:
        """Cancel ongoing operations and cleans up."""
        logger.debug("Shutting down BackendConnector")
        self._cancellable.cancel()
        self._cleanup_proxy()
        logger.debug("BackendConnector shutdown completed")
