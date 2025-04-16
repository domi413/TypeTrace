"""Apples."""

from __future__ import annotations

import logging
import signal
from typing import Callable, Optional

from gi.repository import Gio, GLib

logger = logging.getLogger(__name__)

# Define D-Bus details (ensure these match your .service file and frontend)
BACKEND_DBUS_NAME = "edu.ost.typetrace.backend"
BACKEND_DBUS_PATH = "/edu/ost/typetrace/backend"
BACKEND_DBUS_INTERFACE = "edu.ost.typetrace.backend"


class DbusServiceManager:
    """Manages the D-Bus service lifecycle for the TypeTrace backend."""

    def __init__(self, stop_callback: Callable[[], None] | None = None):
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
          <interface name='{BACKEND_DBUS_INTERFACE}'>
            <method name='Ping'>
              <arg type='s' name='response' direction='out'/>
            </method>
            <method name='Quit'/>
          </interface>
          <interface name='org.freedesktop.DBus.Introspectable'>
            <method name='Introspect'>
              <arg name='xml_data' type='s' direction='out'/>
            </method>
          </interface>
          <interface name='org.freedesktop.DBus.Properties'>
             </interface>
        </node>
        """

    # --- D-Bus Method Implementations ---
    def Ping(self, invocation: Gio.DBusMethodInvocation):
        """Handles the Ping D-Bus method call."""
        logger.debug("Received Ping request")
        invocation.return_value(GLib.Variant("(s)", ("pong",)))

    def Quit(self, invocation: Gio.DBusMethodInvocation):
        """Handles the Quit D-Bus method call."""
        logger.info("Received Quit request via D-Bus")
        invocation.return_value(None)  # Complete the D-Bus call first
        self._trigger_shutdown()

    # --- Standard D-Bus Interface Implementations ---
    def Introspect(self, invocation: Gio.DBusMethodInvocation):
        """Handles the Introspect D-Bus method call."""
        invocation.return_value(GLib.Variant("(s)", (self._dbus_interface_xml,)))

    # --- D-Bus Service Management ---
    def _on_bus_acquired(self, connection: Gio.DBusConnection, name: str):
        """Called when the D-Bus connection is acquired."""
        logger.info(f"D-Bus connection acquired for '{name}'")
        self._connection = connection
        interface_info = Gio.DBusNodeInfo.new_for_xml(
            self._dbus_interface_xml
        ).interfaces[0]

        # Map D-Bus methods to Python methods
        method_map = {
            "Ping": self.Ping,
            "Quit": self.Quit,
            "Introspect": self.Introspect,
            # Add other methods if needed for Properties interface
        }

        def method_call_handler(
            conn, sender, obj_path, iface_name, method_name, params, inv
        ):
            if method_name in method_map:
                method_map[method_name](inv)
            else:
                logger.warning(f"Received unknown D-Bus method call: {method_name}")
                inv.return_error_literal(
                    Gio.DBusError,
                    Gio.DBusError.UNKNOWN_METHOD,
                    f"Unknown method {method_name}",
                )

        try:
            self._registration_id = connection.register_object(
                object_path=BACKEND_DBUS_PATH,
                interface_info=interface_info,
                method_call_closure=method_call_handler,
            )
            logger.info(f"D-Bus object exported successfully at {BACKEND_DBUS_PATH}")
        except GLib.Error as e:
            logger.error(f"Failed to register D-Bus object: {e}", exc_info=True)
            self._mainloop.quit()  # Stop if registration fails

    def _on_name_acquired(self, connection: Gio.DBusConnection, name: str):
        """Called when the D-Bus name is successfully acquired."""
        logger.info(f"Acquired D-Bus name: {name}")

    def _on_name_lost(self, connection: Optional[Gio.DBusConnection], name: str):
        """Called when the D-Bus name is lost."""
        logger.warning(f"Lost D-Bus name: {name}. Shutting down.")
        self._cleanup_dbus()
        self._trigger_shutdown(from_dbus_lost=True)  # Trigger general shutdown

    def _trigger_shutdown(self, from_dbus_lost: bool = False):
        """Initiates the shutdown sequence."""
        logger.debug("Shutdown triggered.")
        # Call the provided callback first to signal other parts (like CLI)
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

        # If shutdown wasn't triggered by name loss, try to clean up D-Bus resources
        if not from_dbus_lost:
            self._cleanup_dbus()

    def _cleanup_dbus(self):
        """Unregister object and release name ownership."""
        if self._registration_id is not None and self._connection:
            logger.debug(f"Unregistering D-Bus object ID: {self._registration_id}")
            if not self._connection.unregister_object(self._registration_id):
                logger.warning("Failed to unregister D-Bus object.")
            self._registration_id = None
        if self._owner_id:
            logger.debug(f"Releasing D-Bus name ownership ID: {self._owner_id}")
            Gio.bus_unown_name(self._owner_id)
            self._owner_id = 0
        self._connection = None

    def run(self) -> int:
        """Acquires the D-Bus name and runs the GLib MainLoop.

        Returns:
            Exit code (0 for success, 1 for D-Bus error).

        """
        self._owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION,  # bus_type
            BACKEND_DBUS_NAME,  # name
            Gio.BusNameOwnerFlags.NONE,  # flags
            self._on_bus_acquired,  # bus_acquired_handler (positional)
            self._on_name_acquired,  # name_acquired_handler (positional)
            self._on_name_lost,  # name_lost_handler (positional)
        )

        if self._owner_id == 0:
            logger.error("Failed to acquire D-Bus name ownership immediately.")
            return 1  # Indicate D-Bus setup failure

        # Handle signals gracefully
        # GLib can integrate signal handling into the main loop
        GLib.unix_signal_add(
            GLib.PRIORITY_HIGH, signal.SIGINT, self._handle_signal, signal.SIGINT
        )
        GLib.unix_signal_add(
            GLib.PRIORITY_HIGH, signal.SIGTERM, self._handle_signal, signal.SIGTERM
        )

        logger.info("Starting GLib MainLoop for D-Bus service...")
        try:
            self._mainloop.run()
            logger.info("GLib MainLoop finished.")
            exit_code = 0
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught, initiating shutdown.")
            self._trigger_shutdown()
            exit_code = 0  # Normal exit on Ctrl+C
        except Exception:
            logger.exception("Error during main loop execution.")
            self._trigger_shutdown()
            exit_code = 1  # Indicate error
        finally:
            # Ensure cleanup happens even if loop exits unexpectedly
            self._cleanup_dbus()

        logger.info("D-Bus service manager finished running.")
        return exit_code

    def _handle_signal(self, signum) -> bool:
        """Signal handler integrated with GLib main loop."""
        logger.info(f"Received signal {signum}, initiating shutdown.")
        self._trigger_shutdown()
        # Returning False removes the signal handler after first invocation
        # Returning True keeps it active (usually want False for exit signals)
        return False  # Or GLib.SOURCE_REMOVE

    def stop(self):
        """Public method to stop the service from outside."""
        logger.info("External stop requested.")
        # Ensure this runs in the main loop's thread context if necessary
        # Using GLib.idle_add ensures it runs in the main loop thread
        GLib.idle_add(self._trigger_shutdown)
