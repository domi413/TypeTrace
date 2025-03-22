"""Base class for device handling."""


class BaseDeviceHandler:
    def check_device_accessibility(self):
        raise NotImplementedError(
            "Method 'check_device_accessibility' must be implemented in subclasses"
        )

