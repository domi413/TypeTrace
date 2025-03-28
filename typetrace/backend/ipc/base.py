"""Base class for IPC communication."""


class BaseIPC:
    def send_message(self, message: str):
        raise NotImplementedError(
            "Method 'send_message' must be implemented in subclasses"
        )

