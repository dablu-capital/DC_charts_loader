from pandera.pandas import Column, DataFrameSchema, Check
from numpy import datetime64, float32
from typing import Union
from numpy import int32

dict_schema = DataFrameSchema(
    {
        "ticker": Column(str, nullable=False),
        "date": Column(datetime64, nullable=False),
        "open": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "high": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "low": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "close": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "volume": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
    },
    strict="filter",
)

min_schema = DataFrameSchema(
    {
        "ticker": Column(str, nullable=False),
        "datetime": Column(datetime64, nullable=False),
        "open": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "high": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "low": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "close": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "volume": Column(int32, Check.greater_than_or_equal_to(0), nullable=False),
        "_date": Column(datetime64, nullable=False),
    },
    strict="filter",
)

min_chart_schema = DataFrameSchema(
    {
        "ticker": Column(str, nullable=False),
        "time": Column(str, nullable=False),
        "open": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "high": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "low": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "close": Column(float32, Check.greater_than_or_equal_to(0.0), nullable=False),
        "volume": Column(int32, Check.greater_than_or_equal_to(0), nullable=False),
    },
    strict="filter",
)
