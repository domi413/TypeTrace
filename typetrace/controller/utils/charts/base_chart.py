"""Base chart utilities and common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, final

import cairo
from gi.repository import Adw

if TYPE_CHECKING:
    from gi.repository import Gtk

from typetrace.controller.utils import color_utils


class ChartColor(StrEnum):
    """Color definitions for chart elements."""

    BLUE = "0.4,0.6,0.8"  # Blue
    RED = "0.8,0.4,0.4"  # Red
    GREEN = "0.4,0.8,0.4"  # Green
    YELLOW = "0.8,0.8,0.4"  # Yellow
    PURPLE = "0.6,0.4,0.8"  # Purple
    ORANGE = "0.8,0.6,0.4"  # Orange
    CYAN = "0.4,0.8,0.8"  # Cyan
    MAGENTA = "0.8,0.4,0.8"  # Magenta
    PINK = "1.0,0.75,0.8"  # Pink
    LIGHT_PURPLE = "0.7,0.7,0.9"  # Light purple
    GRAY = "0.5,0.5,0.5"  # Gray


@dataclass
class TextConfig:
    """Configuration for drawing text."""

    cr: cairo.Context
    text: str
    x: float
    y: float
    font_size: float
    font_weight: cairo.FontWeight
    center: bool = False


class Chart(ABC):
    """Abstract base class for charts."""

    def __init__(self, drawing_area: Gtk.DrawingArea) -> None:
        """Initialize the chart.

        Args:
        ----
            drawing_area: The GTK drawing area to draw on

        """
        self.drawing_area = drawing_area
        self.style_manager = Adw.StyleManager.get_default()
        self.drawing_area.set_draw_func(self.draw)

    @abstractmethod
    def draw(
        self,
        area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the chart.

        Args:
        ----
            area: The drawing area
            cr: The Cairo context
            width: The width of the drawing area
            height: The height of the drawing area

        """

    @final
    def update(self) -> None:
        """Queue a redraw of the chart."""
        self.drawing_area.queue_draw()

    @final
    def _draw_text(
        self,
        config: TextConfig,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        """Draw text on the chart.

        Args:
        ----
            config: The text configuration
            color: The text color as RGB tuple

        """
        config.cr.set_source_rgb(*color)
        config.cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, config.font_weight)
        config.cr.set_font_size(config.font_size)
        x = config.x - (
            config.cr.text_extents(config.text).width / 2 if config.center else 0
        )
        config.cr.move_to(x, config.y)
        config.cr.show_text(config.text)

    @final
    def _draw_no_data(
        self,
        cr: cairo.Context,
        width: int,
        height: int,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        """Draw a message when no data is available.

        Args:
        ----
            cr: The Cairo context
            width: The width of the drawing area
            height: The height of the drawing area
            color: The text color as RGB tuple

        """
        self._draw_text(
            TextConfig(
                cr=cr,
                text="No keystroke data",
                x=width / 2,
                y=height / 2,
                font_size=16,
                font_weight=cairo.FONT_WEIGHT_BOLD,
                center=True,
            ),
            color,
        )

    @final
    def _get_accent_color(self) -> tuple:
        """Get the system accent color.

        Returns
        -------
            The accent color as RGB tuple

        """
        rgba = color_utils.get_system_accent_color()
        return (rgba.red, rgba.green, rgba.blue)

    @final
    def get_colors(self) -> dict[str, Any]:
        """Get the color scheme for the chart.

        Returns
        -------
            A dictionary with color values

        """
        is_dark = self.style_manager.get_dark()
        accent = self._get_accent_color()
        return {
            "line": accent,
            "fill": (*accent, 0.4 if self.style_manager.get_high_contrast() else 0.2),
            "text": (1.0, 1.0, 1.0) if is_dark else (0.0, 0.0, 0.0),
            "grid": (0.7, 0.7, 0.7) if is_dark else (0.3, 0.3, 0.3),
        }
