import pytest
from unittest.mock import MagicMock, patch
import evdev
import signal
import time

from typetrace.backend.events.linux import LinuxEventProcessor
from typetrace.config import Event


class TestLinuxEventProcessor:
    """Test suite for LinuxEventProcessor class."""

    @pytest.fixture
    def linux_processor(self, tmp_path):
        """Provide a LinuxEventProcessor instance."""
        return LinuxEventProcessor(tmp_path / "test.db")

    def test_check_device_accessibility_success(self, linux_processor):
        """Test successful device accessibility check."""
        with patch.object(linux_processor, '_select_devices', return_value=[MagicMock()]):
            linux_processor.check_device_accessibility()  # Should not raise

    def test_select_devices(self, linux_processor):
        """Test device selection."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {evdev.ecodes.EV_KEY: []}
        with patch('evdev.util.list_devices', return_value=["/dev/input/event0"]):
            with patch('evdev.device.InputDevice', return_value=mock_device):
                devices = linux_processor._select_devices()
                assert len(devices) == 1
                assert devices[0] == mock_device

    def test_buffer_with_devices(self, linux_processor):
        """Test buffer method with devices."""
        mock_device = MagicMock()
        with patch('select.select', return_value=([mock_device], [], [])):
            with patch.object(linux_processor, '_read_device_events', return_value=[]):
                with patch.object(linux_processor, '_check_timeout_and_flush', return_value=([], time.time())):
                    linux_processor._buffer([mock_device])  # Should not raise

    def test_signal_termination(self, linux_processor):
        """Test signal termination handling."""
        with patch.object(linux_processor, '_select_devices', return_value=[MagicMock()]):
            with patch.object(linux_processor, '_buffer'):
                with patch('signal.signal') as mock_signal:
                    linux_processor.trace()
                    handler = mock_signal.call_args_list[1][0][1]  # SIGINT handler
                    handler(signal.SIGINT, None)
                    assert linux_processor._LinuxEventProcessor__terminate is True