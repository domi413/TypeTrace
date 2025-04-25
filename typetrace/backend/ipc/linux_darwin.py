"""IPC backend module for Linux and macOS systems.

This module provides a real IPC backend for capturing keyboard inputs on Linux
and macOS systems using the evdev library.
"""

import logging
import select
import threading
from typing import Callable

import evdev

from typetrace.backend.ipc.base import BaseIPC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinuxMacOSIPC(BaseIPC):
    """Real IPC backend for Linux, reads real keyboard inputs."""

    def __init__(self) -> None:
        """Initialize the real backend."""
        self._running = False
        self._callback = None
        self._devices = []
        self._stop_event = threading.Event()

    def register_callback(self, callback: Callable[[dict], None]) -> None:
        """Register a callback to be called when new events occur.

        Args:
        ----
            callback: A function to call with event data as a dictionary.

        """
        self._callback = callback
        logger.info("Callback successfully registered")

    def run(self) -> None:
        """Start the backend main loop."""
        if self._running:
            logger.warning("Backend is already running")
            return

        self._running = True
        self._devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()

    def _event_loop(self) -> None:
        while not self._stop_event.is_set():
            fds = [dev.fd for dev in self._devices]
            try:
                r, _, _ = select.select(
                    fds, [], [], 1,
                )  # Blocks for 1 second or until a key is pressed
                for dev in self._devices:
                    if dev.fd in r:
                        for event in dev.read():
                            if event.type == evdev.ecodes.EV_KEY:
                                key_event = evdev.categorize(event)
                                if key_event.keystate == evdev.events.KeyEvent.key_down:
                                    key_name = key_event.keycode
                                    self._callback({"key": key_name})
            except OSError:
                logger.exception("Error in event loop")

    def stop(self) -> None:
        """Stop the backend."""
        if not self._running:
            logger.warning("Backend is not running")
            return

        self._running = False
        self._stop_event.set()
        logger.info("Backend stopped")
