from .models import ChartsData, ChartsMinuteData
from .models import ChartsWMOverride as Chart
from .config import config
import pandas as pd
from typing import Optional, List, Any
import os
from lightweight_charts.drawings import Box
from pathlib import Path

# ASCII symbols for maximize/minimize buttons
FULLSCREEN = "⬜"
CLOSE = "×"


def on_up(chart: Chart, chart_data: ChartsData):
    df, metadata = chart_data.next_chart()
    plot_chart(df, metadata, chart)


def on_down(chart: Chart, chart_data: ChartsData):
    df, metadata = chart_data.previous_chart()
    plot_chart(df, metadata, chart)


def plot_chart(df: pd.DataFrame, metadata: dict, chart: Chart) -> None:
    """
    Plots the chart using the provided chart data.
    :param chart: The Chart object to plot data on.
    :param chart_data: The ChartsData object containing the data.
    """
    chart.set(df)

    try:
        # Try to use custom watermark with vert_align (for ChartsWMOverride)
        chart.watermark(
            f"{metadata['ticker']} {metadata['timeframe']} {metadata['date_str']}",
            vert_align="top",
        )
    except (AttributeError, TypeError):
        # Fallback to standard watermark (for regular Chart or subcharts)
        try:
            chart.watermark(
                f"{metadata['ticker']} {metadata['timeframe']} {metadata['date_str']}",
            )
        except:
            chart.watermark("na")
    chart.legend(
        visible=True,
        ohlc=True,
        lines=True,
        font_family="arial",
        font_size=12,
        percent=False,
    )
    chart.price_line(line_visible=False)


def plot_sessions(
    df: pd.DataFrame,
    chart: Chart,
    premarket_color: str = "rgba(255, 255, 255, 0.5)",
    aftermarket_color: str = "rgba(255, 255, 0, 0.5)",
) -> List[Any]:

    drawing_ids = []

    if df.empty or "time" not in df.columns:
        return drawing_ids
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    pm_df = df.between_time("00:00", "09:30", inclusive="left").copy()
    am_df = df.between_time("16:00", "00:00", inclusive="left").copy()
    pm_times = _box_values(pm_df)
    am_times = _box_values(am_df)

    pm_settings = [(start, end, premarket_color) for start, end in pm_times]
    am_settings = [(start, end, aftermarket_color) for start, end in am_times]
    settings = pm_settings + am_settings

    start_value = df.low.min()
    end_value = df.high.max()

    if len(settings) == 0:
        return drawing_ids

    for setting in settings:
        start_time, end_time, fill_color = setting
        box_data = chart.box(
            start_time=start_time,
            end_time=end_time,
            start_value=start_value,
            end_value=end_value,
            width=0,
            fill_color=fill_color,
        )
        drawing_ids.append(box_data.id)

    return drawing_ids


def _box_values(df: pd.DataFrame) -> list:
    """
    Extracts start and end times for each day in the DataFrame.
    Args:
        df (pd.DataFrame): DataFrame with a datetime index.
    Returns:
        list: List of tuples containing start and end times for each day.
    """
    times_list = []
    df_grouped = df.groupby(df.index.date)
    for group in df_grouped:
        group_df = group[1]
        start_time = group_df.index[0]
        end_time = group_df.index[-1]
        times_list.append((start_time, end_time))
    return times_list


def plot_line(data: pd.DataFrame, chart: Chart, name: str) -> None:

    line = chart.create_line(name=name, price_line=False)
    line.set(data)


def save_screenshot(chart: Chart, chart_data: ChartsData, folder="screenshots") -> None:

    img = chart.screenshot()
    metadata = chart_data.get_metadata(chart_data.current_index)
    filename = f"{folder}/{metadata['ticker']}_{metadata['date_str']}_screenshot.png"
    with open(filename, "wb") as f:
        f.write(img)
    print(f"Screenshot saved to {filename}")


