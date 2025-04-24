from unittest.mock import MagicMock, patch

import pytest
from gi.repository import Gio

from typetrace.controller.window import TypetraceWindow
from typetrace.model.keystrokes import KeystrokeStore


@pytest.fixture()
def mock_keystroke_store():
    """Fixture for mocking KeystrokeStore."""
    return MagicMock(spec=KeystrokeStore)


@pytest.fixture()
def mock_settings():
    """Fixture for mocking Gio.Settings."""
    return MagicMock(spec=Gio.Settings)


@pytest.fixture()
def mock_typetrace_window(mock_keystroke_store, mock_settings):
    """Fixture for TypetraceWindow with mocked dependencies."""
    stack_mock = MagicMock()

    with patch("gi.repository.Adw.ApplicationWindow"), patch(
        "typetrace.controller.window.Heatmap",
    ) as mock_heatmap, patch("typetrace.controller.window.Verbose") as mock_verbose:

        mock_heatmap.return_value = MagicMock()
        mock_verbose.return_value = MagicMock()

        window = TypetraceWindow(
            keystroke_store=mock_keystroke_store, settings=mock_settings,
        )
        window.refresh_button = MagicMock()

        window.view_switcher = MagicMock()
        window.view_switcher.get_stack.return_value = stack_mock
        window.stack = stack_mock

        return window


def test_initialization(mock_typetrace_window):
    """Test the initialization of the window and its views."""
    window = mock_typetrace_window

    assert window.backend_thread is not None
    assert isinstance(window.heatmap, MagicMock)
    assert isinstance(window.verbose, MagicMock)
    assert window.view_switcher.get_stack() == window.stack


def test_refresh_button_click(mock_typetrace_window):
    """Test the click on the refresh button."""
    window = mock_typetrace_window

    window.heatmap.update = MagicMock()
    window.verbose.update = MagicMock()

    window._on_refresh_clicked()

    window.heatmap.update.assert_called_once()
    window.verbose.update.assert_called_once()


def test_on_keystroke_received(mock_typetrace_window):
    """Test the handling of received keystrokes."""
    window = mock_typetrace_window
    event = {"key": "a", "timestamp": 123456}

    window.heatmap.update = MagicMock()
    window.verbose.update = MagicMock()

    window._on_keystroke_received(event)

    window.heatmap.update.assert_called_once()
    window.verbose.update.assert_called_once()

    window.heatmap.keystroke_store.add.assert_called_once_with(event)
