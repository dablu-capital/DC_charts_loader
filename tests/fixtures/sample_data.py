"""
Sample data fixtures for testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any


def create_sample_stock_data(
    tickers: list = None,
    start_date: str = "2023-01-01",
    periods: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Create sample stock data for testing.

    Args:
        tickers: List of ticker symbols. Defaults to ['AAPL', 'MSFT']
        start_date: Start date for the data
        periods: Number of days of data to generate
        seed: Random seed for reproducible data

    Returns:
        DataFrame with stock data
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT"]

    np.random.seed(seed)
    dates = pd.date_range(start_date, periods=periods, freq="D")

    data = []
    for ticker in tickers:
        # Generate realistic stock prices
        base_price = np.random.uniform(100, 300)
        prices = []
        current_price = base_price

        for _ in range(periods):
            # Random walk with slight upward bias
            change = np.random.normal(0.001, 0.02)  # 0.1% daily return, 2% volatility
            current_price *= 1 + change
            prices.append(current_price)

        for i, date in enumerate(dates):
            price = prices[i]
            # Generate OHLC data
            high = price * np.random.uniform(1.0, 1.05)
            low = price * np.random.uniform(0.95, 1.0)
            open_price = np.random.uniform(low, high)
            close_price = price
            volume = np.random.randint(100000, 10000000)

            data.append(
                {
                    "ticker": ticker,
                    "date": date,
                    "open": np.float32(open_price),
                    "high": np.float32(high),
                    "low": np.float32(low),
                    "close": np.float32(close_price),
                    "volume": volume,
                    "adjusted": False,
                    "type": "CS",
                }
            )

    return pd.DataFrame(data)


def create_sample_config_data() -> Dict[str, Any]:
    """
    Create sample configuration data for testing.

    Returns:
        Dictionary with configuration data
    """
    return {
        "general": {
            "version": "1.0.0",
            "data_path": "./data",
            "data_filename": "test_data.feather",
        },
        "chart": {"use_intraday_tf": False, "intraday_tf": "1m"},
        "indicators": [
            {"name": "SMA", "parameters": {"period": 20, "source": "close"}},
            {"name": "SMA", "parameters": {"period": 50, "source": "close"}},
        ],
    }


def create_sample_charts_data(
    num_charts: int = 5, start_date: str = "2023-01-01"
) -> pd.DataFrame:
    """
    Create sample charts dictionary data for testing.

    Args:
        num_charts: Number of chart entries to create
        start_date: Start date for the charts

    Returns:
        DataFrame with chart metadata
    """
    np.random.seed(42)
    dates = pd.date_range(start_date, periods=num_charts, freq="D")
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

    data = []
    for i in range(num_charts):
        ticker = np.random.choice(tickers)
        date = dates[i]

        # Generate sample OHLC data
        base_price = np.random.uniform(100, 300)
        data.append(
            {
                "ticker": ticker,
                "date": date,
                "open": np.float32(base_price * np.random.uniform(0.98, 1.02)),
                "high": np.float32(base_price * np.random.uniform(1.02, 1.08)),
                "low": np.float32(base_price * np.random.uniform(0.92, 0.98)),
                "close": np.float32(base_price),
                "volume": np.random.randint(1000000, 50000000),
            }
        )

    return pd.DataFrame(data)


def create_sample_indicator_data(
    base_data: pd.DataFrame, indicators: list = None
) -> pd.DataFrame:
    """
    Add sample indicator data to existing DataFrame.

    Args:
        base_data: Base DataFrame with OHLC data
        indicators: List of indicators to add. Defaults to ['SMA_20', 'SMA_50']

    Returns:
        DataFrame with indicator columns added
    """
    if indicators is None:
        indicators = ["SMA_20", "SMA_50"]

    df = base_data.copy()

    # Group by ticker to calculate indicators separately
    for ticker in df["ticker"].unique():
        ticker_mask = df["ticker"] == ticker
        ticker_data = df[ticker_mask].copy()
        ticker_data = ticker_data.sort_values("date")

        for indicator in indicators:
            if indicator.startswith("SMA_"):
                period = int(indicator.split("_")[1])
                sma_values = ticker_data["close"].rolling(window=period).mean()
                df.loc[ticker_mask, indicator] = sma_values.values

    return df


def create_sample_min_data(
    tickers: list = None,
    start_datetime: str = "2023-01-15 09:30:00",
    periods: int = 100,
    freq: str = "1min",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Create sample minute-level stock data for testing.

    Args:
        tickers: List of ticker symbols. Defaults to ['AAPL', 'MSFT']
        start_datetime: Start datetime for the data
        periods: Number of minutes of data to generate
        freq: Frequency of data (e.g., '1min', '5min')
        seed: Random seed for reproducible data

    Returns:
        DataFrame with minute-level stock data
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT"]

    np.random.seed(seed)
    datetimes = pd.date_range(start_datetime, periods=periods, freq=freq)

    data = []
    for ticker in tickers:
        # Generate realistic stock prices
        base_price = np.random.uniform(100, 300)
        prices = []
        current_price = base_price

        for _ in range(periods):
            # Random walk with smaller changes for minute data
            change = np.random.normal(0.0001, 0.005)  # Smaller volatility for minute data
            current_price *= 1 + change
            prices.append(current_price)

        for i, dt in enumerate(datetimes):
            price = prices[i]
            # Generate OHLC data
            high = price * np.random.uniform(1.0, 1.01)
            low = price * np.random.uniform(0.99, 1.0)
            open_price = np.random.uniform(low, high)
            close_price = price
            volume = np.random.randint(100, 10000)

            data.append(
                {
                    "ticker": ticker,
                    "datetime": dt,
                    "open": np.float32(open_price),
                    "high": np.float32(high),
                    "low": np.float32(low),
                    "close": np.float32(close_price),
                    "volume": np.int32(volume),
                }
            )

    return pd.DataFrame(data)


# Pre-defined sample datasets for common test scenarios
SAMPLE_STOCK_DATA = create_sample_stock_data()
SAMPLE_CONFIG_DATA = create_sample_config_data()
SAMPLE_CHARTS_DATA = create_sample_charts_data()
