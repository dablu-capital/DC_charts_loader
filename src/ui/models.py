from abc import ABC
from typing import Any, Optional, Literal
from src.ui.utils import (
    plot_chart,
    plot_indicators,
    save_screenshot,
    save_screenshot_dual,
    on_maximize,
    on_timeframe_change,
    FULLSCREEN,
    CLOSE,
)
from src.models import ChartsData, ChartsMinuteData
from src.models import ChartsWMOverride as Chart


class ChartPlotter(ABC):
    """
    Abstract base class for chart plotters.
    This class defines the interface for plotting charts.
    """

    def __init__(self, chart_data: ChartsData, chart: Optional[Chart] = None):
        self.chart_data = chart_data
        self.chart = chart if chart is not None else Chart()
        self.drawing_ids = []

    def setup(self):
        """
        Set up the chart plotter.
        This method should be implemented by subclasses to define how the chart is set up.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def update_chart(self):
        """
        Update the chart with new data.
        This method should be implemented by subclasses to define how the chart is updated.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def clear_drawings(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def bind_hotkeys(self):
        """
        Bind hotkeys for chart navigation and actions.
        This method should be implemented by subclasses to define the hotkeys.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class SingleChartPlotter(ChartPlotter):
    """
    Concrete implementation of ChartPlotter for single chart setup.
    This class handles the setup and plotting of a single chart.
    """

    def setup(self):
        df, metadata = self.chart_data.load_chart(0)
        drawing_list = plot_chart(df, metadata, self.chart)
        self.drawing_ids = self.drawing_ids + drawing_list
        self.chart.legend(
            visible=True,
            ohlc=True,
            lines=True,
            font_family="arial",
            font_size=12,
            percent=False,
        )
        plot_indicators(df, self.chart)
        self.chart.price_line(line_visible=False)
        self.bind_hotkeys()

    def update_chart(self, direction: Optional[Literal["previous", "next"]] = "next"):
        """
        Update the chart with new data based on the direction.
        Args:
            direction (str): 'next' to load next chart, 'previous' to load previous chart.
        """
        self.clear_drawings()
        if direction == "previous":
            df, metadata = self.chart_data.previous_chart()
        else:
            df, metadata = self.chart_data.next_chart()

        drawing_list = plot_chart(df, metadata, self.chart)
        self.drawing_ids = drawing_list

    def clear_drawings(self):
        """
        Clears the current drawing IDs.
        """
        if len(self.drawing_ids) == 0:
            return
        for drawing in self.drawing_ids:
            drawing.delete()

    def bind_hotkeys(self) -> None:
        """
        Bind hotkeys for chart navigation and actions.
        """
        # self.chart.bind("up", lambda: self.update_chart("next"))
        self.chart.hotkey("shift", 1, func=lambda _: self.update_chart("next"))

        self.chart.hotkey(
            "shift",
            2,
            func=lambda _: self.update_chart("previous"),
        )

        self.chart.hotkey(
            "shift",
            "S",
            func=lambda _: save_screenshot(self.chart, self.chart_data),
        )


class DualChartPlotter(ChartPlotter):
    """
    Concrete implementation of ChartPlotter for dual chart setup.
    This class handles the setup and plotting of two charts side by side.
    """

    def __init__(
        self,
        chart_data: ChartsData,
        chart2_data: Optional[ChartsMinuteData] = None,
    ):
        self.chart_data = chart_data
        if chart2_data is None:
            min_filename = chart_data.dict_filename.with_name(
                chart_data.dict_filename.stem.replace(".feather", "")
                + "_min_data.feather"
            )
            self.chart2_data = ChartsMinuteData(chart_data.dict_filename, min_filename)
        else:
            self.chart2_data = chart2_data
        self.chart = Chart(inner_width=0.5, inner_height=1.0)
        self.right_chart = self.chart.create_subchart(
            position="right", width=0.5, height=1.0
        )
        self.drawing_ids = []

        print(f"initalization")
        print(
            f"chart_data dict: {self.chart_data.dict_filename} data {self.chart_data.data_filename}"
        )
        print(
            f"chart2_data  dict: {self.chart2_data.dict_filename} data {self.chart2_data.data_filename}"
        )
        print(f"chart: {self.chart}")

    def setup(self) -> None:
        """
        Set up the dual chart plotter.
        This method initializes both charts and plots the initial data.
        """
        charts = [self.chart, self.right_chart]
        chart_data_list = [self.chart_data, self.chart2_data]
        timeframes = ["1m", "5m", "15m", "1h", "1D", "4H", "1H", "15M", "5M", "1M"]
        for i, (chart_, chart_data_) in enumerate(zip(charts, chart_data_list)):
            chart_number = str(i + 1)

            # Load initial data
            df, metadata = chart_data_.load_chart(0)
            drawing_list = plot_chart(df, metadata, self.chart)
            plot_indicators(df, self.chart)
            self.drawing_ids = self.drawing_ids + drawing_list

            # Add chart identifier
            chart_.topbar.textbox("number", f"Chart {chart_number}")

            # Add maximize/minimize button
            chart_.topbar.button(
                "max",
                FULLSCREEN,
                False,
                align="right",
                func=lambda target_chart=chart_: on_maximize(target_chart, charts),
            )

            # Determine default timeframe based on chart data type
            print(f"chart {chart_number} timeframe {chart_data_.current_timeframe}")
            default_timeframe = (
                "1m" if hasattr(chart_data_, "current_timeframe") else "1D"
            )

            # Add timeframe selector
            chart_.topbar.switcher(
                "timeframe",
                options=timeframes,
                default=default_timeframe,
                align="right",
                func=lambda timeframe, target_chart=chart_, target_data=self.chart_data: on_timeframe_change(
                    target_chart, target_data, timeframe
                ),
            )

            # Add separator
            chart_.topbar.textbox("sep", " | ", align="right")
        self.bind_hotkeys()

    def update_chart(
        self, direction: Optional[Literal["previous", "next"]] = "next"
    ) -> None:
        """
        Update both charts with new data based on the direction.
        Args:
            direction (str): 'next' to load next chart, 'previous' to load previous chart.
        """
        self.clear_drawings()
        if direction == "previous":
            df, metadata = self.chart_data.previous_chart()
            df2, metadata2 = self.chart2_data.previous_chart()
        else:
            df, metadata = self.chart_data.next_chart()
            df2, metadata2 = self.chart2_data.next_chart()

        drawing_list1 = plot_chart(df, metadata, self.chart)
        drawing_list2 = plot_chart(df2, metadata2, self.right_chart)
        self.drawing_ids = drawing_list1 + drawing_list2

    def clear_drawings(self):
        """
        Clears the current drawing IDs.
        """
        if len(self.drawing_ids) == 0:
            return
        for drawing in self.drawing_ids:
            drawing.delete()

    def bind_hotkeys(self) -> None:
        self.chart.hotkey("shift", 1, func=lambda _: self.update_chart("next"))

        self.chart.hotkey(
            "shift",
            2,
            func=lambda _: self.update_chart("previous"),
        )
        self.chart.hotkey(
            "shift",
            "S",
            func=lambda _: save_screenshot_dual(
                self.chart, self.right_chart, self.chart_data, self.chart2_data
            ),
        )
