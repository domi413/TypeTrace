"""Utilities for drawing charts in the application."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, final, override

import cairo
from gi.repository import Adw, Gtk

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
    GRAY = "0.5,0.5,0.5"  # Gray
    LIGHT_PURPLE = "0.7,0.7,0.9"  # Light purple


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
class PieSliceDrawConfig:
    """Configuration for drawing a single pie slice."""

    cr: cairo.Context
    center_x: float
    center_y: float
    radius: float
    start_angle: float
    percent: float
    color: tuple[float, float, float]
    text_color: tuple[float, float, float]
    label: str | None = None


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
    def _get_accent_color(self) -> tuple:
        """Get the system accent color.

        Returns:
            The accent color as RGB tuple

        """
        rgba = color_utils.get_system_accent_color()
        return (rgba.red, rgba.green, rgba.blue)

    @final
    def get_colors(self) -> dict[str, Any]:
        """Get the color scheme for the chart.

        Returns:
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


@final
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

    @override
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


@final
class PieChart(Chart):
    """Pie chart implementation."""

    MIN_PERCENTAGE_THRESHOLD = 0.05  # Minimum percentage to display in the pie chart

    def __init__(
        self,
        drawing_area: Gtk.DrawingArea,
        data_provider: callable,
        total_count_provider: callable | None = None,
    ) -> None:
        """Initialize the pie chart.

        Args:
            drawing_area: The GTK drawing area to draw on
            data_provider: A function that returns the data for the chart
            total_count_provider: A function that returns the total count of all data

        """
        super().__init__(drawing_area)
        self.data_provider = data_provider
        self.total_count_provider = total_count_provider

    def _get_pie_colors(self) -> list[tuple[float, float, float]]:
        """Return a list of colors for pie slices."""
        return [
            tuple(float(x) for x in color.value.split(","))
            for color in [
                ChartColor.BLUE,
                ChartColor.RED,
                ChartColor.GREEN,
                ChartColor.YELLOW,
                ChartColor.PURPLE,
                ChartColor.ORANGE,
                ChartColor.CYAN,
                ChartColor.MAGENTA,
                ChartColor.GRAY,
                ChartColor.LIGHT_PURPLE,
            ]
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

    def _calculate_data_with_others(
        self,
        data: list[Any],
        total_count: int,
    ) -> tuple[list[Any], int, tuple[float, float, float]]:
        """Calculate others count and return data with others info.

        Args:
            data: List of data items
            total_count: Total count of all items

        Returns:
            Tuple containing (data items, others count, others color)

        """
        # Calculate sum of selected keystrokes
        selected_count = sum(item.count for item in data)

        # Calculate count for "Others" category
        others_count = max(0, total_count - selected_count)

        # Get color for "Others" category
        others_color = tuple(float(x) for x in ChartColor.GRAY.value.split(","))

        return data, others_count, others_color

    def _draw_pie_slice(
        self,
        config: PieSliceDrawConfig,
    ) -> float:
        """Draw a single pie slice with optional label.

        Returns:
            The end angle of the slice

        """
        angle = 2 * math.pi * config.percent

        config.cr.set_source_rgb(*config.color)
        config.cr.move_to(config.center_x, config.center_y)
        config.cr.arc(
            config.center_x,
            config.center_y,
            config.radius,
            config.start_angle,
            config.start_angle + angle,
        )
        config.cr.close_path()
        config.cr.fill()

        if config.percent > self.MIN_PERCENTAGE_THRESHOLD and config.label is not None:
            label_angle = config.start_angle + angle / 2
            label_x = config.center_x + math.cos(label_angle) * config.radius * 0.7
            label_y = config.center_y + math.sin(label_angle) * config.radius * 0.7
            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=config.label,
                    x=label_x,
                    y=label_y,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_BOLD,
                    center=True,
                ),
                config.text_color,
            )

        return config.start_angle + angle

    def _draw_slices_and_labels(self, config: PieSliceConfig) -> float:
        """Draw pie slices and their percentage labels."""
        start_angle = -math.pi / 2

        data, others_count, others_color = self._calculate_data_with_others(
            config.data,
            config.total_count,
        )

        # Draw slices for main data items
        for i, item in enumerate(data):
            percent = 0 if config.total_count == 0 else item.count / config.total_count
            color = config.pie_colors[i % len(config.pie_colors)]

            start_angle = self._draw_pie_slice(
                PieSliceDrawConfig(
                    cr=config.cr,
                    center_x=config.center_x,
                    center_y=config.center_y,
                    radius=config.radius,
                    start_angle=start_angle,
                    percent=percent,
                    color=color,
                    text_color=config.text_color,
                    label=f"{percent:.1%}",
                ),
            )

        # Draw "Others" slice
        if others_count > 0 and config.total_count > 0:
            percent = others_count / config.total_count

            start_angle = self._draw_pie_slice(
                PieSliceDrawConfig(
                    cr=config.cr,
                    center_x=config.center_x,
                    center_y=config.center_y,
                    radius=config.radius,
                    start_angle=start_angle,
                    percent=percent,
                    color=others_color,
                    text_color=config.text_color,
                    label=f"{percent:.1%}",
                ),
            )

        return start_angle

    def _draw_legend(self, config: LegendConfig) -> None:
        """Draw the legend for the pie chart."""
        legend_x = config.width * 0.75
        legend_y = config.height * 0.15
        legend_item_height = 20

        data, others_count, others_color = self._calculate_data_with_others(
            config.data,
            config.total_count,
        )

        # Draw legends for selected items
        for i, item in enumerate(data):
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

        if others_count > 0 and config.total_count > 0:
            percent = others_count / config.total_count
            current_legend_y = legend_y + len(data) * legend_item_height

            # Draw color box for "Others"
            config.cr.set_source_rgb(*others_color)
            config.cr.rectangle(legend_x, current_legend_y, 15, 15)
            config.cr.fill()

            # Draw legend text for "Others"
            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=f"Others: {others_count} ({percent:.1%})",
                    x=legend_x + 20,
                    y=current_legend_y + 12,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                ),
                config.text_color,
            )

    @override
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

        # Get total count of ALL keystrokes (not just selected ones)
        total_count = (
            self.total_count_provider()
            if self.total_count_provider
            else sum(item.count for item in data)
        )

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
