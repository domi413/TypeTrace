"""Used to setup dbus connection."""

from __future__ import annotations

import logging
import signal
from typing import Callable

from gi.repository import Gio, GLib

from typetrace.config import Config, ExitCodes

logger = logging.getLogger(__name__)

class DbusServiceManager:
    """Manages the D-Bus service lifecycle for the TypeTrace backend."""

    def __init__(self, stop_callback: Callable[[], None] | None = None) -> None:
        """Initialize the D-Bus Service Manager.

        Args:
            stop_callback: A function to call when a shutdown is requested
                           (e.g., via D-Bus Quit or OS signal).

        """
        self._stop_callback = stop_callback
        self._owner_id = 0
        self._mainloop = GLib.MainLoop()
        self._connection: Gio.DBusConnection | None = None
        self._registration_id: int | None = None

        # Define the D-Bus interface XML
        self._dbus_interface_xml = f"""
        <!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
        "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
        <node>
          <interface name='{Config.BACKEND_DBUS_INTERFACE}'>
            <method name='ping'>
              <arg type='s' name='response' direction='out'/>
            </method>
            <method name='quit'/>
            <signal name='db_updated'>
            </signal>
          </interface>
          <interface name='org.freedesktop.DBus.Introspectable'>
            <method name='introspect'>
              <arg name='xml_data' type='s' direction='out'/>
            </method>
          </interface>
          <interface name='org.freedesktop.DBus.Properties'>
          </interface>
        </node>
        """

    # --- D-Bus Method Implementations ---
    def ping(self, invocation: Gio.DBusMethodInvocation) -> None:
        """Handle the ping D-Bus method call."""
        logger.debug("Received ping request")
        invocation.return_value(GLib.Variant("(s)", ("pong",)))

    def quit(self, invocation: Gio.DBusMethodInvocation) -> None:
        """Handle the quit D-Bus method call."""
        logger.debug("Received quit request via D-Bus")
        invocation.return_value(None)
        self._trigger_shutdown()

    # --- Standard D-Bus Interface Implementations ---
    def introspect(self, invocation: Gio.DBusMethodInvocation) -> None:
        """Handle the Introspect D-Bus method call."""
        invocation.return_value(GLib.Variant("(s)", (self._dbus_interface_xml,)))

    # --- D-Bus Signal Emission ---
    def emit_db_updated(self) -> None:
        """Emit the db_updated signal to notify clients of a database update."""
        if self._connection is None:
            logger.warning("Cannot emit db_updated signal: No D-Bus connection")
            return
        try:
            self._connection.emit_signal(
                None,  # Destination bus name (None for broadcast)
                Config.BACKEND_DBUS_PATH,
                Config.BACKEND_DBUS_INTERFACE,
                "db_updated",
                None,
            )
            logger.debug("Emitted db_updated signal")
        except Exception:
            logger.exception("Failed to emit db_updated signal")

    # --- D-Bus Service Management ---
    def _on_bus_acquired(self, connection: Gio.DBusConnection, name: str) -> None:
        """Call when the D-Bus connection is acquired."""
        logger.debug("D-Bus connection acquired for '%s'", name)
        self._connection = connection
        interface_info = Gio.DBusNodeInfo.new_for_xml(
            self._dbus_interface_xml,
        ).interfaces[0]

        # Map D-Bus methods to Python methods
        method_map = {
            "ping": self.ping,
            "quit": self.quit,
            "introspect": self.introspect,
        }

        def method_call_handler(
            _conn: Gio.DBusConnection,
            _sender: str,
            _obj_path: str,
            _iface_name: str,
            method_name: str,
            _params: GLib.Variant,
            inv: Gio.DBusMethodInvocation,
        ) -> None:
            if method_name in method_map:
                method_map[method_name](inv)
            else:
                logger.warning("Received unknown D-Bus method call: %s", method_name)
                inv.return_error_literal(
                    Gio.DBusError,
                    Gio.DBusError.UNKNOWN_METHOD,
                    f"Unknown method {method_name}",
                )

        try:
            self._registration_id = connection.register_object(
                object_path=Config.BACKEND_DBUS_PATH,
                interface_info=interface_info,
                method_call_closure=method_call_handler,
            )
            logger.debug("D-Bus object exported at %s", Config.BACKEND_DBUS_PATH)
        except GLib.Error:
            logger.exception("Failed to register D-Bus object")
            self._mainloop.quit()

    def _on_name_acquired(self, _conn: Gio.DBusConnection, name: str) -> None:
        """Call when the D-Bus name is successfully acquired."""
        logger.debug("Acquired D-Bus name: %s", name)

    def _on_name_lost(self, _conn: Gio.DBusConnection | None, name: str) -> None:
        """Call when the D-Bus name is lost."""
        logger.warning("Lost D-Bus name: %s. Shutting down.", name)
        self._cleanup_dbus()
        self._trigger_shutdown(from_dbus_lost=True)

    def _trigger_shutdown(self, *, from_dbus_lost: bool = False) -> None:
        """Initiate the shutdown sequence."""
        logger.debug("Shutdown triggered.")
        if self._stop_callback:
            try:
                self._stop_callback()
            except Exception:
                logger.exception("Error in stop_callback")

        # Quit the main loop if it's running
        if self._mainloop.is_running():
            logger.debug("Quitting GLib MainLoop.")
            self._mainloop.quit()
        else:
            logger.debug("GLib MainLoop was not running.")

        if not from_dbus_lost:
            self._cleanup_dbus()

    def _cleanup_dbus(self) -> None:
        """Unregister object and release name ownership."""
        if self._registration_id is not None and self._connection:
            logger.debug("Unregistering D-Bus object ID: %s", self._registration_id)
            if not self._connection.unregister_object(self._registration_id):
                logger.warning("Failed to unregister D-Bus object.")
            self._registration_id = None
        if self._owner_id:
            logger.debug("Releasing D-Bus name ownership ID: %s", self._owner_id)
            Gio.bus_unown_name(self._owner_id)
            self._owner_id = 0
        self._connection = None

    def run(self) -> int:
        """Acquires the D-Bus name and runs the GLib MainLoop.

        Returns:
            Exit code (0 for success, 1 for D-Bus error).

        """
        self._owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            Config.BACKEND_DBUS_NAME,
            Gio.BusNameOwnerFlags.NONE, # flags
            self._on_bus_acquired,
            self._on_name_acquired,
            self._on_name_lost,
        )

        if self._owner_id == 0:
            logger.error("Failed to acquire D-Bus name ownership immediately.")
            return ExitCodes.RUNTIME_ERROR

        # Handle signals gracefully
        # GLib can integrate signal handling into the main loop
        GLib.unix_signal_add(
            GLib.PRIORITY_HIGH,
            signal.SIGINT,
            self._handle_signal,
            signal.SIGINT,
        )
        GLib.unix_signal_add(
            GLib.PRIORITY_HIGH,
            signal.SIGTERM,
            self._handle_signal,
            signal.SIGTERM,
        )

        logger.debug("Starting GLib MainLoop for D-Bus service...")
        try:
            self._mainloop.run()
            logger.debug("GLib MainLoop finished.")
            exit_code = 0
        except KeyboardInterrupt:
            logger.debug("KeyboardInterrupt caught, initiating shutdown.")
            self._trigger_shutdown()
            exit_code = 0  # Normal exit on Ctrl+C
        except Exception:
            logger.exception("Error during main loop execution.")
            self._trigger_shutdown()
            exit_code = 1  # Indicate error
        finally:
            # Ensure cleanup happens even if loop exits unexpectedly
            self._cleanup_dbus()

        logger.debug("D-Bus service manager finished running.")
        return exit_code

    def _handle_signal(self, signum: str) -> bool:
        """Signal handler integrated with GLib main loop."""
        logger.debug("Received signal %s, initiating shutdown.", signum)
        self._trigger_shutdown()
        # Returning False removes the signal handler after first invocation
        # Returning True keeps it active (usually want False for exit signals)
        return False  # Or GLib.SOURCE_REMOVE

    def stop(self) -> None:
        """Public method to stop the service from outside."""
        logger.debug("External stop requested.")
        GLib.idle_add(self._trigger_shutdown)
