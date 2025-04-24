import logging
import time
import evdev
import threading
import select

from typetrace.backend.ipc.base import BaseIPC

logging.basicConfig(level=logging.INFO)


class LinuxMacOSIPC(BaseIPC):
    """Real IPC backend for Linux, reads real keyboard inputs."""

    def __init__(self):
        """Initialize the real backend."""
        self._running = False
        self._callback = None
        self._devices = []
        self._stop_event = threading.Event()  # <-- ADDED
        print("LinuxMacOSIPC object created")

    def register_callback(self, callback):
        """Register a callback to be called when new events occur."""
        self._callback = callback
        logging.info("Callback successfully registered")

    def run(self):
        """Start the backend main loop."""
        print("LinuxMacOSIPC.run() started")
        if self._running:
            logging.warning("Backend is already running")
            return

        self._running = True
        self._devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        print(f"Devices found: {[dev.name for dev in self._devices]}")

        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()

    def _event_loop(self) -> None:
        while not self._stop_event.is_set():
            fds = [dev.fd for dev in self._devices]
            try:
                r, _, _ = select.select(
                    fds, [], [], 1
                )  # Blocks for 1 second or until a key is pressed
                for dev in self._devices:
                    if dev.fd in r:
                        for event in dev.read():
                            if event.type == evdev.ecodes.EV_KEY:
                                key_event = evdev.categorize(event)
                                if key_event.keystate == evdev.events.KeyEvent.key_down:
                                    key_name = key_event.keycode
                                    print(f" Key detected: {key_name}")  # <--- ADDED
                                    self._callback({"key": key_name})
            except Exception as e:
                print(f"Error in event loop: {e}")

    def stop(self):
        """Stop the backend."""
        if not self._running:
            logging.warning("Backend is not running")
            return

        self._running = False
        self._stop_event.set()  # <-- ADDED
        print("LinuxMacOSIPC stopped")
        logging.info("Backend stopped")
