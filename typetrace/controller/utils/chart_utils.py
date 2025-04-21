"""Utilities for drawing charts in the application."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, final

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


@dataclass
class GridAndAxesConfig:
    """Configuration for drawing grid and axes."""

    cr: cairo.Context
    width: int
    height: int
    padding: float
    graph_height: float
    max_value: float
    colors: dict


@dataclass
class DataLabelsConfig:
    """Configuration for drawing data labels."""

    cr: cairo.Context
    data: list[dict]
    points: list[tuple[float, float]]
    height: int
    padding: float
    colors: dict


@dataclass
class PieSliceConfig:
    """Configuration for drawing pie slices and labels."""

    cr: cairo.Context
    data: list[Any]
    total_count: int
    center_x: float
    center_y: float
    radius: float
    pie_colors: list
    text_color: tuple


@dataclass
class LegendConfig:
    """Configuration for drawing legend."""

    cr: cairo.Context
    data: list[Any]
    total_count: int
    width: int
    height: int
    pie_colors: list
    text_color: tuple


class Chart(ABC):
    """Abstract base class for charts."""

    def __init__(self, drawing_area: Gtk.DrawingArea) -> None:
        """Initialize the chart.

        Args:
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

    @final
    def get_colors(self) -> dict[str, Any]:
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

    def _setup_chart(
        self,
        width: int,
        height: int,
    ) -> tuple[dict, float, float, float]:
        """Set up chart parameters."""
        colors = self.get_colors()
        padding = 40
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        return colors, padding, graph_width, graph_height

    def _calculate_max_value(self, data: list[dict]) -> float:
        """Calculate the maximum value for the Y-axis."""
        max_val = max(d["count"] for d in data) if data else 0
        if max_val == 0:
            return 10.0
        power = 10 ** math.floor(math.log10(max_val))
        return math.ceil(max_val / power) * power

    def _draw_grid_and_axes(self, config: GridAndAxesConfig) -> None:
        """Draw the grid lines and axes for the chart."""
        num_steps = 5
        step = config.max_value / num_steps

        # Draw horizontal grid lines and y-axis labels
        for i in range(num_steps + 1):
            y = (
                config.padding
                + config.graph_height
                - (i * config.graph_height / num_steps)
            )
            config.cr.set_source_rgba(*config.colors["grid"], 0.5)
            config.cr.set_line_width(0.5)
            config.cr.move_to(config.padding, y)
            config.cr.line_to(config.width - config.padding, y)
            config.cr.stroke()
            value = int(i * step)
            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=str(value),
                    x=config.padding - 25,
                    y=y + 5,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                    center=True,
                ),
                config.colors["text"],
            )

        # Draw axes
        config.cr.set_source_rgba(*config.colors["text"], 1)
        config.cr.set_line_width(2)
        config.cr.move_to(config.padding, config.padding)
        config.cr.line_to(config.padding, config.height - config.padding)
        config.cr.line_to(config.width - config.padding, config.height - config.padding)
        config.cr.stroke()

    def _calculate_points(
        self,
        data: list[dict],
        padding: float,
        graph_width: float,
        graph_height: float,
        max_value: float,
    ) -> list[tuple[float, float]]:
        """Calculate the coordinates for data points."""
        if not data:
            return []

        return [
            (
                padding + (i * graph_width / (len(data) - 1) if len(data) > 1 else 0),
                padding
                + graph_height
                - (d["count"] / max_value * graph_height if max_value else 0),
            )
            for i, d in enumerate(data)
        ]

    def _draw_line_and_fill(
        self,
        cr: cairo.Context,
        points: list[tuple[float, float]],
        padding: float,
        graph_height: float,
        colors: dict,
    ) -> None:
        """Draw the line graph and the filled area underneath."""
        if not points:
            return

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

    def _draw_data_labels(self, config: DataLabelsConfig) -> None:
        """Draw data points and labels on the chart."""
        for i, ((x, y), d) in enumerate(zip(config.points, config.data)):
            # Draw points
            config.cr.set_source_rgba(*config.colors["line"], 1)
            config.cr.arc(x, y, 3, 0, 2 * math.pi)
            config.cr.fill()

            # Draw count labels
            if d["count"] > 0:
                x_offset = 20 if i == 0 else 0  # Offset first label from Y-axis
                self._draw_text(
                    TextConfig(
                        cr=config.cr,
                        text=str(d["count"]),
                        x=x + x_offset,
                        y=y - 10,
                        font_size=12,
                        font_weight=cairo.FONT_WEIGHT_NORMAL,
                        center=True,
                    ),
                    config.colors["text"],
                )

            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=d["date"],
                    x=x,
                    y=config.height - config.padding + 15,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                    center=True,
                ),
                config.colors["text"],
            )

    def draw(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the line chart."""
        data = self.data_provider()
        colors, padding, graph_width, graph_height = self._setup_chart(width, height)

        if not data:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        max_value = self._calculate_max_value(data)
        self._draw_grid_and_axes(
            GridAndAxesConfig(
                cr=cr,
                width=width,
                height=height,
                padding=padding,
                graph_height=graph_height,
                max_value=max_value,
                colors=colors,
            ),
        )
        points = self._calculate_points(
            data,
            padding,
            graph_width,
            graph_height,
            max_value,
        )
        self._draw_line_and_fill(cr, points, padding, graph_height, colors)
        self._draw_data_labels(
            DataLabelsConfig(
                cr=cr,
                data=data,
                points=points,
                height=height,
                padding=padding,
                colors=colors,
            ),
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

    def _get_pie_colors(self) -> list[tuple[float, float, float]]:
        """Return a list of colors for pie slices."""
        # NOTE: Consider making this dynamic or configurable
        return [
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

    def _calculate_geometry(
        self,
        width: int,
        height: int,
    ) -> tuple[float, float, float]:
        """Calculate center coordinates and radius for the pie chart."""
        chart_width = width * 0.65
        center_x = width / 2
        center_y = height / 2
        radius = min(chart_width, height) * 0.35
        return center_x, center_y, radius

    def _draw_slices_and_labels(self, config: PieSliceConfig) -> float:
        """Draw pie slices and their percentage labels."""
        start_angle = -math.pi / 2
        for i, item in enumerate(config.data):
            percent = 0 if config.total_count == 0 else item.count / config.total_count
            angle = 2 * math.pi * percent
            color = config.pie_colors[i % len(config.pie_colors)]

            config.cr.set_source_rgb(*color)
            config.cr.move_to(config.center_x, config.center_y)
            config.cr.arc(
                config.center_x,
                config.center_y,
                config.radius,
                start_angle,
                start_angle + angle,
            )
            config.cr.close_path()
            config.cr.fill()

            if percent > self.MIN_PERCENTAGE_THRESHOLD:
                label_angle = start_angle + angle / 2
                label_x = config.center_x + math.cos(label_angle) * config.radius * 0.7
                label_y = config.center_y + math.sin(label_angle) * config.radius * 0.7
                self._draw_text(
                    TextConfig(
                        cr=config.cr,
                        text=f"{percent:.1%}",
                        x=label_x,
                        y=label_y,
                        font_size=12,
                        font_weight=cairo.FONT_WEIGHT_BOLD,
                        center=True,
                    ),
                    config.text_color,
                )

            start_angle += angle
        return start_angle

    def _draw_legend(self, config: LegendConfig) -> None:
        """Draw the legend for the pie chart."""
        legend_x = config.width * 0.75
        legend_y = config.height * 0.15
        legend_item_height = 25

        for i, item in enumerate(config.data):
            percent = 0 if config.total_count == 0 else item.count / config.total_count

            color = config.pie_colors[i % len(config.pie_colors)]
            current_legend_y = legend_y + i * legend_item_height

            # Draw color box
            config.cr.set_source_rgb(*color)
            config.cr.rectangle(legend_x, current_legend_y, 15, 15)
            config.cr.fill()

            # Draw legend text
            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=f"{item.key_name}: {item.count} ({percent:.1%})",
                    x=legend_x + 20,
                    y=current_legend_y + 12,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                ),
                config.text_color,
            )

    def draw(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw the pie chart."""
        colors = self.get_colors()
        data = self.data_provider()

        if not data:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        total_count = sum(item.count for item in data)
        if total_count == 0:
            self._draw_no_data(cr, width, height, colors["text"])
            return

        pie_colors = self._get_pie_colors()
        center_x, center_y, radius = self._calculate_geometry(width, height)

        self._draw_slices_and_labels(
            PieSliceConfig(
                cr=cr,
                data=data,
                total_count=total_count,
                center_x=center_x,
                center_y=center_y,
                radius=radius,
                pie_colors=pie_colors,
                text_color=colors["text"],
            ),
        )
        self._draw_legend(
            LegendConfig(
                cr=cr,
                data=data,
                total_count=total_count,
                width=width,
                height=height,
                pie_colors=pie_colors,
                text_color=colors["text"],
            ),
        )
