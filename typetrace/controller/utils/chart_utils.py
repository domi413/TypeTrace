"""Utilities for drawing charts in the application."""

from __future__ import annotations

import abc
import math
from dataclasses import dataclass
from typing import Any, Dict

import cairo
from gi.repository import Adw, Gtk


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


class Chart(abc.ABC):
    """Abstract base class for charts."""

    def __init__(self, drawing_area: Gtk.DrawingArea) -> None:
        """Initialize the chart.

        Args:
            drawing_area: The GTK drawing area to draw on

        """
        self.drawing_area = drawing_area
        self.style_manager = Adw.StyleManager.get_default()
        self.drawing_area.set_draw_func(self.draw)

    @abc.abstractmethod
    def draw(
        self,
        area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the chart.

        Args:
            area: The drawing area
            cr: The Cairo context
            width: The width of the drawing area
            height: The height of the drawing area

        """

    def update(self) -> None:
        """Queue a redraw of the chart."""
        self.drawing_area.queue_draw()

    def _draw_text(
        self,
        config: TextConfig,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        """Draw text on the chart.

        Args:
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

    def _draw_no_data(
        self,
        cr: cairo.Context,
        width: int,
        height: int,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        """Draw a message when no data is available.

        Args:
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

    def _get_accent_color(self, *, is_dark: bool) -> tuple:
        """Get the system accent color.

        Args:
            is_dark: Whether the system is using dark mode

        Returns:
            The accent color as RGB tuple

        """
        if hasattr(self.style_manager, "get_accent_color_rgba"):
            rgba = self.style_manager.get_accent_color_rgba()
            if rgba:
                return (rgba.red, rgba.green, rgba.blue)

        # Default accent color if no accent color
        return (0.3, 0.6, 1.0) if is_dark else (0.2, 0.5, 0.9)

    def get_colors(self) -> Dict[str, Any]:
        """Get the color scheme for the chart.

        Returns:
            A dictionary with color values

        """
        is_dark = self.style_manager.get_dark()
        accent = self._get_accent_color(is_dark=is_dark)
        return {
            "line": accent,
            "fill": (*accent, 0.4 if self.style_manager.get_high_contrast() else 0.2),
            "text": (1.0, 1.0, 1.0) if is_dark else (0.0, 0.0, 0.0),
            "grid": (0.7, 0.7, 0.7) if is_dark else (0.3, 0.3, 0.3),
        }


class LineChart(Chart):
    """Line chart implementation."""

    def __init__(
        self,
        drawing_area: Gtk.DrawingArea,
        data_provider: callable,
    ) -> None:
        """Initialize the line chart.

        Args:
            drawing_area: The GTK drawing area to draw on
            data_provider: A function that returns the data for the chart

        """
        super().__init__(drawing_area)
        self.data_provider = data_provider

    def draw(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the line chart.

        Args:
            _area: The drawing area
            cr: The Cairo context
            width: The width of the drawing area
            height: The height of the drawing area

        """
        colors = self.get_colors()
        padding = 40
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        data = self.data_provider()

        if not data:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        max_value = max(d["count"] for d in data)

        if max_value == 0:
            max_value = 10
        else:
            power = 10 ** math.floor(math.log10(max_value))
            max_value = math.ceil(max_value / power) * power

        num_steps = 5
        step = max_value / num_steps

        # Draw grid lines and y-axis labels
        for i in range(num_steps + 1):
            y = padding + graph_height - (i * graph_height / num_steps)
            cr.set_source_rgba(*colors["grid"], 0.5)
            cr.set_line_width(0.5)
            cr.move_to(padding, y)
            cr.line_to(width - padding, y)
            cr.stroke()
            value = int(i * step)
            self._draw_text(
                TextConfig(
                    cr=cr,
                    text=str(value),
                    x=padding - 25,
                    y=y + 5,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                    center=True,
                ),
                colors["text"],
            )

        # Draw vertical grid lines
        for i in range(len(data)):
            x = padding + (i * graph_width / (len(data) - 1) if len(data) > 1 else 0)
            cr.set_source_rgba(*colors["grid"], 0.5)
            cr.move_to(x, padding)
            cr.line_to(x, height - padding)
            cr.stroke()

        # Draw axes
        cr.set_source_rgba(*colors["text"], 1)
        cr.set_line_width(2)
        cr.move_to(padding, padding)
        cr.line_to(padding, height - padding)
        cr.line_to(width - padding, height - padding)
        cr.stroke()

        # Draw line and fill
        points = [
            (
                padding + (i * graph_width / (len(data) - 1) if len(data) > 1 else 0),
                padding
                + graph_height
                - (d["count"] / max_value * graph_height if max_value else 0),
            )
            for i, d in enumerate(data)
        ]

        if points:
            cr.set_line_width(2)
            cr.set_source_rgba(*colors["line"], 1)
            cr.move_to(*points[0])
            for i in range(1, len(points)):
                x0, y0 = points[i - 1]
                x1, y1 = points[i]
                cp_dist_x = (x1 - x0) * 0.4
                cr.curve_to(x0 + cp_dist_x, y0, x1 - cp_dist_x, y1, x1, y1)
            cr.stroke_preserve()
            cr.line_to(points[-1][0], padding + graph_height)
            cr.line_to(padding, padding + graph_height)
            cr.close_path()
            cr.set_source_rgba(*colors["fill"])
            cr.fill()

        # Draw points and labels
        for i, ((x, y), d) in enumerate(zip(points, data)):
            cr.set_source_rgba(*colors["line"], 1)
            cr.arc(x, y, 3, 0, 2 * math.pi)
            cr.fill()
            if d["count"] > 0:
                # First data point, increase offset so it's not overlapping with Y-axis
                x_offset = 0
                if i == 0:
                    x_offset = 20
                self._draw_text(
                    TextConfig(
                        cr=cr,
                        text=str(d["count"]),
                        x=x + x_offset,
                        y=y - 10,
                        font_size=12,
                        font_weight=cairo.FONT_WEIGHT_NORMAL,
                        center=True,
                    ),
                    colors["text"],
                )
            self._draw_text(
                TextConfig(
                    cr=cr,
                    text=d["date"],
                    x=x,
                    y=height - padding + 15,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                    center=True,
                ),
                colors["text"],
            )


class PieChart(Chart):
    """Pie chart implementation."""

    MIN_PERCENTAGE_THRESHOLD = 0.05  # Minimum percentage to display in the pie chart

    def __init__(
        self,
        drawing_area: Gtk.DrawingArea,
        data_provider: callable,
    ) -> None:
        """Initialize the pie chart.

        Args:
            drawing_area: The GTK drawing area to draw on
            data_provider: A function that returns the data for the chart

        """
        super().__init__(drawing_area)
        self.data_provider = data_provider

    def draw(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the pie chart.

        Args:
            _area: The drawing area
            cr: The Cairo context
            width: The width of the drawing area
            height: The height of the drawing area

        """
        colors = self.get_colors()
        data = self.data_provider()

        if not data:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        # Colors for the pie slices
        pie_colors = [
            (0.4, 0.6, 0.8),  # Blue
            (0.8, 0.4, 0.4),  # Red
            (0.4, 0.8, 0.4),  # Green
            (0.8, 0.8, 0.4),  # Yellow
            (0.6, 0.4, 0.8),  # Purple
            (0.8, 0.6, 0.4),  # Orange
            (0.4, 0.8, 0.8),  # Cyan
            (0.8, 0.4, 0.8),  # Magenta
            (0.5, 0.5, 0.5),  # Gray
            (0.7, 0.7, 0.9),  # Light purple
        ]

        total_count = sum(item.count for item in data)
        if total_count == 0:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        chart_width = width * 0.65
        center_x, center_y = width / 2, height / 2
        radius = min(chart_width, height) * 0.35
        start_angle = -math.pi / 2
        legend_x, legend_y = width * 0.75, height * 0.15

        for i, item in enumerate(data):
            percent = item.count / total_count
            angle = 2 * math.pi * percent
            cr.set_source_rgb(*pie_colors[i % len(pie_colors)])
            cr.move_to(center_x, center_y)
            cr.arc(center_x, center_y, radius, start_angle, start_angle + angle)
            cr.close_path()
            cr.fill()

            if percent > self.MIN_PERCENTAGE_THRESHOLD:
                label_angle = start_angle + angle / 2
                label_x = center_x + math.cos(label_angle) * radius * 0.7
                label_y = center_y + math.sin(label_angle) * radius * 0.7
                self._draw_text(
                    TextConfig(
                        cr=cr,
                        text=f"{percent:.1%}",
                        x=label_x,
                        y=label_y,
                        font_size=12,
                        font_weight=cairo.FONT_WEIGHT_BOLD,
                        center=True,
                    ),
                    colors["text"],
                )

            cr.set_source_rgb(*pie_colors[i % len(pie_colors)])
            cr.rectangle(legend_x, legend_y + i * 25, 15, 15)
            cr.fill()
            self._draw_text(
                TextConfig(
                    cr=cr,
                    text=f"{item.key_name}: {item.count} ({percent:.1%})",
                    x=legend_x + 20,
                    y=legend_y + i * 25 + 12,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                ),
                colors["text"],
            )
            start_angle += angle
