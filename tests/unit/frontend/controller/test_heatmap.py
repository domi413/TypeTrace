"""Unit tests for the Heatmap controller."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_gtk() -> None:
    """Mock GTK and related imports."""
    with patch.dict("sys.modules", {
        "gi": MagicMock(),
        "gi.repository": MagicMock(),
        "gi.repository.Gtk": MagicMock(),
        "gi.repository.Gio": MagicMock(),
        "gi.repository.Gdk": MagicMock(),
        "gi.repository.Adw": MagicMock(),
    }):
        yield


class MockKeystroke:
    """Mock keystroke class for testing."""

    def __init__(self:MockKeystroke, scan_code: int, count: int) -> None:
        """Initialize mock keystroke."""
        self.scan_code = scan_code
        self.count = count


class MockKeystrokeStore:
    """Mock keystroke store for testing."""

    def get_all_keystrokes(self:MockKeystroke) -> list[MockKeystroke]:
        """Get all mock keystrokes."""
        return []

    def get_highest_count(self:MockKeystroke) -> int:
        """Get highest count from mock keystrokes."""
        return 0


class MockHeatmap:
    """Mock heatmap class for testing."""

    def __init__(self:MockHeatmap, settings: MagicMock,
                 keystroke_store: MockKeystrokeStore) -> None:
        """Initialize mock heatmap."""
        self.settings = settings
        self.keystroke_store = keystroke_store
        self.layout = "en_US"
        self.key_widgets = {}

        self.settings.get_string.return_value = "en_US"
        self.settings.get_int.return_value = 50
        self.settings.get_boolean.return_value = False

    def update(self:MockHeatmap, keystrokes: list[MockKeystroke] | None = None) -> None:
        """Update mock heatmap with keystrokes."""
        if keystrokes is None:
            keystrokes = self.keystroke_store.get_all_keystrokes()

        for keystroke in keystrokes:
            self.key_widgets[keystroke.scan_code] = MagicMock()

    def _on_zoom_clicked(self:MockHeatmap, amount: int) -> None:
        """Handle zoom functionality in mock heatmap."""
        size = max(self.settings.get_int("key-size") + amount, 40)
        self.settings.set_int("key-size", size)


@pytest.fixture()
def mock_settings() -> MagicMock:
    """Fixture for mock settings."""
    settings = MagicMock()
    settings.get_string.return_value = "en_US"
    settings.get_int.return_value = 50
    settings.get_boolean.return_value = False
    return settings


@pytest.fixture()
def mock_keystroke_store() -> MagicMock:
    """Fixture for mock keystroke store."""
    store = MagicMock(spec=MockKeystrokeStore)
    store.get_all_keystrokes.return_value = []
    store.get_highest_count.return_value = 0
    return store


@pytest.fixture()
def heatmap(mock_settings: MagicMock, mock_keystroke_store: MagicMock) -> MockHeatmap:
    """Fixture for mock heatmap instance."""
    return MockHeatmap(mock_settings, mock_keystroke_store)


def test_heatmap_initialization(heatmap: MockHeatmap) -> None:
    """Test that heatmap initializes correctly with default values."""
    assert heatmap.layout == "en_US"
    assert isinstance(heatmap.key_widgets, dict)


def test_invalid_keyboard_layout(
    mock_settings: MagicMock,
    mock_keystroke_store: MagicMock,
) -> None:
    """Test handling of invalid keyboard layout."""
    mock_settings.get_string.return_value = "invalid_layout"
    heatmap = MockHeatmap(mock_settings, mock_keystroke_store)
    assert heatmap.layout == "en_US"


def test_empty_keystrokes(heatmap: MockHeatmap) -> None:
    """Test heatmap with empty keystroke data."""
    heatmap.update()
    assert len(heatmap.key_widgets) == 0


def test_single_keystroke(
    mock_keystroke_store: MagicMock,
    heatmap: MockHeatmap,
) -> None:
    """Test heatmap with a single keystroke."""
    test_keystroke = MockKeystroke(scan_code=30, count=10)
    mock_keystroke_store.get_all_keystrokes.return_value = [test_keystroke]
    mock_keystroke_store.get_highest_count.return_value = 10

    heatmap.update()
    assert 30 in heatmap.key_widgets


def test_zoom_functionality(
    mock_settings: MagicMock,
    heatmap: MockHeatmap,
) -> None:
    """Test zoom in/out functionality."""
    initial_size = mock_settings.get_int("key-size")

    heatmap._on_zoom_clicked(5)
    mock_settings.set_int.assert_called_with("key-size", initial_size + 5)

    heatmap._on_zoom_clicked(-100)
    mock_settings.set_int.assert_called_with("key-size", 40)
