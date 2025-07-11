from abc import ABC
from typing import Any, Optional, Literal, Dict, List, Union
from src.ui.utils import (
    plot_chart,
    plot_indicators,
    save_screenshot,
    save_screenshot_dual,
    on_maximize,
    on_timeframe_change,
    clear_drawings,
    FULLSCREEN,
    CLOSE,
)
from src.models import ChartsData, ChartsMinuteData
from src.models import ChartsWMOverride as Chart
from src.logger import logger


class ChartPlotter(ABC):
    """
    Abstract base class for chart plotters.
    This class defines the interface for plotting charts.
    """

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

    def __init__(self, chart_data: ChartsData, chart: Optional[Chart] = None):
        self.chart_data = chart_data
        self.chart = chart if chart is not None else Chart(toolbox=True)
        self.drawing_ids = []

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
        # add a button that will clear all lines created with toolbox when clicked
        self.chart.topbar.button(
            "clear",
            button_text="❌",
            func=clear_drawings,
        )
        # add a button to clear distance markers
        self.chart.topbar.button(
            "clear_distance",
            button_text="📏❌",
            func=lambda chart: double_click_tracker.clear_drawings(),
        )
        # self.chart.events.click += on_chart_click
        watch_crosshair_moves(self.chart)
        subscribe_click(self.chart, callback=on_chart_click2)

        self.bind_hotkeys()

    def update_chart(self, direction: Optional[Literal["previous", "next"]] = "next"):
        """
        Update the chart with new data based on the direction.
        Args:
            direction (str): 'next' to load next chart, 'previous' to load previous chart.
        """
        self.clear_drawings()
        # Clear distance markers when changing charts
        double_click_tracker.clear_drawings()
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
            drawing_list = plot_chart(df, metadata, chart_)
            plot_indicators(df, chart_)
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
        # Clear distance markers when changing charts
        double_click_tracker.clear_drawings()
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


import json
import pandas as pd
from datetime import datetime, timedelta


class DoubleClickTracker:
    """
    Tracks double clicks on chart and calculates distance between two points.
    """
    def __init__(self):
        self.first_click: Optional[Dict[str, Any]] = None
        self.click_count: int = 0
        self.chart: Optional[Chart] = None
        self.current_drawings: List[Any] = []
        
    def set_chart(self, chart: Chart) -> None:
        """Set the chart instance for drawing markers."""
        self.chart = chart
        
    def handle_click(self, data: Dict[str, Any]) -> None:
        """
        Handle click events and calculate distance on second click.
        
        Args:
            data: Dictionary containing timestamp and price from click event
        """
        self.click_count += 1
        
        if self.click_count == 1:
            # Store first click
            self.first_click = data
            logger.info(f"First click recorded at time: {data['timestamp']}, price: {data['price']}")
            print(f"First click: {data['timestamp']}, price: {data['price']}")
            
            # Add marker for first click
            if self.chart:
                self._add_first_click_marker(data)
            
        elif self.click_count == 2 and self.first_click is not None:
            # Calculate distance on second click
            second_click = data
            logger.info(f"Second click recorded at time: {data['timestamp']}, price: {data['price']}")
            
            # Calculate time difference in days
            time_diff = abs((second_click['timestamp'] - self.first_click['timestamp']).total_seconds())
            days_diff = time_diff / (24 * 3600)  # Convert seconds to days
            
            # Calculate price difference and percentage
            price_diff = abs(second_click['price'] - self.first_click['price'])
            price_change_pct = ((second_click['price'] - self.first_click['price']) / self.first_click['price']) * 100
            
            # Log and print results
            logger.info(f"Distance calculation - Days: {days_diff:.2f}, Price difference: {price_diff:.2f}, Price change: {price_change_pct:.2f}%")
            print(f"Distance between clicks:")
            print(f"  Time difference: {days_diff:.2f} days")
            print(f"  Price difference: {price_diff:.2f}")
            print(f"  Price change: {price_change_pct:.2f}%")
            print(f"  First click: {self.first_click['timestamp']} at {self.first_click['price']}")
            print(f"  Second click: {second_click['timestamp']} at {second_click['price']}")
            
            # Add visual markers to chart
            if self.chart:
                self._add_distance_markers(self.first_click, second_click, days_diff, price_diff, price_change_pct)
            
            # Reset for next measurement
            self.reset()
            
    def _add_first_click_marker(self, data: Dict[str, Any]) -> None:
        """Add a marker for the first click."""
        if self.chart is None:
            return
        try:
            marker = self.chart.marker(
                time=data['timestamp'],
                position='below',
                shape='circle',
                color='blue',
                text='1'
            )
            self.current_drawings.append(marker)
        except Exception as e:
            logger.warning(f"Could not add first click marker: {e}")
            
    def _add_distance_markers(self, first_click: Dict[str, Any], second_click: Dict[str, Any], 
                             days_diff: float, price_diff: float, price_change_pct: float) -> None:
        """Add visual markers showing the distance measurement."""
        if self.chart is None:
            return
        try:
            # Add marker for second click
            marker2 = self.chart.marker(
                time=second_click['timestamp'],
                position='below',
                shape='circle',
                color='red',
                text='2'
            )
            self.current_drawings.append(marker2)
            
            # Create trend line connecting the two points
            trend_line = self.chart.trend_line(
                start_time=first_click['timestamp'],
                start_value=first_click['price'],
                end_time=second_click['timestamp'],
                end_value=second_click['price']
            )
            self.current_drawings.append(trend_line)
            
            # Add horizontal line at midpoint with distance info
            mid_price = (first_click['price'] + second_click['price']) / 2
            info_text = f"Δ{days_diff:.1f}d | Δ${price_diff:.2f} | {price_change_pct:+.1f}%"
            
            info_line = self.chart.horizontal_line(
                price=mid_price,
                color='purple',
                width=1,
                style='dashed',
                text=info_text,
                axis_label_visible=True
            )
            self.current_drawings.append(info_line)
            
        except Exception as e:
            logger.warning(f"Could not add distance markers: {e}")
            
    def clear_drawings(self) -> None:
        """Clear all current drawings from the chart."""
        for drawing in self.current_drawings:
            try:
                if hasattr(drawing, 'delete'):
                    drawing.delete()
                elif hasattr(drawing, 'remove'):
                    drawing.remove()
            except Exception as e:
                logger.warning(f"Could not remove drawing: {e}")
        self.current_drawings = []
            
    def reset(self) -> None:
        """Reset the tracker for new measurement."""
        self.first_click = None
        self.click_count = 0


