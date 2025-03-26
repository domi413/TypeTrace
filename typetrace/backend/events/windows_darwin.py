"""Windows and Darwin-specific event processing."""

import logging
import time
from pathlib import Path
from typing import Any, override

from backend.config import Config, KeyEvent
from backend.db import DatabaseManager
from backend.events.base import BaseEventProcessor
from pynput import keyboard

logger = logging.getLogger(__name__)


class WindowsDarwinEventProcessor(BaseEventProcessor):
    """Event processor for Windows and Darwin platforms."""

    @override
    def trace(self, db_path: Path) -> None:
        """See base class."""
        with keyboard.Listener(
            on_press=lambda key: self._on_key_event(key, True, db_path),
            on_release=lambda key: self._on_key_event(key, False, db_path),
        ) as listener:
            logger.info("Started keyboard monitoring")
            listener.join()

    @override
    def _buffer(self, devices: list[Any], db_path: Path) -> None:
        """See base class."""
        buffer: list[KeyEvent] = []
        start_time = time.time()

        def on_press(key: Any) -> None:
            nonlocal buffer, start_time
            event = self._create_key_event(key, True)
            if event:
                buffer.append(event)
                self._print_key(event)

                if len(buffer) >= Config.BUFFER_SIZE:
                    DatabaseManager.write_to_database(db_path, buffer)
                    buffer.clear()
                    start_time = time.time()
                else:
                    buffer, start_time = self._check_timeout_and_flush(
                        buffer, start_time, db_path
                    )

    @override
    def _process_single_event(
        self,
        event: Any,
        buffer: list[KeyEvent],
        start_time: float,
    ) -> tuple[list[KeyEvent], float]:
        """See base class."""
        if event:
            buffer.append(event)
            self._print_key(event)

            if len(buffer) >= Config.BUFFER_SIZE:
                return [], time.time()

        return buffer, start_time

    def _create_key_event(self, key: Any, is_press: bool) -> KeyEvent:
        """Create a key event dictionary from a pynput key.

        Args:
            key: The pynput key object.
            is_press: True if key was pressed, False if released.

        Returns:
            Dictionary containing key details.

        """
        try:
            current_time = time.time()
            event_type = "press" if is_press else "release"

            # Handle special keys
            if isinstance(key, keyboard.Key):
                return {
                    "time": current_time,
                    "name": key.name,
                    "scan_code": key.value.vk,
                    "event_type": event_type,
                }
            # Handle regular character keys
            elif hasattr(key, "char") and key.char is not None:
                return {
                    "time": current_time,
                    "name": key.char,
                    "scan_code": key.vk,
                    "event_type": event_type,
                }
            # Handle other keys
            elif hasattr(key, "vk"):
                return {
                    "time": current_time,
                    "name": f"unknown_{key.vk}",
                    "scan_code": key.vk,
                    "event_type": event_type,
                }
            return None
        except AttributeError:
            logger.warning(f"Could not process key {key}")
            return None

    def _on_key_event(self, key: Any, is_press: bool, db_path: Path) -> None:
        """Process key press or release events.

        Args:
            key: The key that was pressed or released.
            is_press: True if key was pressed, False if released.
            db_path: Path to the database.

        """
        try:
            # Handle key presses and releases
            event = self._create_key_event(key, is_press)
            if event:
                DatabaseManager.write_to_database(db_path, [event])
                self._print_key(event)
        except Exception as e:
            logger.error(f"Error processing key event: {e}")
