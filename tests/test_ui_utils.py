import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open

from src.ui.utils import (
    plot_chart,
    set_chart,
    plot_indicators,
    plot_sessions,
    _box_values,
    plot_line,
    save_screenshot,
    on_maximize,
    on_timeframe_change,
    save_screenshot_dual,
    FULLSCREEN,
    CLOSE,
)


class TestPlotChart:
    """Test cases for the plot_chart function."""

    @patch('src.ui.utils.plot_sessions')
    @patch('src.ui.utils.set_chart')
    @patch('src.ui.utils.config')
    def test_plot_chart_with_session_shading(self, mock_config, mock_set_chart, mock_plot_sessions):
        """Test plot_chart with session shading enabled."""
        mock_config.chart.show_session_shading = True
        mock_plot_sessions.return_value = ['drawing1', 'drawing2']
        
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'timeframe': '1m', 'ticker': 'AAPL', 'date_str': '2023-01-15'}
        chart = Mock()
        
        result = plot_chart(df, metadata, chart)
        
        mock_set_chart.assert_called_once_with(df, metadata, chart)
        mock_plot_sessions.assert_called_once_with(df, chart)
        assert result == ['drawing1', 'drawing2']

    @patch('src.ui.utils.plot_sessions')
    @patch('src.ui.utils.set_chart')
    @patch('src.ui.utils.config')
    def test_plot_chart_without_session_shading(self, mock_config, mock_set_chart, mock_plot_sessions):
        """Test plot_chart without session shading."""
        mock_config.chart.show_session_shading = False
        
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'timeframe': '1m', 'ticker': 'AAPL', 'date_str': '2023-01-15'}
        chart = Mock()
        
        result = plot_chart(df, metadata, chart)
        
        mock_set_chart.assert_called_once_with(df, metadata, chart)
        mock_plot_sessions.assert_not_called()
        assert result == []

    @patch('src.ui.utils.plot_sessions')
    @patch('src.ui.utils.set_chart')
    @patch('src.ui.utils.config')
    def test_plot_chart_non_minute_timeframe(self, mock_config, mock_set_chart, mock_plot_sessions):
        """Test plot_chart with non-minute timeframe."""
        mock_config.chart.show_session_shading = True
        
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'timeframe': '1D', 'ticker': 'AAPL', 'date_str': '2023-01-15'}
        chart = Mock()
        
        result = plot_chart(df, metadata, chart)
        
        mock_set_chart.assert_called_once_with(df, metadata, chart)
        mock_plot_sessions.assert_not_called()
        assert result == []


class TestSetChart:
    """Test cases for the set_chart function."""

    def test_set_chart_success(self):
        """Test successful chart setting."""
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'ticker': 'AAPL', 'timeframe': '1D', 'date_str': '2023-01-15'}
        chart = Mock()
        
        set_chart(df, metadata, chart)
        
        chart.set.assert_called_once_with(df)
        chart.watermark.assert_called_once_with(
            'AAPL 1D 2023-01-15',
            vert_align='top'
        )

    def test_set_chart_watermark_fallback(self):
        """Test chart setting with watermark fallback."""
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'ticker': 'AAPL', 'timeframe': '1D', 'date_str': '2023-01-15'}
        chart = Mock()
        
        # First call fails with AttributeError, second succeeds
        chart.watermark.side_effect = [AttributeError(), None]
        
        set_chart(df, metadata, chart)
        
        chart.set.assert_called_once_with(df)
        assert chart.watermark.call_count == 2
        chart.watermark.assert_any_call('AAPL 1D 2023-01-15', vert_align='top')
        chart.watermark.assert_any_call('AAPL 1D 2023-01-15')

    def test_set_chart_watermark_double_fallback(self):
        """Test chart setting with double watermark fallback."""
        df = pd.DataFrame({'close': [100, 101, 102]})
        metadata = {'ticker': 'AAPL', 'timeframe': '1D', 'date_str': '2023-01-15'}
        chart = Mock()
        
        # All calls fail, should use 'na'
        chart.watermark.side_effect = [AttributeError(), Exception(), None]
        
        set_chart(df, metadata, chart)
        
        chart.set.assert_called_once_with(df)
        assert chart.watermark.call_count == 3
        chart.watermark.assert_any_call('na')


