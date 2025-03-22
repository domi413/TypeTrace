"""Linux-specific device handling."""

from .base import BaseDeviceHandler


class LinuxDeviceHandler(BaseDeviceHandler):
    def check_device_accessibility(self):
        # Linux-specific device accessibility check
        pass

