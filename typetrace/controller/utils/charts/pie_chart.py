"""Pie chart implementation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final, override

import cairo

if TYPE_CHECKING:
    from gi.repository import Gtk

from typetrace.controller.utils.charts.base_chart import Chart, ChartColor, TextConfig


@dataclass
class PieSliceConfig:
    """Configuration for drawing pie slices and labels."""

    cr: cairo.Context
    data: list[Any]
    total_count: int
    center_x: float
    center_y: float
    radius: float
    pie_colors: list[tuple[float, float, float]]
    text_color: tuple[float, float, float]


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
    pie_colors: list[tuple[float, float, float]]
    text_color: tuple[float, float, float]


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
        ----
            drawing_area: The GTK drawing area to draw on
            data_provider: A function that returns the data for the chart
            total_count_provider: A function that returns the total count of all data

        """
        super().__init__(drawing_area)
        self.data_provider = data_provider
        self.total_count_provider = total_count_provider

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
        ----
            data: List of data items
            total_count: Total count of all items

        Returns:
        -------
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

        Returns
        -------
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

        pie_colors = [
            tuple(float(x) for x in color.value.split(",")) for color in ChartColor
        ]
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
