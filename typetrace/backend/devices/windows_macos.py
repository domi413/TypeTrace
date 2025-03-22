"""Windows and macOS-specific device handling."""

from .base import BaseDeviceHandler


class WindowsMacOSDeviceHandler(BaseDeviceHandler):
    def check_device_accessibility(self):
        # Windows and macOS-specific device accessibility check
        pass

