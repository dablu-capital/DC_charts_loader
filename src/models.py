from abc import ABC
import pandas as pd
from typing import Union, Optional
from datetime import datetime, time
from .data import (
    load_daily_data,
    load_daily_df,
    apply_indicators,
    load_min_data,
    load_min_chart,
)
from lightweight_charts import Chart


class ChartsWMOverride(Chart):
    def watermark(
        self,
        text: str,
        font_size: int = 44,
        color: str = "rgba(180, 180, 200, 0.5)",
        horz_align: str = "center",
        vert_align: str = "center",
    ) -> None:
        """
        Adds a watermark to the chart. CUSTOM_OVERRIDE to allow for vertical alignment.
        """
        self.run_script(
            f"""
          {self.id}.chart.applyOptions({{
              watermark: {{
                  visible: true,
                  fontSize: {font_size},
                  horzAlign: '{horz_align}',
                  vertAlign: '{vert_align}',
                  color: '{color}',
                  text: '{text}',
              }}
          }})"""
        )

    def add_trading_session_shading(
        self,
        df: pd.DataFrame,
        premarket_color: str = "rgba(255, 255, 0, 0.2)",
        aftermarket_color: str = "rgba(255, 165, 0, 0.2)",
    ) -> None:
        """
        Adds visual indicators for premarket (before 9:30 AM) and aftermarket (after 4:00 PM) trading sessions.
        
        Args:
            df: DataFrame with 'time' column in format 'YYYY-MM-DD HH:MM:SS'
            premarket_color: Color for premarket indicators (before 9:30 AM)
            aftermarket_color: Color for aftermarket indicators (after 4:00 PM)
        """
        if df.empty or 'time' not in df.columns:
            return
        
        # Parse times and identify market sessions
        df_copy = df.copy()
        df_copy['datetime'] = pd.to_datetime(df_copy['time'])
        df_copy['time_only'] = df_copy['datetime'].dt.time
        
        # Define market hours (9:30 AM to 4:00 PM ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        # Find continuous premarket periods
        premarket_mask = df_copy['time_only'] < market_open
        if premarket_mask.any():
            premarket_times = df_copy[premarket_mask]['time'].tolist()
            if premarket_times:
                # Create vertical span for premarket period
                start_time = premarket_times[0]
                end_time = premarket_times[-1]
                self.vertical_span(start_time, end_time, color=premarket_color)
        
        # Find continuous aftermarket periods
        aftermarket_mask = df_copy['time_only'] >= market_close
        if aftermarket_mask.any():
            aftermarket_times = df_copy[aftermarket_mask]['time'].tolist()
            if aftermarket_times:
                # Create vertical span for aftermarket period
                start_time = aftermarket_times[0]
                end_time = aftermarket_times[-1]
                self.vertical_span(start_time, end_time, color=aftermarket_color)


class ChartsData(ABC):
    def __init__(self, charts):
        self.charts = charts
        self.current_index = 0

    def set_index(self, index):
        self.current_index = index

    def increase_index(self):
        if self.current_index < len(self.charts) - 1:
            self.current_index += 1
        else:
            self.current_index = 0  # wrap around to the first chart
        return self.current_index

    def decrease_index(self):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.charts) - 1
            # wrap around to the last chart
        return self.current_index

    def next_chart(self):
        return self.load_chart(self.increase_index())

    def previous_chart(self):
        return self.load_chart(self.decrease_index())

    def load_chart(self, index: Optional[int] = None):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_metadata(self, index: int) -> dict:
        raise NotImplementedError("This method should be implemented by subclasses.")


class ChartsDailyData(ChartsData):
    def __init__(self, dict_filename, data_filename):
        self.charts = pd.DataFrame()
        self.current_index = 0
        self.dict_filename = dict_filename
        self.data_filename = data_filename
        self.load_dict()
        self.load_data()

    def load_dict(self):
        self.charts = load_daily_df(self.dict_filename)
        self.charts.sort_values(by="date", ascending=False, inplace=True)

    def load_data(self):
        self.data = load_daily_df(self.data_filename)
        self.data = apply_indicators(self.data)

    def get_metadata(self, index: int) -> dict:
        ticker = self.charts.ticker.iloc[index]
        date = self.charts.date.iloc[index]
        return {
            "ticker": ticker,
            "date_str": date.strftime("%Y-%m-%d"),
            "date": date,
            "timeframe": "1D",
            "index": index,
        }

    def load_chart(self, index: Optional[int] = None) -> tuple[pd.DataFrame, dict]:
        if index is None:
            index = self.current_index

        metadata = self.get_metadata(index)

        ticker = metadata["ticker"]
        date = metadata["date"]
        df = load_daily_data(ticker, date, self.data)
        return df, metadata


class ChartsMinuteData(ChartsData):
    def __init__(self, dict_filename, data_filename):
        self.charts = pd.DataFrame()
        self.current_index = 0
        self.dict_filename = dict_filename
        self.data_filename = data_filename
        self.current_timeframe = "1m"
        self.load_dict()
        self.load_data()

    def load_dict(self):
        self.charts = load_daily_df(self.dict_filename)
        self.charts.sort_values(by="date", ascending=False, inplace=True)

    def load_data(self):
        # self.data = load_daily_df(self.data_filename)
        # self.data = apply_indicators(self.data)
        self.data = load_min_data(self.data_filename)

    def set_timeframe(self, timeframe: str):
        """Set the current timeframe for display purposes."""
        self.current_timeframe = timeframe

    def get_metadata(self, index: int) -> dict:
        ticker = self.charts.ticker.iloc[index]
        date = self.charts.date.iloc[index]
        return {
            "ticker": ticker,
            "date_str": date.strftime("%Y-%m-%d"),
            "date": date,
            "timeframe": self.current_timeframe,
            "index": index,
        }

    def load_chart(self, index: Optional[int] = None) -> tuple[pd.DataFrame, dict]:
        if index is None:
            index = self.current_index

        metadata = self.get_metadata(index)

        ticker = metadata["ticker"]
        date = metadata["date"]
        df = load_min_chart(ticker, date, self.data)
        return df, metadata
