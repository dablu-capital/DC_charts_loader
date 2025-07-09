import pandas as pd
from typing import List, Any
from src.models import ChartsData, ChartsWMOverride as Chart
from src.config import config

# ASCII symbols for maximize/minimize buttons
FULLSCREEN = "⬜"
CLOSE = "×"


def plot_chart(df: pd.DataFrame, metadata: dict, chart: Chart) -> List[Any]:
    """
    Plot the chart with the given DataFrame and metadata.
    """
    set_chart(df, metadata, chart)
    plot_indicators(df, chart)
    drawing_list = []
    if metadata.get("timeframe") == "1m" and config.chart.show_session_shading:
        # print(f"drawings cleared")
        drawing_list = plot_sessions(df, chart)
        # print(f"session shading drawn. {len(drawing_list)} drawings created")
    return drawing_list


def set_chart(df: pd.DataFrame, metadata: dict, chart: Chart) -> None:
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


def save_screenshot_dual(
    chart1, chart2, chart_data1, chart_data2, folder="../screenshots"
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
