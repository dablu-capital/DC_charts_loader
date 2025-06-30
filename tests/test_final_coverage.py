"""
Final tests to achieve 100% coverage for remaining lines in ui.py
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.ui import on_maximize, on_timeframe_change


class TestFinalCoverage:
    """Tests to cover the final missing lines in ui.py."""
    
    def test_on_maximize_close_button_coverage(self):
        """Test on_maximize function with CLOSE button value to cover lines 129-131."""
        # Create mock charts
        chart1 = MagicMock()
        chart2 = MagicMock()
        charts = [chart1, chart2]
        
        # Mock topbar button with CLOSE value
        mock_button = MagicMock()
        mock_button.value = "×"  # This should trigger the restore logic (CLOSE constant)
        chart1.topbar = {"max": mock_button}
        
        # Call the function
        on_maximize(chart1, charts)
        
        # Verify both charts are resized to 0.5 width (side-by-side)
        chart1.resize.assert_called_once_with(0.5, 1.0)
        chart2.resize.assert_called_once_with(0.5, 1.0)
        
        # Verify button is set to FULLSCREEN
        mock_button.set.assert_called_once_with("⬜")
    
    def test_on_timeframe_change_no_timeframe_attribute(self):
        """Test on_timeframe_change when chart has no _timeframe attribute to cover line 146."""
        # Create mock chart without _timeframe attribute
        mock_chart = MagicMock()
        # Ensure the chart doesn't have _timeframe attribute initially
        if hasattr(mock_chart, '_timeframe'):
            delattr(mock_chart, '_timeframe')
        
        # Mock chart_data without set_timeframe method
        mock_chart_data = MagicMock()
        del mock_chart_data.set_timeframe  # Remove the method
        mock_chart_data.current_index = 0
        mock_chart_data.load_chart.return_value = (
            pd.DataFrame({'close': [150.0]}),
            {'ticker': 'AAPL'}
        )
        
        with patch('src.ui.plot_chart') as mock_plot_chart:
            # This should trigger the hasattr check and set _timeframe to "1D"
            on_timeframe_change(mock_chart, mock_chart_data, "5m")
        
        # Verify _timeframe was set to "5m" (after initially being set to "1D")
        assert mock_chart._timeframe == "5m"
        
        # Verify load_chart was called
        mock_chart_data.load_chart.assert_called_once_with(0)
        
        # Verify plot_chart was called with timeframe added to metadata
        mock_plot_chart.assert_called_once()
        args, kwargs = mock_plot_chart.call_args
        df, metadata, chart = args
        assert metadata['timeframe'] == "5m"


class TestUILineCoverage:
    """Additional tests to cover specific missing lines."""
    
    @patch('src.ui.ChartsMinuteData')
    @patch('src.ui.Chart')
    @patch('src.ui.plot_chart')
    @patch('src.ui.plot_indicators')
    def test_create_dual_chart_grid_line_255(self, mock_plot_indicators, mock_plot_chart, mock_chart_class, mock_charts_minute_data):
        """Test create_dual_chart_grid to cover line 255 (filename doesn't end with .feather)."""
        from src.ui import create_dual_chart_grid
        
        # Create mock chart_data1 with filename that doesn't end with .feather
        chart_data1 = MagicMock()
        chart_data1.data_filename = "/path/to/test_data.parquet"
        chart_data1.dict_filename = "/path/to/dict.feather"
        
        # Mock Chart class
        mock_main_chart = MagicMock()
        mock_right_chart = MagicMock()
        mock_main_chart.create_subchart.return_value = mock_right_chart
        mock_chart_class.return_value = mock_main_chart
        
        # Mock ChartsMinuteData
        mock_chart_data2 = MagicMock()
        mock_chart_data2.load_chart.return_value = (
            pd.DataFrame({'close': [250.0]}),
            {'ticker': 'MSFT'}
        )
        mock_charts_minute_data.return_value = mock_chart_data2
        
        # Mock chart_data1.load_chart
        chart_data1.load_chart.return_value = (
            pd.DataFrame({'close': [150.0]}),
            {'ticker': 'AAPL'}
        )
        
        with patch('src.ui.os.path.dirname', return_value="/path/to"):
            with patch('src.ui.os.path.basename', return_value="test_data.parquet"):
                with patch('src.ui.os.path.join', return_value="/path/to/test_data.parquet_min_data.feather"):
                    # This should trigger line 255: min_filename = base_name + "_min_data.feather"
                    result = create_dual_chart_grid(chart_data1, chart_data2=None)
        
        # Verify ChartsMinuteData was created
        mock_charts_minute_data.assert_called_once_with(
            "/path/to/dict.feather", 
            "/path/to/test_data.parquet_min_data.feather"
        )
        
        # Verify Chart was created
        mock_chart_class.assert_called_once_with(inner_width=0.5, inner_height=1.0)
        
        # Verify subchart was created
        mock_main_chart.create_subchart.assert_called_once_with(position="right", width=0.5, height=1.0)
        
        # Verify load_chart was called on both chart data objects
        chart_data1.load_chart.assert_called_once_with(0)
        mock_chart_data2.load_chart.assert_called_once_with(0)
        
        # Verify plot_chart and plot_indicators were called
        assert mock_plot_chart.call_count == 2
        assert mock_plot_indicators.call_count == 2