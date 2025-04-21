"""The statistics page displays keystroke data in various graphs/diagrams."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from gi.repository import Gtk

from typetrace.controller.utils.chart_utils import LineChart, PieChart

if TYPE_CHECKING:
    from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/statistics.ui")
class Statistics(Gtk.Box):
    """The statistics page displays keystroke data in various graphs/diagrams."""

    __gtype_name__ = "Statistics"
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

        # Initialize charts
        self.line_chart = LineChart(self.drawing_area, self._get_keystroke_data)
        self.pie_chart = PieChart(self.line_drawing_area, self._get_top_keystrokes)

        # Setup UI controls
        self.bar_count_spin.set_range(1, 10)
        self.bar_count_spin.set_value(5)
        self.bar_count_spin.connect(
            "value-changed",
            lambda _: self.pie_chart.update(),
        )
        self.clear_date_button.connect("clicked", self._clear_date)
        self.calendar.connect("day-selected", self._date_selected)
        self.clear_date_button.set_sensitive(False)

    def update(self) -> None:
        """Queue a redraw of the statistics drawing areas."""
        self.line_chart.update()
        self.pie_chart.update()

    def _clear_date(self, _button: Gtk.Button) -> None:
        self.selected_date = None
        self.clear_date_button.set_sensitive(False)
        self.date_button.set_label("Select Date")
        self.pie_chart.update()

    def _date_selected(self, calendar: Gtk.Calendar) -> None:
        self.selected_date = calendar.get_date().format("%Y-%m-%d")
        self.date_button.get_popover().popdown()
        self.clear_date_button.set_sensitive(True)
        self.date_button.set_label(self.selected_date)
        self.pie_chart.update()

    def _get_top_keystrokes(self) -> list:
        """Get the top keystrokes for the pie chart.

        Returns:
            The list of top keystrokes ordered by count

        """
        keystrokes = (
            self.keystroke_store.get_keystrokes_by_date(self.selected_date)
            if self.selected_date
            else self.keystroke_store.get_all_keystrokes()
        )
        return sorted(keystrokes, key=lambda k: k.count, reverse=True)[
            : int(self.bar_count_spin.get_value())
        ]

    def _get_keystroke_data(self) -> list[dict]:
        """Get daily keystroke data for the line chart using SQL queries.

        Returns:
            A list of data points with date and count values

        """
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
