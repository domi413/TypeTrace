"""Windows-specific IPC communication using pipes."""

from typetrace.backend.ipc.base import BaseIPC


class WindowsIPC(BaseIPC):
    """Windows-specific IPC communication using pipes."""

    def send_message(self, message: str) -> None:
        """Send a message through the IPC channel."""
        # Windows-specific IPC communication using pipes
