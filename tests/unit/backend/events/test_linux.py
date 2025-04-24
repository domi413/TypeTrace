import os
import signal
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import evdev

from typetrace.backend.events.linux import LinuxEventProcessor


class TestLinuxEventProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.linux_processor = LinuxEventProcessor(self.db_path)

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_check_device_accessibility_success(self):
        with patch.object(
            self.linux_processor,
            "_select_devices",
            return_value=[MagicMock()],
        ):
            self.linux_processor.check_device_accessibility()

    def test_select_devices(self):
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {evdev.ecodes.EV_KEY: []}
        with patch("evdev.util.list_devices", return_value=["/dev/input/event0"]):
            with patch("evdev.device.InputDevice", return_value=mock_device):
                devices = self.linux_processor._select_devices()
                self.assertEqual(len(devices), 1, "Expected exactly one device")
                self.assertEqual(
                    devices[0],
                    mock_device,
                    "Device does not match mock_device",
                )

    def test_signal_termination(self):
        with patch.object(
            self.linux_processor,
            "_select_devices",
            return_value=[MagicMock()],
        ):
            with patch.object(self.linux_processor, "_buffer"):
                with patch("signal.signal") as mock_signal:
                    self.linux_processor.trace()
                    handler = mock_signal.call_args_list[1][0][1]
                    handler(signal.SIGINT, None)
                    self.assertTrue(
                        self.linux_processor._LinuxEventProcessor__terminate,
                        "Termination flag should be True",
                    )


if __name__ == "__main__":
    unittest.main()