class TestPlotIndicators:
    """Test cases for the plot_indicators function."""

    @patch('src.ui.utils.plot_line')
    @patch('src.ui.utils.config')
    def test_plot_indicators_sma(self, mock_config, mock_plot_line):
        """Test plotting SMA indicator."""
        mock_indicator = Mock()
        mock_indicator.name = 'SMA'
        mock_indicator.parameters = {'period': 20}
        mock_config.indicators = [mock_indicator]
        
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'close': [100, 101, 102],
            'SMA_20': [99, 100, 101]
        })
        chart = Mock()
        
        plot_indicators(df, chart)
        
        mock_plot_line.assert_called_once()
        args = mock_plot_line.call_args[0]
        pd.testing.assert_frame_equal(args[0], df[['date', 'SMA_20']])
        assert args[1] is chart
        assert args[2] == 'SMA_20'

    @patch('src.ui.utils.plot_line')
    @patch('src.ui.utils.config')
    def test_plot_indicators_missing_column(self, mock_config, mock_plot_line):
        """Test plotting indicator with missing column."""
        mock_indicator = Mock()
        mock_indicator.name = 'SMA'
        mock_indicator.parameters = {'period': 20}
        mock_config.indicators = [mock_indicator]
        
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'close': [100, 101, 102]
        })
        chart = Mock()
        
        plot_indicators(df, chart)
        
        mock_plot_line.assert_not_called()

    @patch('src.ui.utils.plot_line')
    @patch('src.ui.utils.config')
    def test_plot_indicators_no_indicators(self, mock_config, mock_plot_line):
        """Test plotting with no indicators."""
        mock_config.indicators = None
        
        df = pd.DataFrame({'close': [100, 101, 102]})
        chart = Mock()
        
        plot_indicators(df, chart)
        
        mock_plot_line.assert_not_called()

    @patch('src.ui.utils.plot_line')
    @patch('src.ui.utils.config')
    def test_plot_indicators_non_sma(self, mock_config, mock_plot_line):
        """Test plotting non-SMA indicator."""
        mock_indicator = Mock()
        mock_indicator.name = 'RSI'
        mock_indicator.parameters = {'period': 14}
        mock_config.indicators = [mock_indicator]
        
        df = pd.DataFrame({'close': [100, 101, 102]})
        chart = Mock()
        
        plot_indicators(df, chart)
        
        mock_plot_line.assert_not_called()


class TestPlotSessions:
    """Test cases for the plot_sessions function."""

    def test_plot_sessions_success(self):
        """Test successful session plotting."""
        df = pd.DataFrame({
            'time': ['2023-01-15 08:00:00', '2023-01-15 10:00:00', '2023-01-15 17:00:00'],
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5]
        })
        chart = Mock()
        mock_box = Mock()
        chart.box.return_value = mock_box
        
        result = plot_sessions(df, chart)
        
        assert len(result) > 0
        assert all(box is mock_box for box in result)
        chart.box.assert_called()

    def test_plot_sessions_empty_dataframe(self):
        """Test plot_sessions with empty DataFrame."""
        df = pd.DataFrame()
        chart = Mock()
        
        result = plot_sessions(df, chart)
        
        assert result == []
        chart.box.assert_not_called()

    def test_plot_sessions_no_time_column(self):
        """Test plot_sessions with no time column."""
        df = pd.DataFrame({'close': [100, 101, 102]})
        chart = Mock()
        
        result = plot_sessions(df, chart)
        
        assert result == []
        chart.box.assert_not_called()

    def test_plot_sessions_no_session_data(self):
        """Test plot_sessions with no premarket/aftermarket data."""
        # Create data that doesn't fall into premarket or aftermarket hours
        df = pd.DataFrame({
            'time': ['2023-01-15 12:00:00', '2023-01-15 13:00:00', '2023-01-15 14:00:00'],
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5]
        })
        chart = Mock()
        
        result = plot_sessions(df, chart)
        
        assert result == []
        chart.box.assert_not_called()


class TestBoxValues:
    """Test cases for the _box_values function."""

    def test_box_values(self):
        """Test _box_values function."""
        dates = pd.date_range('2023-01-15', periods=6, freq='h')
        df = pd.DataFrame({
            'value': [1, 2, 3, 4, 5, 6]
        }, index=dates)
        
        result = _box_values(df)
        
        assert len(result) == 1  # One day
        start_time, end_time = result[0]
        assert start_time == dates[0]
        assert end_time == dates[-1]


