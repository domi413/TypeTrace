"""Helper functions to manage autostart for the TypeTrace application."""

from __future__ import annotations

import logging
from typing import Callable

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from typetrace.config import Config

logger = logging.getLogger(__name__)


def is_autostart_enabled() -> bool:
    """Check if the backend autostart is enabled by checking for the symlink."""
    return Config.AUTOSTART_TARGET_FILE.exists(follow_symlinks=False)


def enable_autostart(
    callback: Callable[[bool, str | None], None] | None = None,
) -> None:
    """Enable autostart using portal for Flatpak or symlink for non-Flatpak."""

    def invoke_callback(error_msg: str | None, *, success: bool) -> None:
        if callback:
            GLib.idle_add(callback, success, error_msg)

    try:
        if Config.IS_FLATPAK:
            DBusGMainLoop(set_as_default=True)

            bus = dbus.SessionBus()

            # Get the Background portal object
            portal = bus.get_object(
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
            )
            interface = dbus.Interface(portal, "org.freedesktop.portal.Background")

            # Use empty window handle for portal request
            window_handle = ""

            options = {
                "handle_token": "typetrace_autostart",
                "reason": "Backend needs to run at startup to monitor typing activity.",
                "autostart": True,
                "background": False,
                "commandline": dbus.Array(
                    ["flatpak", "run", "edu.ost.typetrace", "-b"],
                    signature="s",
                ),
            }

            # Create a request object path
            request_path = interface.RequestBackground(window_handle, options)

            # Get the Request interface for the response
            request = bus.get_object("org.freedesktop.portal.Desktop", request_path)
            req_interface = dbus.Interface(request, "org.freedesktop.portal.Request")

            def handle_response(response: dbus.UInt32, result: dbus.Dictionary) -> None:
                if response == 0:  # Success
                    invoke_callback(None, success=True)
                else:
                    error = f"Portal request denied: {result.get('error', 'Unknown')}"
                    invoke_callback(error, success=False)
                # Disconnect the signal handler to prevent accumulation
                if signal_handler_id[0]:
                    signal_handler_id[0].remove()
                    signal_handler_id[0] = None

            # Store the signal handler ID
            signal_handler_id = [None]  # Mutable list to allow modification in handler
            signal_handler_id[0] = req_interface.connect_to_signal(
                "Response",
                handle_response,
            )

            return

        # Non-Flatpak: Use symlink approach
        Config.AUTOSTART_TARGET_DIR.mkdir(parents=True, exist_ok=True)
        Config.AUTOSTART_TARGET_FILE.symlink_to(Config.AUTOSTART_SOURCE)
        invoke_callback(None, success=True)

    except FileExistsError:
        error_msg = "Autostart symlink already existed."
        logger.exception(error_msg)
        invoke_callback(error_msg, success=True)
    except PermissionError:
        error_msg = "Denied trying to create autostart symlink."
        logger.exception(error_msg)
        invoke_callback(error_msg, success=False)
    except dbus.DBusException as e:
        error_msg = f"D-Bus error: {e!s}"
        logger.exception(error_msg)
        invoke_callback(error_msg, success=False)


def disable_autostart() -> tuple[bool, str | None]:
    """Disable autostart by removing the autostart symlink."""
    try:
        if Config.AUTOSTART_TARGET_FILE.exists(follow_symlinks=False):
            Config.AUTOSTART_TARGET_FILE.unlink()
            return True, None
    except PermissionError:
        error_msg = "Permission denied when trying to remove autostart symlink"
        logger.exception(error_msg)
        return False, error_msg
    except OSError as e:
        error_msg = f"Failed to remove autostart symlink: {e!s}"
        logger.exception(error_msg)
        return False, error_msg
    except FileNotFoundError:
        error_msg = "Autostart was already not enabled"
        logger.debug(error_msg)
        return True, error_msg
