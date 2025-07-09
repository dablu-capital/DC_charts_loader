from abc import ABC
import pandas as pd
from typing import Optional
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
        self.current_timeframe = "1D"

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

        print(f"metadata for daily chart: {metadata}")

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
        self.current_timeframe = "1m"

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
        print(f"metadata for min chart: {metadata}")
        return df, metadata
