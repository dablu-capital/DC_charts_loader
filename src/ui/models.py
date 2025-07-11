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
        # watch_crosshair_moves(self.chart)
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
        self.chart = Chart(inner_width=0.5, inner_height=1.0, toolbox=True)
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
            
            # Add toolbox clear button for each chart
            chart_.topbar.button(
                "clear",
                button_text="❌",
                func=lambda chart: clear_drawings(chart),
            )
            
            # Add double-click tracker subscription for each chart
            subscribe_click(chart_, callback=on_chart_click2)
            
        # Add a unified clear measurements button on the main chart
        self.chart.topbar.button(
            "clear_distance",
            button_text="📏❌",
            func=lambda chart: double_click_tracker.clear_drawings(),
        )
        
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
        self.current_drawings: Dict[str, List[Any]] = {}
        self.charts_with_markers: Dict[str, Chart] = {}
        
    def set_chart(self, chart: Chart) -> None:
        """Set the chart instance for drawing markers."""
        self.chart = chart
        # Initialize drawings list for this chart if not exists
        if chart.id not in self.current_drawings:
            self.current_drawings[chart.id] = []
        # Keep track of charts that have markers
        self.charts_with_markers[chart.id] = chart
        
    def handle_click(self, data: Dict[str, Any], chart: Optional[Chart] = None) -> None:
        """
        Handle click events and calculate distance on second click.
        
        Args:
            data: Dictionary containing timestamp and price from click event
            chart: The specific chart instance that was clicked (optional, uses stored chart if not provided)
        """
        # Use the provided chart or fall back to stored chart
        active_chart = chart if chart is not None else self.chart
        if active_chart is None:
            logger.warning("No chart available for handling click")
            return
            
        # Ensure chart is tracked
        if active_chart.id not in self.current_drawings:
            self.current_drawings[active_chart.id] = []
        if active_chart.id not in self.charts_with_markers:
            self.charts_with_markers[active_chart.id] = active_chart
        
        self.click_count += 1
        
        if self.click_count == 1:
            # Store first click
            self.first_click = data
            logger.info(f"First click recorded at time: {data['timestamp']}, price: {data['price']}")
            print(f"First click: {data['timestamp']}, price: {data['price']}")
            
            # Add marker for first click on the specific chart that was clicked
            self._add_first_click_marker(data, active_chart)
            
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
            
            # Add visual markers to the specific chart that was clicked
            self._add_distance_markers(self.first_click, second_click, days_diff, price_diff, price_change_pct, active_chart)
            
            # Reset for next measurement
            self.reset()
            
    def _add_first_click_marker(self, data: Dict[str, Any], chart: Chart) -> None:
        """Add a marker for the first click."""
        try:
            # Create marker on the specific chart that was clicked
            chart.marker(
                time=data['timestamp'],
                position='below',
                shape='circle',
                color='blue',
                text='1'
            )
            # Note: markers will be cleared using chart.clear_markers()
        except Exception as e:
            logger.warning(f"Could not add first click marker: {e}")
            
    def _add_distance_markers(self, first_click: Dict[str, Any], second_click: Dict[str, Any], 
                             days_diff: float, price_diff: float, price_change_pct: float, chart: Chart) -> None:
        """Add visual markers showing the distance measurement."""
        try:
            # Add marker for second click on the specific chart that was clicked
            chart.marker(
                time=second_click['timestamp'],
                position='below',
                shape='circle',
                color='red',
                text='2'
            )
            
            # Create trend line connecting the two points - these can be deleted individually
            trend_line = chart.trend_line(
                start_time=first_click['timestamp'],
                start_value=first_click['price'],
                end_time=second_click['timestamp'],
                end_value=second_click['price']
            )
            self.current_drawings[chart.id].append(trend_line)
            
            # Add horizontal line at midpoint with distance info - these can be deleted individually
            mid_price = (first_click['price'] + second_click['price']) / 2
            info_text = f"Δ{days_diff:.1f}d | Δ${price_diff:.2f} | {price_change_pct:+.1f}%"
            
            info_line = chart.horizontal_line(
                price=mid_price,
                color='purple',
                width=1,
                style='dashed',
                text=info_text,
                axis_label_visible=True
            )
            self.current_drawings[chart.id].append(info_line)
            
        except Exception as e:
            logger.warning(f"Could not add distance markers: {e}")
            
    def clear_drawings(self) -> None:
        """Clear all current drawings from all charts."""
        # Clear markers from all charts that have them
        for chart_id, chart in self.charts_with_markers.items():
            try:
                chart.clear_markers()
            except Exception as e:
                logger.warning(f"Could not clear markers from chart {chart_id}: {e}")
        
        # Clear other drawing elements (lines, trend lines, etc.)
        for drawings in self.current_drawings.values():
            for drawing in drawings:
                try:
                    if hasattr(drawing, 'delete'):
                        drawing.delete()
                    elif hasattr(drawing, 'remove'):
                        drawing.remove()
                except Exception as e:
                    logger.warning(f"Could not remove drawing: {e}")
        
        # Reset the tracking dictionaries
        self.current_drawings = {}
        self.charts_with_markers = {}
            
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
        f"window.callbackFunction(`on_click_~_${chart.id}_~_${{data}}`);"
        "}"
        f"{chart.id}.chart.subscribeClick(clickHandler);"
    )

    def create_decorated_callback(target_chart):
        def decorated_callback(data):
            # add some preprocessing
            data = json.loads(data)
            data = {
                "timestamp": pd.to_datetime(data["time"], unit="s"),
                "price": data["price"],
            }
            return callback(data, target_chart)
        return decorated_callback

    chart.win.handlers[f"on_click_{chart.id}"] = create_decorated_callback(chart)
    chart.win.run_script(js)


def on_chart_click2(data, chart):
    """
    Enhanced callback function that handles double-click distance measurement.
    
    Args:
        data: Dictionary containing timestamp and price from click event
        chart: The chart instance for drawing markers
    """
    # print(data)
    # Use the double-click tracker to handle distance calculation
    # Pass the specific chart that was clicked to ensure markers are drawn on the correct chart
    logger.info(f"Handling click on chart {chart.id} with data: {data}")
    double_click_tracker.handle_click(data, chart)


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
