"""Linux and Darwin-specific IPC communication using sockets."""

from backend.ipc.base import BaseIPC


class LinuxMacOSIPC(BaseIPC):
    """Linux and Darwin-specific IPC communication using sockets."""

    def send_message(self, message: str) -> None:
        """Send a message through the IPC channel."""
        # Linux and macOS-specific IPC communication using sockets
