"""
Tests to complete 100% coverage for models.py and ui.py
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import os

from src.models import ChartsMinuteData
from src.ui import (
    plot_chart, on_maximize, on_timeframe_change, on_up_dual, on_down_dual,
    save_screenshot_dual, create_dual_chart_grid
)


class TestChartsMinuteDataCoverage:
    """Tests to cover missing lines in ChartsMinuteData."""
    
    @patch('src.models.load_min_chart')
    @patch('src.models.load_daily_df')
    @patch('src.models.apply_indicators')
    def test_set_timeframe_coverage(self, mock_apply_indicators, mock_load_daily_df, mock_load_min_chart):
        """Test set_timeframe method to cover line 138."""
        # Mock the data loading
        mock_charts_df = pd.DataFrame({
            'ticker': ['AAPL'],
            'date': [datetime(2023, 1, 15)],
            'volume': [1000]
        })
        mock_data_df = pd.DataFrame({
            'ticker': ['AAPL'],
            'date': [datetime(2023, 1, 15)],
            'close': [150.0]
        })
        
        mock_load_daily_df.side_effect = [mock_charts_df, mock_data_df]
        mock_apply_indicators.return_value = mock_data_df
        
        charts_data = ChartsMinuteData("dict.feather", "data.feather")
        
        # Test set_timeframe method (covers line 138)
        charts_data.set_timeframe("5m")
        assert charts_data.current_timeframe == "5m"
        
        charts_data.set_timeframe("1h")
        assert charts_data.current_timeframe == "1h"
    
    @patch('src.models.load_min_chart')
    @patch('src.models.load_daily_df')
    @patch('src.models.apply_indicators')
    def test_get_metadata_coverage(self, mock_apply_indicators, mock_load_daily_df, mock_load_min_chart):
        """Test get_metadata method to cover lines 141-143."""
        # Mock the data loading
        mock_charts_df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 15), datetime(2023, 1, 16)],
            'volume': [1000, 2000]
        })
        mock_data_df = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'date': [datetime(2023, 1, 15), datetime(2023, 1, 16)],
            'close': [150.0, 250.0]
        })
        
        mock_load_daily_df.side_effect = [mock_charts_df, mock_data_df]
        mock_apply_indicators.return_value = mock_data_df
        
        charts_data = ChartsMinuteData("dict.feather", "data.feather")
        charts_data.set_timeframe("1h")
        
        # Test get_metadata method (covers lines 141-143)
        metadata = charts_data.get_metadata(0)
        
        # After sorting by date descending, index 0 should be MSFT (2023-01-16)
        expected_metadata = {
            'ticker': 'MSFT',
            'date_str': '2023-01-16',
            'date': datetime(2023, 1, 16),
            'timeframe': '1h',
            'index': 0
        }
        assert metadata == expected_metadata
        
        # Test with index 1 (should be AAPL)
        metadata = charts_data.get_metadata(1)
        expected_metadata = {
            'ticker': 'AAPL',
            'date_str': '2023-01-15',
            'date': datetime(2023, 1, 15),
            'timeframe': '1h',
            'index': 1
        }
        assert metadata == expected_metadata
    
    @patch('src.models.load_min_chart')
    @patch('src.models.load_daily_df')
    @patch('src.models.apply_indicators')
    def test_load_chart_coverage(self, mock_apply_indicators, mock_load_daily_df, mock_load_min_chart):
        """Test load_chart method to cover lines 152-160."""
        # Mock the data loading
        mock_charts_df = pd.DataFrame({
            'ticker': ['AAPL'],
            'date': [datetime(2023, 1, 15)],
            'volume': [1000]
        })
        mock_data_df = pd.DataFrame({
            'ticker': ['AAPL'],
            'date': [datetime(2023, 1, 15)],
            'close': [150.0]
        })
        mock_chart_df = pd.DataFrame({
            'date': [datetime(2023, 1, 15)],
            'close': [150.0]
        })
        
        mock_load_daily_df.side_effect = [mock_charts_df, mock_data_df]
        mock_apply_indicators.return_value = mock_data_df
        mock_load_min_chart.return_value = mock_chart_df
        
        charts_data = ChartsMinuteData("dict.feather", "data.feather")
        
        # Test load_chart with explicit index (covers lines 152-160)
        df, metadata = charts_data.load_chart(0)
        
        # Verify load_min_chart was called with correct parameters
        assert mock_load_min_chart.call_count == 1
        call_args = mock_load_min_chart.call_args[0]
        assert call_args[0] == 'AAPL'
        assert call_args[1] == datetime(2023, 1, 15)
        # Third argument should be the data DataFrame
        
        # Verify returned data
        pd.testing.assert_frame_equal(df, mock_chart_df)
        assert metadata['ticker'] == 'AAPL'
        
        # Test load_chart with None index (should use current_index)
        mock_load_min_chart.reset_mock()
        charts_data.current_index = 0
        df2, metadata2 = charts_data.load_chart(None)
        
        # Should call load_min_chart again with same parameters
        assert mock_load_min_chart.call_count == 1
        call_args = mock_load_min_chart.call_args[0]
        assert call_args[0] == 'AAPL'
        assert call_args[1] == datetime(2023, 1, 15)


class TestUIFunctionsCoverage:
    """Tests to cover missing lines in ui.py functions."""
    
    def test_plot_chart_exception_coverage(self):
        """Test plot_chart exception handling to cover lines 46-47."""
        # Create a mock chart that raises exceptions
        mock_chart = MagicMock()
        
        # Make watermark method raise AttributeError first, then Exception on second call
        mock_chart.watermark.side_effect = [
            AttributeError("No vert_align parameter"),  # First call fails with AttributeError
            Exception("Standard watermark failed"),     # Second call fails with Exception
            None  # Third call succeeds
        ]
        
        metadata = {
            'ticker': 'AAPL',
            'timeframe': '1D',
            'date_str': '2023-01-15'
        }
        
        # Create sample data
        df = pd.DataFrame({
            'time': ['2023-01-15'],
            'open': [150.0],
            'high': [155.0],
            'low': [148.0],
            'close': [152.0],
            'volume': [1000]
        })
        
        # This should trigger the exception handling and call watermark("na")
        plot_chart(df, metadata, mock_chart)
        
        # Verify that watermark was called three times: 
        # 1. with vert_align (failed with AttributeError)
        # 2. without vert_align (failed with Exception) 
        # 3. with "na" (succeeded)
        assert mock_chart.watermark.call_count == 3
        mock_chart.watermark.assert_any_call("na")
    
    def test_on_maximize_coverage(self):
        """Test on_maximize function to cover lines 126-137."""
        # Create mock charts
        chart1 = MagicMock()
        chart2 = MagicMock()
        charts = [chart1, chart2]
        
        # Mock topbar button
        mock_button = MagicMock()
        chart1.topbar = {"max": mock_button}
        
        # Test maximize functionality (button value is not CLOSE)
        mock_button.value = "FULLSCREEN"  # Not CLOSE
        
        on_maximize(chart1, charts)
        
        # Verify chart1 is maximized (width=1.0) and chart2 is minimized (width=0.0)
        chart1.resize.assert_called_once_with(1.0, 1.0)
        chart2.resize.assert_called_once_with(0.0, 1.0)
        mock_button.set.assert_called_once_with("CLOSE")
        
        # Reset mocks
        chart1.reset_mock()
        chart2.reset_mock()
        mock_button.reset_mock()
        
        # Test restore functionality (button value is CLOSE)
        mock_button.value = "CLOSE"
        
        on_maximize(chart1, charts)
        
        # Verify both charts are restored to side-by-side (width=0.5)
        chart1.resize.assert_called_once_with(0.5, 1.0)
        chart2.resize.assert_called_once_with(0.5, 1.0)
        mock_button.set.assert_called_once_with("FULLSCREEN")
    
    @patch('src.ui.plot_chart')
    def test_on_timeframe_change_coverage(self, mock_plot_chart):
        """Test on_timeframe_change function to cover lines 145-158."""
        # Create mock chart and chart_data
        mock_chart = MagicMock()
        mock_chart_data = MagicMock()
        
        # Test with chart_data that has set_timeframe method (ChartsMinuteData)
        mock_chart_data.set_timeframe = MagicMock()
        mock_chart_data.current_index = 0
        mock_chart_data.load_chart.return_value = (
            pd.DataFrame({'close': [150.0]}),
            {'ticker': 'AAPL', 'timeframe': '5m'}
        )
        
        # Test timeframe change
        on_timeframe_change(mock_chart, mock_chart_data, "5m")
        
        # Verify chart._timeframe is set
        assert mock_chart._timeframe == "5m"
        
        # Verify set_timeframe was called
        mock_chart_data.set_timeframe.assert_called_once_with("5m")
        
        # Verify load_chart and plot_chart were called
        mock_chart_data.load_chart.assert_called_once_with(0)
        mock_plot_chart.assert_called_once()
        
        # Reset mocks
        mock_chart_data.reset_mock()
        mock_plot_chart.reset_mock()
        
        # Test with chart_data that doesn't have set_timeframe method
        mock_chart_data_no_timeframe = MagicMock()
        del mock_chart_data_no_timeframe.set_timeframe  # Remove the method
        mock_chart_data_no_timeframe.current_index = 1
        mock_chart_data_no_timeframe.load_chart.return_value = (
            pd.DataFrame({'close': [250.0]}),
            {'ticker': 'MSFT'}
        )
        
        on_timeframe_change(mock_chart, mock_chart_data_no_timeframe, "1h")
        
        # Verify timeframe was added to metadata
        args, kwargs = mock_plot_chart.call_args
        df, metadata, chart = args
        assert metadata['timeframe'] == "1h"
    
    @patch('src.ui.plot_chart')
    def test_on_up_dual_coverage(self, mock_plot_chart):
        """Test on_up_dual function to cover lines 163-167."""
        # Create mock charts and chart data
        chart1 = MagicMock()
        chart2 = MagicMock()
        chart_data1 = MagicMock()
        chart_data2 = MagicMock()
        
        # Mock next_chart returns
        chart_data1.next_chart.return_value = (
            pd.DataFrame({'close': [150.0]}),
            {'ticker': 'AAPL'}
        )
        chart_data2.next_chart.return_value = (
            pd.DataFrame({'close': [250.0]}),
            {'ticker': 'MSFT'}
        )
        
        on_up_dual(chart1, chart2, chart_data1, chart_data2)
        
        # Verify next_chart was called on both chart_data objects
        chart_data1.next_chart.assert_called_once()
        chart_data2.next_chart.assert_called_once()
        
        # Verify plot_chart was called twice
        assert mock_plot_chart.call_count == 2
    
    @patch('src.ui.plot_chart')
    def test_on_down_dual_coverage(self, mock_plot_chart):
        """Test on_down_dual function to cover lines 172-176."""
        # Create mock charts and chart data
        chart1 = MagicMock()
        chart2 = MagicMock()
        chart_data1 = MagicMock()
        chart_data2 = MagicMock()
        
        # Mock previous_chart returns
        chart_data1.previous_chart.return_value = (
            pd.DataFrame({'close': [150.0]}),
            {'ticker': 'AAPL'}
        )
        chart_data2.previous_chart.return_value = (
            pd.DataFrame({'close': [250.0]}),
            {'ticker': 'MSFT'}
        )
        
        on_down_dual(chart1, chart2, chart_data1, chart_data2)
        
        # Verify previous_chart was called on both chart_data objects
        chart_data1.previous_chart.assert_called_once()
        chart_data2.previous_chart.assert_called_once()
        
        # Verify plot_chart was called twice
        assert mock_plot_chart.call_count == 2
    
    @patch('os.makedirs')
    @patch('PIL.Image.new')
    @patch('PIL.Image.open')
    def test_save_screenshot_dual_coverage(self, mock_image_open, mock_image_new, mock_makedirs):
        """Test save_screenshot_dual function to cover missing lines."""
        # Create mock charts and chart data
        chart1 = MagicMock()
        chart2 = MagicMock()
        chart_data1 = MagicMock()
        chart_data2 = MagicMock()
        
        # Mock chart data metadata
        chart_data1.current_index = 0
        chart_data1.get_metadata.return_value = {
            "ticker": "AAPL",
            "date_str": "2023-01-15",
        }
        
        chart_data2.current_index = 0
        chart_data2.get_metadata.return_value = {
            "ticker": "MSFT",
            "date_str": "2023-01-15",
        }
        
        # Mock PIL Images
        mock_img1 = MagicMock()
        mock_img1.size = (800, 600)
        
        mock_img2 = MagicMock()
        mock_img2.size = (800, 600)
        
        mock_combined_img = MagicMock()
        
        # Configure mocks
        mock_image_open.side_effect = [mock_img1, mock_img2]
        mock_image_new.return_value = mock_combined_img
        
        # Mock print to capture output
        with patch("builtins.print") as mock_print:
            save_screenshot_dual(chart1, chart2, chart_data1, chart_data2, "test_folder")
        
        # Verify screenshots were taken from both charts
        chart1.screenshot.assert_called_once()
        chart2.screenshot.assert_called_once()
        
        # Verify PIL Image.open was called twice (for both screenshots)
        assert mock_image_open.call_count == 2
        
        # Verify a new combined image was created
        mock_image_new.assert_called_once_with('RGB', (1600, 600), 'white')
        
        # Verify images were pasted onto the combined image
        mock_combined_img.paste.assert_any_call(mock_img1, (0, 0))
        mock_combined_img.paste.assert_any_call(mock_img2, (800, 0))
        
        # Verify metadata was retrieved from both charts
        chart_data1.get_metadata.assert_called_once_with(0)
        chart_data2.get_metadata.assert_called_once_with(0)
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with("test_folder", exist_ok=True)
        
        # Verify the combined image was saved with correct filename
        expected_filename = "test_folder/AAPL_MSFT_2023-01-15_dual_screenshot.png"
        mock_combined_img.save.assert_called_once_with(expected_filename)
    
    @patch('src.ui.ChartsMinuteData')
    @patch('src.ui.Chart')
    def test_create_dual_chart_coverage_part1(self, mock_chart_class, mock_charts_minute_data):
        """Test create_dual_chart function to cover lines 246-280."""
        # Create mock chart_data1 with data_filename attribute
        chart_data1 = MagicMock()
        chart_data1.data_filename = "/path/to/data_data.feather"
        
        # Mock Chart class
        mock_main_chart = MagicMock()
        mock_right_chart = MagicMock()
        mock_main_chart.create_subchart.return_value = mock_right_chart
        mock_chart_class.return_value = mock_main_chart
        
        # Mock ChartsMinuteData
        mock_chart_data2 = MagicMock()
        mock_charts_minute_data.return_value = mock_chart_data2
        
        # Test with chart_data2=None (should create ChartsMinuteData)
        with patch('src.ui.os.path.dirname', return_value="/path/to"):
            with patch('src.ui.os.path.basename', return_value="data_data.feather"):
                with patch('src.ui.os.path.join', return_value="/path/to/data_min_data.feather"):
                    # This should trigger the chart_data2 creation logic (lines 246-263)
                    result = create_dual_chart_grid(chart_data1, chart_data2=None)
        
        # Verify ChartsMinuteData was created with correct parameters
        mock_charts_minute_data.assert_called_once()
        
        # Verify Chart was created with correct parameters
        mock_chart_class.assert_called_once_with(inner_width=0.5, inner_height=1.0)
        
        # Verify subchart was created
        mock_main_chart.create_subchart.assert_called_once_with(position="right", width=0.5, height=1.0)
    
    @patch('src.ui.ChartsMinuteData')
    @patch('src.ui.Chart')
    def test_create_dual_chart_no_data_filename_error(self, mock_chart_class, mock_charts_minute_data):
        """Test create_dual_chart error when chart_data1 has no data_filename."""
        # Create mock chart_data1 without data_filename attribute
        chart_data1 = MagicMock()
        del chart_data1.data_filename  # Remove the attribute
        
        # This should raise ValueError (lines 261-263)
        with pytest.raises(ValueError, match="chart_data1 must have a data_filename attribute"):
            create_dual_chart_grid(chart_data1, chart_data2=None)
    
    @patch('src.ui.ChartsMinuteData')
    @patch('src.ui.Chart')
    def test_create_dual_chart_filename_handling(self, mock_chart_class, mock_charts_minute_data):
        """Test create_dual_chart filename handling for different cases."""
        # Test case 1: filename ends with .feather
        chart_data1 = MagicMock()
        chart_data1.data_filename = "/path/to/test_data.feather"
        
        mock_main_chart = MagicMock()
        mock_right_chart = MagicMock()
        mock_main_chart.create_subchart.return_value = mock_right_chart
        mock_chart_class.return_value = mock_main_chart
        
        mock_chart_data2 = MagicMock()
        mock_charts_minute_data.return_value = mock_chart_data2
        
        with patch('src.ui.os.path.dirname', return_value="/path/to"):
            with patch('src.ui.os.path.basename', return_value="test_data.feather"):
                with patch('src.ui.os.path.join', return_value="/path/to/test_min_data.feather"):
                    create_dual_chart_grid(chart_data1, chart_data2=None)
        
        # Test case 2: filename doesn't end with .feather
        chart_data1.data_filename = "/path/to/test_data.parquet"
        
        with patch('src.ui.os.path.dirname', return_value="/path/to"):
            with patch('src.ui.os.path.basename', return_value="test_data.parquet"):
                with patch('src.ui.os.path.join', return_value="/path/to/test_data.parquet_min_data.feather"):
                    create_dual_chart_grid(chart_data1, chart_data2=None)