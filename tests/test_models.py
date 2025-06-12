import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.models import ChartsData, ChartsDailyData, ChartsWMOverride


class TestChartsData:
    """Test cases for the abstract ChartsData class."""

    def test_init(self):
        """Test ChartsData initialization."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        assert charts_data.charts == charts
        assert charts_data.current_index == 0

    def test_set_index(self):
        """Test setting the current index."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        charts_data.set_index(2)
        assert charts_data.current_index == 2

    def test_increase_index_normal(self):
        """Test increasing index within bounds."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        # Start at 0, should go to 1
        result = charts_data.increase_index()
        assert result == 1
        assert charts_data.current_index == 1
        
        # Go to 2
        result = charts_data.increase_index()
        assert result == 2
        assert charts_data.current_index == 2

    def test_increase_index_wrap_around(self):
        """Test increasing index wraps around at the end."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        charts_data.set_index(2)  # Set to last index
        
        # Should wrap around to 0
        result = charts_data.increase_index()
        assert result == 0
        assert charts_data.current_index == 0

    def test_decrease_index_normal(self):
        """Test decreasing index within bounds."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        charts_data.set_index(2)  # Start at 2
        
        # Should go to 1
        result = charts_data.decrease_index()
        assert result == 1
        assert charts_data.current_index == 1
        
        # Go to 0
        result = charts_data.decrease_index()
        assert result == 0
        assert charts_data.current_index == 0

    def test_decrease_index_wrap_around(self):
        """Test decreasing index wraps around at the beginning."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        # Start at 0 (default)
        
        # Should wrap around to last index (2)
        result = charts_data.decrease_index()
        assert result == 2
        assert charts_data.current_index == 2

    def test_next_chart(self):
        """Test next_chart method calls increase_index and load_chart."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        # Mock the load_chart method
        charts_data.load_chart = Mock(return_value="loaded_chart")
        
        result = charts_data.next_chart()
        
        # Should have increased index and called load_chart
        assert charts_data.current_index == 1
        charts_data.load_chart.assert_called_once_with(1)
        assert result == "loaded_chart"

    def test_previous_chart(self):
        """Test previous_chart method calls decrease_index and load_chart."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        charts_data.set_index(1)  # Start at middle
        
        # Mock the load_chart method
        charts_data.load_chart = Mock(return_value="loaded_chart")
        
        result = charts_data.previous_chart()
        
        # Should have decreased index and called load_chart
        assert charts_data.current_index == 0
        charts_data.load_chart.assert_called_once_with(0)
        assert result == "loaded_chart"

    def test_load_chart_not_implemented(self):
        """Test that load_chart raises NotImplementedError."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        with pytest.raises(NotImplementedError):
            charts_data.load_chart()

    def test_get_metadata_not_implemented(self):
        """Test that get_metadata raises NotImplementedError."""
        charts = ['chart1', 'chart2', 'chart3']
        charts_data = ChartsData(charts)
        
        with pytest.raises(NotImplementedError):
            charts_data.get_metadata(0)


class TestChartsDailyData:
    """Test cases for the ChartsDailyData class."""

    @patch('src.models.load_daily_df')
    def test_init(self, mock_load_daily_df):
        """Test ChartsDailyData initialization."""
        # Mock the load functions
        mock_charts_df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 2), datetime(2023, 1, 1)]
        })
        mock_data_df = pd.DataFrame({
            'ticker': ['AAPL'],
            'date': [datetime(2023, 1, 1)],
            'close': [100.0]
        })
        
        mock_load_daily_df.side_effect = [mock_charts_df, mock_data_df]
        
        with patch('src.models.apply_indicators', return_value=mock_data_df) as mock_apply:
            charts_data = ChartsDailyData("dict_file.feather", "data_file.feather")
        
        # Check initialization
        assert charts_data.dict_filename == "dict_file.feather"
        assert charts_data.data_filename == "data_file.feather"
        assert charts_data.current_index == 0
        
        # Check that data was loaded and sorted
        assert len(charts_data.charts) == 2
        # Should be sorted by date descending
        assert charts_data.charts.iloc[0]['ticker'] == 'AAPL'  # 2023-01-02
        assert charts_data.charts.iloc[1]['ticker'] == 'MSFT'  # 2023-01-01
        
        # Check that apply_indicators was called
        mock_apply.assert_called_once()

    def test_get_metadata(self):
        """Test get_metadata method."""
        # Create a mock ChartsDailyData with sample data
        charts_data = ChartsDailyData.__new__(ChartsDailyData)
        charts_data.charts = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 15), datetime(2023, 1, 10)]
        })
        
        metadata = charts_data.get_metadata(0)
        
        expected = {
            "ticker": "AAPL",
            "date_str": "2023-01-15",
            "date": datetime(2023, 1, 15),
            "timeframe": "1D",
            "index": 0,
        }
        
        assert metadata == expected

    @patch('src.models.load_daily_data')
    def test_load_chart_with_index(self, mock_load_daily_data):
        """Test load_chart method with specific index."""
        # Create a mock ChartsDailyData
        charts_data = ChartsDailyData.__new__(ChartsDailyData)
        charts_data.charts = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 15), datetime(2023, 1, 10)]
        })
        charts_data.data = pd.DataFrame()
        charts_data.current_index = 0
        
        # Mock the load_daily_data function
        mock_df = pd.DataFrame({'close': [100, 101, 102]})
        mock_load_daily_data.return_value = mock_df
        
        df, metadata = charts_data.load_chart(1)
        
        # Check that load_daily_data was called with correct parameters
        mock_load_daily_data.assert_called_once_with(
            'MSFT', datetime(2023, 1, 10), charts_data.data
        )
        
        # Check return values
        assert df is mock_df
        assert metadata['ticker'] == 'MSFT'
        assert metadata['date'] == datetime(2023, 1, 10)

    @patch('src.models.load_daily_data')
    def test_load_chart_default_index(self, mock_load_daily_data):
        """Test load_chart method with default (current) index."""
        # Create a mock ChartsDailyData
        charts_data = ChartsDailyData.__new__(ChartsDailyData)
        charts_data.charts = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 15), datetime(2023, 1, 10)]
        })
        charts_data.data = pd.DataFrame()
        charts_data.current_index = 1
        
        # Mock the load_daily_data function
        mock_df = pd.DataFrame({'close': [100, 101, 102]})
        mock_load_daily_data.return_value = mock_df
        
        df, metadata = charts_data.load_chart()  # No index provided
        
        # Should use current_index (1)
        mock_load_daily_data.assert_called_once_with(
            'MSFT', datetime(2023, 1, 10), charts_data.data
        )
        
        assert metadata['ticker'] == 'MSFT'


class TestChartsWMOverride:
    """Test cases for the ChartsWMOverride class."""

    def test_watermark_default_parameters(self):
        """Test watermark method with default parameters."""
        chart = ChartsWMOverride()
        chart.id = "test_chart"
        chart.run_script = Mock()
        
        chart.watermark("Test Watermark")
        
        # Check that run_script was called with correct parameters
        expected_script = """
          test_chart.chart.applyOptions({
              watermark: {
                  visible: true,
                  fontSize: 44,
                  horzAlign: 'center',
                  vertAlign: 'center',
                  color: 'rgba(180, 180, 200, 0.5)',
                  text: 'Test Watermark',
              }
          })"""
        
        chart.run_script.assert_called_once_with(expected_script)

    def test_watermark_custom_parameters(self):
        """Test watermark method with custom parameters."""
        chart = ChartsWMOverride()
        chart.id = "test_chart"
        chart.run_script = Mock()
        
        chart.watermark(
            text="Custom Text",
            font_size=20,
            color="red",
            horz_align="left",
            vert_align="bottom"
        )
        
        expected_script = """
          test_chart.chart.applyOptions({
              watermark: {
                  visible: true,
                  fontSize: 20,
                  horzAlign: 'left',
                  vertAlign: 'bottom',
                  color: 'red',
                  text: 'Custom Text',
              }
          })"""
        
        chart.run_script.assert_called_once_with(expected_script)

    def test_watermark_special_characters(self):
        """Test watermark method with special characters in text."""
        chart = ChartsWMOverride()
        chart.id = "test_chart"
        chart.run_script = Mock()
        
        chart.watermark("AAPL 1D 2023-01-15")
        
        # Should handle the text as-is
        expected_script = """
          test_chart.chart.applyOptions({
              watermark: {
                  visible: true,
                  fontSize: 44,
                  horzAlign: 'center',
                  vertAlign: 'center',
                  color: 'rgba(180, 180, 200, 0.5)',
                  text: 'AAPL 1D 2023-01-15',
              }
          })"""
        
        chart.run_script.assert_called_once_with(expected_script)