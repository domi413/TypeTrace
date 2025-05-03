"""Base class for IPC communication."""

from __future__ import annotations

from typing import Self


class BaseIPC:
    """Base class for IPC communication."""

    def send_message(self: Self, message: str) -> None:
        """Send a message through the IPC channel."""
        raise NotImplementedError
