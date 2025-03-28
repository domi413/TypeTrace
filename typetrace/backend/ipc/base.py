"""Base class for IPC communication."""


class BaseIPC:
    """Base class for IPC communication."""

    def send_message(self, message: str) -> None:
        """Send a message through the IPC channel."""
        raise NotImplementedError
