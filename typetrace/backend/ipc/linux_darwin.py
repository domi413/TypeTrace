"""Linux and Darwin-specific IPC communication using sockets."""

from backend.ipc.base import BaseIPC


class LinuxMacOSIPC(BaseIPC):
    def send_message(self, message: str):
        # Linux and macOS-specific IPC communication using sockets
        pass
