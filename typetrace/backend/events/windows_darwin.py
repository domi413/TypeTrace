"""Windows and Darwin-specific event processing."""

import logging
import platform
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

    def __init__(self) -> None:
        super().__init__()
        self.__cached_keyboards: None = None
        self.__db_path: Path
        self.__terminate = False

    @override
    def trace(self, db_path: Path) -> None:
        with keyboard.Listener(
                on_release=lambda key: self._on_key_event(key, db_path),
        ) as listener:
            logger.debug("Started Windows keyboard monitoring")
            listener.join()

    @override
    def _process_single_event(
            self,
            event: Any,
            buffer: list[KeyEvent],
            start_time: float,
    ) -> tuple[list[KeyEvent], float]:
        if event:
            buffer.append(event)
            self._print_key(event)

            if len(buffer) >= Config.BUFFER_SIZE:
                return [], time.time()

        return buffer, start_time

    def _create_key_event(self, key: Any) -> KeyEvent:
        """Create a key event dictionary from a pynput key.

        Args:
            key: The pynput key object.
        Returns:
            Dictionary containing key details.
        """
        try:
            current_time = time.time()

            # Handle special keys
            if isinstance(key, keyboard.Key):
                return {
                    "time": current_time,
                    "name": key.name,
                    "scan_code": key.value.vk,
                }
            # Handle regular character keys
            elif hasattr(key, "char") and key.char is not None:
                return {
                    "time": current_time,
                    "name": key.char,
                    "scan_code": key.vk,
                }
            # Handle other keys
            elif hasattr(key, "vk"):
                return {
                    "time": current_time,
                    "name": f"unknown_{key.vk}",
                    "scan_code": key.vk,
                }
            return None
        except AttributeError:
            logger.warning(f"Could not process key {key}")
            return None

    def _on_key_event(self, key: Any, db_path: Path) -> None:
        """Process key release events.

        Args:
            key: The key that was released.
            db_path: Path to the database.
        """
        try:
            event = self._create_key_event(key)
            if event:
                DatabaseManager.write_to_database(db_path, [event])
                self._print_key(event)
        except Exception as e:
            logger.error(f"Error processing key event: {e}")
