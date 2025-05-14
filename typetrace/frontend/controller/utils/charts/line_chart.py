"""Line chart implementation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final, override

import cairo

if TYPE_CHECKING:
    from gi.repository import Gtk

from typetrace.frontend.controller.utils.charts.base_chart import Chart, TextConfig


@dataclass
class GridAndAxesConfig:
    """Configuration for drawing grid and axes."""

    cr: cairo.Context
    width: int
    height: int
    padding: float
    graph_height: float
    max_value: float
    colors: dict[str, Any]


@dataclass
class DataLabelsConfig:
    """Configuration for drawing data labels."""

    cr: cairo.Context
    data: list[dict[str, Any]]
    points: list[tuple[float, float]]
    height: int
    padding: float
    colors: dict[str, Any]


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
        padding = 60
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
            text_width = config.cr.text_extents(str(value)).width
            self._draw_text(
                TextConfig(
                    cr=config.cr,
                    text=str(value),
                    x=config.padding - 10 - text_width,
                    y=y + 5,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                    center=False,
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
        area: Gtk.DrawingArea,
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