class ChartPlotter:
    def __init__(self, chart_data: ChartsData, chart: Optional[Chart] = None):
        self.chart_data = chart_data
        self.chart = chart if chart is not None else Chart()
        self.drawing_ids = []
        print(f"chart plotter initialized")

    def setup(self) -> None:
        df, metadata = self.chart_data.load_chart(0)
        plot_chart(df, metadata, self.chart)
        plot_indicators(df, self.chart)
        if metadata.get("timeframe") == "1m" and config.chart.show_session_shading:
            self.clear_drawings()
            print(f"drawings cleared")
            drawing_list = plot_sessions(df, self.chart)
            print(f"session shading drawn. {len(drawing_list)} drawings created")
            self.drawing_ids = self.drawing_ids + drawing_list
        bind_hotkeys(self)

    def clear_drawings(self):
        """
        Clears the current drawing IDs.
        """
        if len(self.drawing_ids) == 0:
            return
        for drawing in self.drawing_ids:
            drawing.delete()


def bind_hotkeys(chart_plotter: ChartPlotter) -> None:
    chart_plotter.chart.hotkey(
        "shift", 1, func=lambda _: on_up(chart_plotter.chart, chart_plotter.chart_data)
    )
    chart_plotter.chart.hotkey(
        "shift",
        2,
        func=lambda _: on_down(chart_plotter.chart, chart_plotter.chart_data),
    )
    chart_plotter.chart.hotkey(
        "shift",
        "S",
        func=lambda _: save_screenshot(chart_plotter.chart, chart_plotter.chart_data),
    )


class DualChartPlotter:
    def __init__(
        self,
        chart_data1: ChartsData,
        chart_data2: Optional[ChartsMinuteData] = None,
    ):
        self.chart_data1 = chart_data1
        if chart_data2 is None:
            min_filename = chart_data1.dict_filename.with_name(
                chart_data1.dict_filename.stem.replace(".feather", "")
                + "_min_data.feather"
            )
            chart_data2 = ChartsMinuteData(chart_data1.dict_filename, min_filename)
        self.chart_data2 = chart_data2
        self.chart = Chart(inner_width=0.5, inner_height=1.0)
        self.right_chart = self.chart.create_subchart(
            position="right", width=0.5, height=1.0
        )
        self.drawing_ids = []

    def setup(self) -> None:
        charts = [self.chart, self.right_chart]
        chart_data_list = [self.chart_data1, self.chart_data2]
        timeframes = ["1m", "5m", "15m", "1h", "1D", "4H", "1H", "15M", "5M", "1M"]
        for i, (chart, chart_data) in enumerate(zip(charts, chart_data_list)):
            chart_number = str(i + 1)

            # Load initial data
            df, metadata = chart_data.load_chart(0)
            plot_chart(df, metadata, chart)
            plot_indicators(df, chart)
            if metadata.get("timeframe") == "1m" and config.chart.show_session_shading:
                self.clear_drawings()
                print(f"drawings cleared for chart {chart_number}")
                drawing_list = plot_sessions(df, chart)
                print(
                    f"session shading drawn for chart {chart_number}. {len(drawing_list)} drawings created"
                )
                self.drawing_ids.extend(drawing_list)

            # Add chart identifier
            chart.topbar.textbox("number", f"Chart {chart_number}")

            # Add maximize/minimize button
            chart.topbar.button(
                "max",
                FULLSCREEN,
                False,
                align="right",
                func=lambda target_chart=chart: on_maximize(target_chart, charts),
            )

            # Determine default timeframe based on chart data type
            default_timeframe = (
                "1m" if hasattr(chart_data, "current_timeframe") else "1D"
            )

            # Add timeframe selector
            chart.topbar.switcher(
                "timeframe",
                options=timeframes,
                default=default_timeframe,
                align="right",
                func=lambda timeframe, target_chart=chart, target_data=chart_data: on_timeframe_change(
                    target_chart, target_data, timeframe
                ),
            )

            # Add separator
            chart.topbar.textbox("sep", " | ", align="right")
        dual_bind_hotkeys(self)

    def clear_drawings(self):
        """
        Clears the current drawing IDs.
        """
        if len(self.drawing_ids) == 0:
            return
        for drawing in self.drawing_ids:
            drawing.delete()
        self.drawing_ids = []


