"""Linux and macOS-specific IPC communication using sockets."""

from .base import BaseIPC


class LinuxMacOSIPC(BaseIPC):
    def send_message(self, message: str):
        # Linux and macOS-specific IPC communication using sockets
        pass

