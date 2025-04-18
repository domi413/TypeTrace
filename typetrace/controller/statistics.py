"""The statistics page displays keystroke data in various graphs/diagrams."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import cairo
from gi.repository import Adw, Gio, Gtk

if TYPE_CHECKING:
    from typetrace.model.keystrokes import Keystroke, KeystrokeStore


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


@Gtk.Template(resource_path="/edu/ost/typetrace/view/statistics.ui")
class Statistics(Gtk.Box):
    """The statistics page displays keystroke data in various graphs/diagrams."""

    __gtype_name__ = "Statistics"
    MIN_PERCENTAGE_THRESHOLD = 0.05  # Minimum percentage to display in the pie chart
    carousel = Gtk.Template.Child()
    drawing_area = Gtk.Template.Child()
    line_drawing_area = Gtk.Template.Child()
    bar_count_spin = Gtk.Template.Child()
    calendar = Gtk.Template.Child()
    date_button = Gtk.Template.Child()
    clear_date_button = Gtk.Template.Child()

    def __init__(self, keystroke_store: KeystrokeStore, **kwargs) -> None:
        """Initialize the statistics page with keystroke data.

        Args:
            keystroke_store: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store
        self.selected_date = None
        self.style_manager = Adw.StyleManager.get_default()
        self.drawing_area.set_draw_func(self._draw_line_chart)
        self.line_drawing_area.set_draw_func(self._draw_pie_chart)
        self.bar_count_spin.set_range(1, 10)
        self.bar_count_spin.set_value(5)
        self.bar_count_spin.connect(
            "value-changed",
            lambda _: self.line_drawing_area.queue_draw(),
        )
        self.clear_date_button.connect("clicked", self._clear_date)
        self.calendar.connect("day-selected", self._date_selected)
        self.clear_date_button.set_sensitive(False)

    def update(self) -> None:
        """Queue a redraw of the statistics drawing areas."""
        self.drawing_area.queue_draw()
        self.line_drawing_area.queue_draw()

    def _clear_date(self, _button: Gtk.Button) -> None:
        self.selected_date = None
        self.clear_date_button.set_sensitive(False)
        self.date_button.set_label("Select Date")
        self.line_drawing_area.queue_draw()

    def _date_selected(self, calendar: Gtk.Calendar) -> None:
        self.selected_date = calendar.get_date().format("%Y-%m-%d")
        self.date_button.get_popover().popdown()
        self.clear_date_button.set_sensitive(True)
        self.date_button.set_label(self.selected_date)
        self.line_drawing_area.queue_draw()

    def _get_top_keystrokes(self, count: int) -> list[Keystroke]:
        keystrokes = (
            self.keystroke_store.get_keystrokes_by_date(self.selected_date)
            if self.selected_date
            else self.keystroke_store.get_all_keystrokes()
        )
        return sorted(keystrokes, key=lambda k: k.count, reverse=True)[:count]

    def _draw_text(
        self,
        config: TextConfig,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
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

    def _draw_pie_chart(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        keystrokes = self._get_top_keystrokes(int(self.bar_count_spin.get_value()))
        if not keystrokes:
            self._draw_no_data(cr, width, height)
            return

        # Colors for the pie slices
        colors = [
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
        total_count = sum(k.count for k in keystrokes)
        if total_count == 0:
            self._draw_no_data(cr, width, height)
            return

        self._draw_text(
            TextConfig(
                cr=cr,
                text="Top Keystrokes",
                x=width / 2,
                y=30,
                font_size=16,
                font_weight=cairo.FONT_WEIGHT_BOLD,
                center=True,
            ),
        )

        chart_width = width * 0.65
        center_x, center_y = chart_width / 2, height / 2
        radius = min(chart_width, height) * 0.35
        start_angle = -math.pi / 2
        legend_x, legend_y = chart_width + 40, height * 0.15

        for i, k in enumerate(keystrokes):
            percent = k.count / total_count
            angle = 2 * math.pi * percent
            cr.set_source_rgb(*colors[i % len(colors)])
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
                )

            cr.set_source_rgb(*colors[i % len(colors)])
            cr.rectangle(legend_x, legend_y + i * 25, 15, 15)
            cr.fill()
            self._draw_text(
                TextConfig(
                    cr=cr,
                    text=f"{k.key_name}: {k.count} ({percent:.1%})",
                    x=legend_x + 20,
                    y=legend_y + i * 25 + 12,
                    font_size=12,
                    font_weight=cairo.FONT_WEIGHT_NORMAL,
                ),
            )
            start_angle += angle

    def _draw_line_chart(  # noqa: PLR0915, else it gets to messy
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        is_dark = self.style_manager.get_dark()
        accent = self._get_accent_color(is_dark=is_dark)
        colors = {
            "line": accent,
            "fill": (*accent, 0.4 if self.style_manager.get_high_contrast() else 0.2),
            "text": (1.0, 1.0, 1.0) if is_dark else (0.0, 0.0, 0.0),
            "grid": (0.7, 0.7, 0.7) if is_dark else (0.3, 0.3, 0.3),
        }

        padding = 40
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        data = self._get_keystroke_data()

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

        for i in range(len(data)):
            x = padding + (i * graph_width / (len(data) - 1) if len(data) > 1 else 0)
            cr.set_source_rgba(*colors["grid"], 0.5)
            cr.move_to(x, padding)
            cr.line_to(x, height - padding)
            cr.stroke()

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

        self._draw_text(
            TextConfig(
                cr=cr,
                text="Daily Keystrokes",
                x=width / 2,
                y=padding - 20,
                font_size=14,
                font_weight=cairo.FONT_WEIGHT_BOLD,
                center=True,
            ),
            colors["text"],
        )

    def _get_accent_color(self, *, is_dark: bool) -> tuple:
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            accent = settings.get_string("accent-color")
            return {
                "blue": (0.2, 0.5, 0.9),
                "green": (0.3, 0.8, 0.2),
                "yellow": (0.9, 0.8, 0.2),
                "orange": (0.9, 0.6, 0.2),
                "red": (0.9, 0.2, 0.2),
                "magenta": (0.9, 0.2, 0.9),
                "purple": (0.7, 0.3, 0.9),
                "brown": (0.7, 0.5, 0.4),
                "gray": (0.5, 0.5, 0.5),
            }.get(accent, (0.3, 0.6, 1.0) if is_dark else (0.2, 0.5, 0.9))
        except Gio.Error:
            return (0.3, 0.6, 1.0) if is_dark else (0.2, 0.5, 0.9)

    def _get_keystroke_data(self) -> list[dict]:
        """Get daily keystroke data for the line chart using SQL queries."""
        data_points = self.keystroke_store.get_daily_keystroke_counts()

        if not data_points:
            return []

        latest_date = (
            datetime.fromisoformat(data_points[-1]["date"]).date()
            if data_points
            else datetime.now(timezone.utc).date()
        )

        all_days = {
            (latest_date - timedelta(days=6 - i)).isoformat(): {
                "date": (latest_date - timedelta(days=6 - i)).strftime("%b %d"),
                "count": 0,
            }
            for i in range(7)
        }

        for point in data_points:
            date = point["date"]
            if date in all_days:
                all_days[date]["count"] = point["count"]

        return [all_days[key] for key in sorted(all_days)]