class TestPlotLine:
    """Test cases for the plot_line function."""

    def test_plot_line(self):
        """Test plot_line function."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'SMA_20': [99, 100, 101]
        })
        chart = Mock()
        mock_line = Mock()
        chart.create_line.return_value = mock_line
        
        plot_line(data, chart, 'SMA_20')
        
        chart.create_line.assert_called_once_with(name='SMA_20', price_line=False)
        mock_line.set.assert_called_once_with(data)


class TestSaveScreenshot:
    """Test cases for the save_screenshot function."""

    @patch('builtins.open', new_callable=mock_open)
    def test_save_screenshot(self, mock_file_open):
        """Test save_screenshot function."""
        chart = Mock()
        chart.screenshot.return_value = b'fake_image_data'
        
        chart_data = Mock()
        chart_data.current_index = 0
        chart_data.get_metadata.return_value = {
            'ticker': 'AAPL',
            'date_str': '2023-01-15'
        }
        
        save_screenshot(chart, chart_data, 'test_folder')
        
        chart.screenshot.assert_called_once()
        chart_data.get_metadata.assert_called_once_with(0)
        
        expected_filename = 'test_folder/AAPL_2023-01-15_screenshot.png'
        mock_file_open.assert_called_once_with(expected_filename, 'wb')
        mock_file_open().write.assert_called_once_with(b'fake_image_data')


class TestOnMaximize:
    """Test cases for the on_maximize function."""

    def test_on_maximize_fullscreen(self):
        """Test maximizing a chart."""
        chart1 = Mock()
        chart2 = Mock()
        chart1.topbar = {'max': Mock()}
        chart1.topbar['max'].value = FULLSCREEN
        
        charts = [chart1, chart2]
        
        on_maximize(chart1, charts)
        
        chart1.resize.assert_called_once_with(1.0, 1.0)
        chart2.resize.assert_called_once_with(0.0, 1.0)
        chart1.topbar['max'].set.assert_called_once_with(CLOSE)

    def test_on_maximize_restore(self):
        """Test restoring charts to side-by-side view."""
        chart1 = Mock()
        chart2 = Mock()
        chart1.topbar = {'max': Mock()}
        chart1.topbar['max'].value = CLOSE
        
        charts = [chart1, chart2]
        
        on_maximize(chart1, charts)
        
        chart1.resize.assert_called_once_with(0.5, 1.0)
        chart2.resize.assert_called_once_with(0.5, 1.0)
        chart1.topbar['max'].set.assert_called_once_with(FULLSCREEN)


class TestOnTimeframeChange:
    """Test cases for the on_timeframe_change function."""

    @patch('src.ui.utils.plot_chart')
    def test_on_timeframe_change_with_set_timeframe(self, mock_plot_chart):
        """Test timeframe change with set_timeframe method."""
        chart = Mock()
        chart_data = Mock()
        chart_data.set_timeframe = Mock()
        chart_data.current_index = 0
        chart_data.load_chart.return_value = (
            pd.DataFrame({'close': [100]}), 
            {'timeframe': '5m'}
        )
        
        on_timeframe_change(chart, chart_data, '5m')
        
        chart_data.set_timeframe.assert_called_once_with('5m')
        chart_data.load_chart.assert_called_once_with(0)
        mock_plot_chart.assert_called_once()

    @patch('src.ui.utils.plot_chart')
    def test_on_timeframe_change_without_set_timeframe(self, mock_plot_chart):
        """Test timeframe change without set_timeframe method."""
        chart = Mock()
        chart_data = Mock()
        chart_data.current_index = 0
        # Remove set_timeframe method to simulate chart_data without it
        if hasattr(chart_data, 'set_timeframe'):
            delattr(chart_data, 'set_timeframe')
        
        metadata = {'timeframe': '1D'}
        chart_data.load_chart.return_value = (
            pd.DataFrame({'close': [100]}), 
            metadata
        )
        
        on_timeframe_change(chart, chart_data, '5m')
        
        chart_data.load_chart.assert_called_once_with(0)
        mock_plot_chart.assert_called_once()
        # Should have modified metadata to include new timeframe
        call_args = mock_plot_chart.call_args[0]
        assert call_args[1]['timeframe'] == '5m'

    @patch('src.ui.utils.plot_chart')
    def test_on_timeframe_change_chart_without_timeframe_attribute(self, mock_plot_chart):
        """Test timeframe change when chart doesn't have _timeframe attribute."""
        chart = Mock()
        # Ensure chart doesn't have _timeframe attribute
        del chart._timeframe  # This will make hasattr return False
        
        chart_data = Mock()
        chart_data.set_timeframe = Mock()
        chart_data.current_index = 0
        chart_data.load_chart.return_value = (
            pd.DataFrame({'close': [100]}), 
            {'timeframe': '5m'}
        )
        
        on_timeframe_change(chart, chart_data, '5m')
        
        # Should set default timeframe and then update
        assert chart._timeframe == '5m'
        chart_data.set_timeframe.assert_called_once_with('5m')
        chart_data.load_chart.assert_called_once_with(0)
        mock_plot_chart.assert_called_once()


class TestSaveScreenshotDual:
    """Test cases for the save_screenshot_dual function."""

    @patch('builtins.open', new_callable=mock_open)
    def test_save_screenshot_dual(self, mock_file_open):
        """Test save_screenshot_dual function."""
        chart1 = Mock()
        chart2 = Mock()
        chart1.screenshot.return_value = b'fake_image_data1'
        chart2.screenshot.return_value = b'fake_image_data2'
        
        chart_data1 = Mock()
        chart_data2 = Mock()
        chart_data1.current_index = 0
        chart_data2.current_index = 1
        chart_data1.get_metadata.return_value = {
            'ticker': 'AAPL',
            'date_str': '2023-01-15'
        }
        chart_data2.get_metadata.return_value = {
            'ticker': 'MSFT',
            'date_str': '2023-01-16'
        }
        
        save_screenshot_dual(chart1, chart2, chart_data1, chart_data2, 'test_folder')
        
        chart1.screenshot.assert_called_once()
        chart2.screenshot.assert_called_once()
        chart_data1.get_metadata.assert_called_once_with(0)
        chart_data2.get_metadata.assert_called_once_with(1)
        
        expected_filename1 = 'test_folder/AAPL_2023-01-15_chart1_screenshot.png'
        expected_filename2 = 'test_folder/MSFT_2023-01-16_chart2_screenshot.png'
        
        assert mock_file_open.call_count == 2