"""Unit tests for LinuxEventProcessor from typetrace.backend.events.linux."""

import signal
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import evdev

from typetrace.backend.events.linux import LinuxEventProcessor


class TestLinuxEventProcessor(unittest.TestCase):
    """Test suite for LinuxEventProcessor."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.linux_processor = LinuxEventProcessor(str(self.db_path))

    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_check_device_accessibility_success(self) -> None:
        """Ensure no error when devices are accessible."""
        with patch.object(
            self.linux_processor,
            "_select_devices",
            return_value=[MagicMock()],
        ):
            self.linux_processor.check_device_accessibility()

    def test_select_devices(self) -> None:
        """Return mocked device from _select_devices()."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {
            evdev.ecodes.EV_KEY: [],
        }

        with (
            patch("evdev.util.list_devices", return_value=["/dev/input/event0"]),
            patch("evdev.device.InputDevice", return_value=mock_device),
        ):
            devices = self.linux_processor._select_devices()
            assert len(devices) == 1, "Expected exactly one device"
            assert devices[0] == mock_device, "Device does not match mock_device"

    def test_signal_termination(self) -> None:
        """SIGINT should set termination flag to True."""
        with (
            patch.object(
                self.linux_processor, "_select_devices", return_value=[MagicMock()]
            ),
            patch.object(self.linux_processor, "_buffer"),
            patch("signal.signal") as mock_signal,
        ):
            self.linux_processor.trace()
            handler = mock_signal.call_args_list[1][0][1]
            handler(signal.SIGINT, None)
            assert self.linux_processor._LinuxEventProcessor__terminate, (
                "Termination flag should be True"
            )


if __name__ == "__main__":
    unittest.main()
