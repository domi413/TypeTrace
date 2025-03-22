"""Windows-specific IPC communication using pipes."""

from .base import BaseIPC


class WindowsIPC(BaseIPC):
    def send_message(self, message: str):
        # Windows-specific IPC communication using pipes
        pass

