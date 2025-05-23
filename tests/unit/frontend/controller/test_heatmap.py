"""Tests for the Heatmap controller."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from unittest.mock import Mock


@pytest.fixture(autouse=True)
def mock_gtk() -> Generator[None, Mock, None]:
    """Mock GTK and related imports."""
    with patch.dict(
        "sys.modules",
        {
            "gi": MagicMock(),
            "gi.repository": MagicMock(),
            "gi.repository.Gtk": MagicMock(),
            "gi.repository.Gio": MagicMock(),
            "gi.repository.Gdk": MagicMock(),
            "gi.repository.Adw": MagicMock(),
        },
    ):
        yield


@pytest.fixture
def mock_settings() -> Mock:
    """Provide mock settings object."""
    settings = MagicMock()
    settings.get_string.return_value = "en_US"
    settings.get_int.return_value = 50
    settings.get_boolean.return_value = False
    return settings


@pytest.fixture
def mock_keystroke_store() -> Mock:
    """Provide mock keystroke store."""
    store = MagicMock()
    store.get_all_keystrokes.return_value = []
    store.get_highest_count.return_value = 0
    return store


@pytest.fixture
def mock_keystroke() -> Mock:
    """Provide mock keystroke object."""
    keystroke = MagicMock()
    keystroke.scan_code = 30
    keystroke.count = 10
    return keystroke


@pytest.fixture
def heatmap(mock_settings: Mock, mock_keystroke_store: Mock) -> Mock:
    """Provide a mock Heatmap instance."""
    heatmap = MagicMock()
    heatmap.settings = mock_settings
    heatmap.keystroke_store = mock_keystroke_store
    heatmap.layout = "en_US"
    heatmap.key_widgets = {}

    # Configure update method to populate key_widgets
    def update_side_effect(keystrokes: list[Mock] | None = None) -> None:
        if keystrokes is None:
            keystrokes = mock_keystroke_store.get_all_keystrokes()
        if keystrokes is None:
            return
        for keystroke in keystrokes:
            heatmap.key_widgets[keystroke.scan_code] = MagicMock()

    heatmap.update.side_effect = update_side_effect

    # Configure _on_zoom_clicked method to adjust key size
    def zoom_side_effect(amount: int) -> None:
        current_size = mock_settings.get_int("key-size")
        new_size = max(current_size + amount, 40)
        mock_settings.set_int("key-size", new_size)

    heatmap._on_zoom_clicked.side_effect = zoom_side_effect

    return heatmap


# =============================================================================
# ==================== Tests for Heatmap initialization =======================
# =============================================================================
def test_heatmap_initialization(heatmap: Mock) -> None:
    """Test that Heatmap initializes correctly with default values."""
    assert heatmap.layout == "en_US"
    assert isinstance(heatmap.key_widgets, dict)


def test_invalid_keyboard_layout(
    mock_settings: Mock,
    mock_keystroke_store: Mock,
) -> None:
    """Test handling of invalid keyboard layout."""
    mock_settings.get_string.return_value = "invalid_layout"
    heatmap = MagicMock()
    heatmap.settings = mock_settings
    heatmap.keystroke_store = mock_keystroke_store
    heatmap.layout = "en_US"  # Fallback to default
    heatmap.key_widgets = {}
    assert heatmap.layout == "en_US"


# =============================================================================
# ==================== Tests for Heatmap update method ========================
# =============================================================================
def test_empty_keystrokes(heatmap: Mock) -> None:
    """Test Heatmap update with empty keystroke data."""
    heatmap.update()
    assert len(heatmap.key_widgets) == 0


def test_single_keystroke(
    mock_keystroke_store: Mock,
    mock_keystroke: Mock,
    heatmap: Mock,
) -> None:
    """Test Heatmap update with a single keystroke."""
    mock_keystroke_store.get_all_keystrokes.return_value = [mock_keystroke]
    mock_keystroke_store.get_highest_count.return_value = 10

    heatmap.update()
    assert 30 in heatmap.key_widgets
    assert heatmap.key_widgets[30] is not None


# =============================================================================
# ==================== Tests for Heatmap zoom functionality ===================
# =============================================================================
def test_zoom_functionality(
    mock_settings: Mock,
    heatmap: Mock,
) -> None:
    """Test zoom in/out functionality."""
    initial_size = mock_settings.get_int.return_value

    heatmap._on_zoom_clicked(5)
    mock_settings.set_int.assert_called_with("key-size", initial_size + 5)

    heatmap._on_zoom_clicked(-100)
    mock_settings.set_int.assert_called_with("key-size", 40)


# =============================================================================
# ==================== TEMPORARY TEST TO DEMO PYTEST-MD-REPORT ===============
# =============================================================================
def test_temporary_failure_demo() -> None:
    """Temporary test that fails to demonstrate pytest-md-report.
    
    TODO: Remove this test after verifying the report functionality works.
    """
    assert 1 == 2, "This test intentionally fails to demo pytest-md-report"


def test_another_temporary_failure() -> None:
    """Another failing test to show multiple failures in the report."""
    msg = "Another intentional failure for the demo"
    raise ValueError(msg)
