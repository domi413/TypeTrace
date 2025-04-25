"""Windows and Darwin-specific event processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from backend.events.base import BaseEventProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from typetrace.config import Event

logger = logging.getLogger(__name__)


class WindowsDarwinEventProcessor(BaseEventProcessor):
    """Event processor for Windows and Darwin platforms."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the Windows or Darwin event processor."""
        super().__init__(db_path)

    @override
    def trace(self) -> None:
        """See base class."""

    @override
    def _buffer(self, devices: list[Any]) -> None:
        """See base class."""

    @override
    def _process_single_event(
        self,
        event: Any,
    ) -> Event | None:
        """See base class."""