# Global instance for tracking double clicks
double_click_tracker = DoubleClickTracker()


def on_chart_click(chart, time, price):
    """
    Callback function that gets called when chart is clicked

    Args:
        chart: The chart object that was clicked
        time: The time coordinate of the click (timestamp)
        price: The price coordinate of the click (numeric value)
    """
    logger.info(f"Chart clicked at time: {time}, price: {price}")
    logger.info(f"Chart ID: {chart.id}")
    return time, price


def subscribe_click(chart, *, callback):
    js = (
        "function clickHandler(param) {"
        "if (!param.point) {"
        "return;"
        "}"
        f"const time = {chart.id}.chart.timeScale().coordinateToTime(param.point.x);"
        f"const price = {chart.id}.series.coordinateToPrice(param.point.y);"
        "const data = JSON.stringify({time: time, price: price});"
        "window.callbackFunction(`on_click_~_${data}`);"
        "}"
        f"{chart.id}.chart.subscribeClick(clickHandler);"
    )

    def decorated_callback(data):
        # add some preprocessing
        data = json.loads(data)
        data = {
            "timestamp": pd.to_datetime(data["time"], unit="s"),
            "price": data["price"],
        }
        return callback(data, chart)

    chart.win.handlers["on_click"] = decorated_callback
    chart.win.run_script(js)


def on_chart_click2(data, chart):
    """
    Enhanced callback function that handles double-click distance measurement.
    
    Args:
        data: Dictionary containing timestamp and price from click event
        chart: The chart instance for drawing markers
    """
    print(data)
    # Set the chart instance in the tracker
    double_click_tracker.set_chart(chart)
    # Use the double-click tracker to handle distance calculation
    double_click_tracker.handle_click(data)


def watch_crosshair_moves(chart):
    chart.crosshair_position = {}

    def on_crosshair_move(point):
        # assigning a new field to an existing object is an anti-pattern
        # but here it's convenient (at least for my use case)
        new_position = json.loads(point)
        if chart.crosshair_position != new_position:
            chart.crosshair_position = new_position
            print(chart.crosshair_position)

    crosshair_script = (
        "function onCrosshairMove(param) {"
        "if (!param.point) {"
        "return;"
        "}"
        f"const time = {chart.id}.chart.timeScale().coordinateToTime(param.point.x);"
        f"const price = {chart.id}.series.coordinateToPrice(param.point.y);"
        "const data = JSON.stringify({time: time, price: price});"
        "window.callbackFunction(`on_crosshair_move_~_${data}`);"
        "}"
        f"{chart.id}.chart.subscribeCrosshairMove(onCrosshairMove);"
    )

    chart.win.handlers["on_crosshair_move"] = on_crosshair_move
    chart.win.run_script(crosshair_script)