def dual_bind_hotkeys(chart_plotter: DualChartPlotter) -> None:
    chart_plotter.chart.hotkey(
        "shift",
        1,
        func=lambda _: on_up_dual(chart_plotter

        ),
    )
    chart_plotter.chart.hotkey(
        "shift",
        2,
        func=lambda _: on_down_dual(
            chart_plotter.chart,
            chart_plotter.right_chart,
            chart_plotter.chart_data1,
            chart_plotter.chart_data2,
        ),
    )
    chart_plotter.chart.hotkey(
        "shift",
        "S",
        func=lambda _: save_screenshot_dual(
            chart_plotter.chart,
            chart_plotter.right_chart,
            chart_plotter.chart_data1,
            chart_plotter.chart_data2,
        ),
    )


def plot_indicators(df: pd.DataFrame, chart: Chart) -> None:
    """
    Plots indicators on the chart.
    :param df: DataFrame containing the data with indicators.
    :param chart: The Chart object to plot indicators on.
    """
    indicators_list = config.indicators if config.indicators is not None else []
    for indicator in indicators_list:
        if indicator.name == "SMA":
            if indicator.parameters is not None and "period" in indicator.parameters:
                period = indicator.parameters["period"]
                col_name = f"SMA_{period}"
                if col_name in df.columns:
                    plot_line(df[["date", col_name]], chart, col_name)


def on_maximize(target_chart, charts):
    """
    Handles maximize/minimize functionality for charts.
    """
    button = target_chart.topbar["max"]
    if button.value == CLOSE:
        # Restore to side-by-side view
        for chart in charts:
            chart.resize(0.5, 1.0)
        button.set(FULLSCREEN)
    else:
        # Maximize target chart
        for chart in charts:
            width = 1.0 if chart == target_chart else 0.0
            chart.resize(width, 1.0)
        button.set(CLOSE)


def on_timeframe_change(chart, chart_data, timeframe):
    """
    Handles timeframe switching for a chart.
    """
    # Store current timeframe in chart metadata
    if not hasattr(chart, "_timeframe"):
        chart._timeframe = "1D"

    chart._timeframe = timeframe

    # For ChartsMinuteData, update the timeframe setting
    if hasattr(chart_data, "set_timeframe"):
        chart_data.set_timeframe(timeframe)

    # Reload current chart with new timeframe
    df, metadata = chart_data.load_chart(chart_data.current_index)
    if not hasattr(chart_data, "set_timeframe"):
        metadata["timeframe"] = timeframe
    plot_chart(df, metadata, chart)


# def on_up_dual(chart1, chart2, chart_data1, chart_data2):
#     """Navigate to next chart for dual chart setup."""
#     df1, metadata1 = chart_data1.next_chart()
#     plot_chart(df1, metadata1, chart1)

#     df2, metadata2 = chart_data2.next_chart()
#     plot_chart(df2, metadata2, chart2)
def on_up_dual(chart_plotter: DualChartPlotter):
    

def on_down_dual(chart1, chart2, chart_data1, chart_data2):
    """Navigate to previous chart for dual chart setup."""
    df1, metadata1 = chart_data1.previous_chart()
    plot_chart(df1, metadata1, chart1)

    df2, metadata2 = chart_data2.previous_chart()
    plot_chart(df2, metadata2, chart2)


def save_screenshot_dual(
    chart1, chart2, chart_data1, chart_data2, folder="screenshots"
):
    """Save screenshots for both charts."""
    # Save screenshot for chart 1
    img1 = chart1.screenshot()
    metadata1 = chart_data1.get_metadata(chart_data1.current_index)
    filename1 = (
        f"{folder}/{metadata1['ticker']}_{metadata1['date_str']}_chart1_screenshot.png"
    )
    with open(filename1, "wb") as f:
        f.write(img1)

    # Save screenshot for chart 2
    img2 = chart2.screenshot()
    metadata2 = chart_data2.get_metadata(chart_data2.current_index)
    filename2 = (
        f"{folder}/{metadata2['ticker']}_{metadata2['date_str']}_chart2_screenshot.png"
    )
    with open(filename2, "wb") as f:
        f.write(img2)

    print(f"Screenshots saved to {filename1} and {filename2}")


