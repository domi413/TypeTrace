"""Windows and Darwin-specific event processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typetrace.backend.events.base import BaseEventProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from typetrace.config import Event

logger = logging.getLogger(__name__)


class WindowsDarwinEventProcessor(BaseEventProcessor):
    """Event processor for Windows and Darwin platforms."""

    def __init__(self: WindowsDarwinEventProcessor, db_path: Path) -> None:
        """Initialize the Windows or Darwin event processor."""
        super().__init__(db_path)

    def trace(self: WindowsDarwinEventProcessor) -> None:
        """See base class."""
        # Logic for tracing events on Windows or Darwin platforms can go here

    def _buffer(self: WindowsDarwinEventProcessor, devices: list) -> None:
        """See base class."""
        # Logic for buffering events can go here

    def _process_single_event(
        self: WindowsDarwinEventProcessor, event: Event | None,
    ) -> Event | None:
        """See base class."""