def create_dual_chart_grid(
    chart_data1: ChartsData, chart_data2: Optional[ChartsMinuteData] = None
) -> Chart:
    """
    Creates a grid of 2 charts side by side with timeframe switching and maximize/minimize functionality.

    Args:
        chart_data1 (ChartsData): Data for the left chart
        chart_data2 (ChartsData): Data for the right chart (optional, defaults to minute data)

    Returns:
        Chart: The main chart object with dual chart setup

    Features:
        - Side-by-side layout (50% width each)
        - Left chart: uses provided data
        - Right chart: automatically loads minute data from files ending with "_min.feather"
        - Maximize/minimize buttons for each chart
        - Timeframe switching (1D, 4H, 1H, 15M, 5M, 1M)
        - Navigation hotkeys (Shift+1/2 for next/previous)
        - Screenshot functionality (Shift+S)
    """
    # Create minute data for right chart if not provided
    if chart_data2 is None:
        # Find the minute data file by replacing the data filename
        if hasattr(chart_data1, "data_filename"):
            base_path = Path(chart_data1.data_filename).parent
            base_name = Path(chart_data1.data_filename).name
            # Replace with _min.feather version
            if base_name.endswith(".feather"):
                min_filename = base_name.replace("_data.feather", "_min_data.feather")
            else:
                min_filename = base_name + "_min_data.feather"
            min_data_path = os.path.join(base_path, min_filename)

            # Create ChartsMinuteData instance
            chart_data2 = ChartsMinuteData(chart_data1.dict_filename, min_data_path)
        else:
            raise ValueError(
                "chart_data1 must have a data_filename attribute to create minute data."
            )

    # Create main chart (left side) using custom Chart class
    chart = Chart(inner_width=0.5, inner_height=1.0)

    # Create subchart (right side)
    right_chart = chart.create_subchart(position="right", width=0.5, height=1.0)

    charts = [chart, right_chart]
    chart_data_list = [chart_data1, chart_data2]

    # Available timeframes
    timeframes = ["1m", "5m", "15m", "1h", "1D", "4H", "1H", "15M", "5M", "1M"]

    # Setup each chart
    for i, (chart, chart_data) in enumerate(zip(charts, chart_data_list)):
        chart_number = str(i + 1)

        # Load initial data
        df, metadata = chart_data.load_chart(0)
        plot_chart(df, metadata, chart)
        plot_indicators(df, chart)
        if metadata.get("timeframe") == "1m" and config.chart.show_session_shading:
            plot_sessions(df, chart)

        # Add chart identifier
        chart.topbar.textbox("number", f"Chart {chart_number}")

        # Add maximize/minimize button
        chart.topbar.button(
            "max",
            FULLSCREEN,
            False,
            align="right",
            func=lambda target_chart=chart: on_maximize(target_chart, charts),
        )

        # Determine default timeframe based on chart data type
        default_timeframe = "1m" if hasattr(chart_data, "current_timeframe") else "1D"

        # Add timeframe selector
        chart.topbar.switcher(
            "timeframe",
            options=timeframes,
            default=default_timeframe,
            align="right",
            func=lambda timeframe, target_chart=chart, target_data=chart_data: on_timeframe_change(
                target_chart, target_data, timeframe
            ),
        )

        # Add separator
        chart.topbar.textbox("sep", " | ", align="right")

    # Bind global hotkeys to main chart
    chart.hotkey(
        "shift",
        1,
        func=lambda _: on_up_dual(chart, right_chart, chart_data1, chart_data2),
    )
    chart.hotkey(
        "shift",
        2,
        func=lambda _: on_down_dual(chart, right_chart, chart_data1, chart_data2),
    )
    chart.hotkey(
        "shift",
        "S",
        func=lambda _: save_screenshot_dual(
            chart, right_chart, chart_data1, chart_data2
        ),
    )

    return chart
