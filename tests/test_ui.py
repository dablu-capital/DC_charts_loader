import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open

from src.ui import (
    plot_chart,
    plot_line,
    on_up,
    on_down,
    plot_indicators,
    on_maximize,
    on_timeframe_change,
    on_up_dual,
    on_down_dual,
    save_screenshot_dual,
    create_dual_chart_grid,
    save_screenshot,
    create_and_bind_chart,
)
from src.models import ChartsMinuteData


class TestPlotChart:
    """Test cases for the plot_chart function."""

    def test_plot_chart_success(self):
        """Test successful chart plotting."""
        # Create mock chart and data
        mock_chart = Mock()
        mock_chart.watermark = Mock()
        mock_chart.legend = Mock()

        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        metadata = {"ticker": "AAPL", "timeframe": "1D", "date_str": "2023-01-15"}

        plot_chart(df, metadata, mock_chart)

        # Verify chart methods were called
        mock_chart.set.assert_called_once_with(df)
        mock_chart.watermark.assert_called_once_with(
            "AAPL 1D 2023-01-15", vert_align="top"
        )
        mock_chart.legend.assert_called_once_with(
            visible=True,
            ohlc=True,
            lines=True,
            font_family="arial",
            font_size=12,
            percent=False,
        )

    def test_plot_chart_watermark_attribute_error(self):
        """Test chart plotting when watermark raises AttributeError."""
        # Create mock chart that raises AttributeError on first call, succeeds on second
        mock_chart = Mock()
        mock_chart.watermark = Mock(
            side_effect=[TypeError("Custom watermark not available"), None]
        )
        mock_chart.watermark = Mock(
            side_effect=[AttributeError("Custom watermark not available"), None]
        )
        mock_chart.legend = Mock()

        df = pd.DataFrame({"close": [100, 101, 102]})
        metadata = {"ticker": "AAPL", "timeframe": "1D", "date_str": "2023-01-15"}

        plot_chart(df, metadata, mock_chart)

        # Should call watermark twice: once with full text (fails), once with "na"
        assert mock_chart.watermark.call_count == 2
        mock_chart.watermark.assert_any_call("AAPL 1D 2023-01-15", vert_align="top")
        mock_chart.watermark.assert_any_call("na")


class TestPlotLine:
    """Test cases for the plot_line function."""

    def test_plot_line(self):
        """Test plotting a line on the chart."""
        mock_chart = Mock()
        mock_line = Mock()
        mock_chart.create_line.return_value = mock_line

        data = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "SMA_20": [100, 101, 102]}
        )

        plot_line(data, mock_chart, "SMA_20")

        # Verify line creation and data setting
        mock_chart.create_line.assert_called_once_with(name="SMA_20", price_line=False)
        mock_line.set.assert_called_once_with(data)


class TestNavigationFunctions:
    """Test cases for navigation functions."""

    def test_on_up(self):
        """Test on_up function."""
        mock_chart = Mock()
        mock_chart_data = Mock()

        # Mock the next_chart method
        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "AAPL", "timeframe": "1D", "date_str": "2023-01-15"}
        mock_chart_data.next_chart.return_value = (mock_df, mock_metadata)

        with patch("src.ui.plot_chart") as mock_plot_chart:
            on_up(mock_chart, mock_chart_data)

        # Verify next_chart was called and plot_chart was called with results
        mock_chart_data.next_chart.assert_called_once()
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, mock_chart)

    def test_on_down(self):
        """Test on_down function."""
        mock_chart = Mock()
        mock_chart_data = Mock()

        # Mock the previous_chart method
        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "MSFT", "timeframe": "1D", "date_str": "2023-01-10"}
        mock_chart_data.previous_chart.return_value = (mock_df, mock_metadata)

        with patch("src.ui.plot_chart") as mock_plot_chart:
            on_down(mock_chart, mock_chart_data)

        # Verify previous_chart was called and plot_chart was called with results
        mock_chart_data.previous_chart.assert_called_once()
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, mock_chart)


class TestPlotIndicators:
    """Test cases for the plot_indicators function."""

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_sma(self, mock_plot_line, mock_config):
        """Test plotting SMA indicator."""
        # Mock configuration
        mock_indicator = MagicMock()
        mock_indicator.name = "SMA"
        mock_indicator.parameters = {"period": 20}
        mock_config.indicators = [mock_indicator]

        # Create DataFrame with SMA column
        df = pd.DataFrame(
            {
                "date": pd.date_range("2023-01-01", periods=3),
                "close": [100, 101, 102],
                "SMA_20": [99, 100, 101],
            }
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # Verify plot_line was called for SMA
        mock_plot_line.assert_called_once()
        call_args = mock_plot_line.call_args
        called_data, called_chart, called_name = call_args[0]

        # Check the arguments separately
        pd.testing.assert_frame_equal(called_data, df[["date", "SMA_20"]])
        assert called_chart is mock_chart
        assert called_name == "SMA_20"

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_sma_missing_column(self, mock_plot_line, mock_config):
        """Test plotting SMA indicator when column is missing."""
        # Mock configuration
        mock_indicator = MagicMock()
        mock_indicator.name = "SMA"
        mock_indicator.parameters = {"period": 20}
        mock_config.indicators = [mock_indicator]

        # Create DataFrame without SMA column
        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # plot_line should not be called since SMA_20 column doesn't exist
        mock_plot_line.assert_not_called()

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_no_parameters(self, mock_plot_line, mock_config):
        """Test plotting indicator with no parameters."""
        # Mock configuration
        mock_indicator = MagicMock()
        mock_indicator.name = "SMA"
        mock_indicator.parameters = None
        mock_config.indicators = [mock_indicator]

        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # plot_line should not be called since no period is specified
        mock_plot_line.assert_not_called()

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_no_indicators(self, mock_plot_line, mock_config):
        """Test plotting when no indicators are configured."""
        mock_config.indicators = None

        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # plot_line should not be called
        mock_plot_line.assert_not_called()

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_empty_list(self, mock_plot_line, mock_config):
        """Test plotting with empty indicators list."""
        mock_config.indicators = []

        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # plot_line should not be called
        mock_plot_line.assert_not_called()

    @patch("src.ui.config")
    @patch("src.ui.plot_line")
    def test_plot_indicators_non_sma(self, mock_plot_line, mock_config):
        """Test plotting non-SMA indicator (should be ignored)."""
        # Mock configuration with non-SMA indicator
        mock_indicator = MagicMock()
        mock_indicator.name = "RSI"
        mock_indicator.parameters = {"period": 14}
        mock_config.indicators = [mock_indicator]

        df = pd.DataFrame(
            {"date": pd.date_range("2023-01-01", periods=3), "close": [100, 101, 102]}
        )

        mock_chart = Mock()

        plot_indicators(df, mock_chart)

        # plot_line should not be called since only SMA is implemented
        mock_plot_line.assert_not_called()


class TestSaveScreenshot:
    """Test cases for the save_screenshot function."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_screenshot(self, mock_makedirs, mock_file_open):
        """Test save_screenshot function."""
        from src.ui import save_screenshot

        # Create mock chart and chart_data
        mock_chart = Mock()
        mock_chart.screenshot.return_value = b"fake_image_data"

        mock_chart_data = Mock()
        mock_chart_data.current_index = 0
        mock_chart_data.get_metadata.return_value = {
            "ticker": "AAPL",
            "date_str": "2023-01-15",
        }

        # Mock print to capture output
        with patch("builtins.print") as mock_print:
            save_screenshot(mock_chart, mock_chart_data, "test_folder")

        # Verify screenshot was taken
        mock_chart.screenshot.assert_called_once()

        # Verify metadata was retrieved
        mock_chart_data.get_metadata.assert_called_once_with(0)

        # Verify file was written
        expected_filename = "test_folder/AAPL_2023-01-15_screenshot.png"
        mock_file_open.assert_called_once_with(expected_filename, "wb")
        mock_file_open().write.assert_called_once_with(b"fake_image_data")

        # Verify print message
        mock_print.assert_called_once_with(f"Screenshot saved to {expected_filename}")


class TestCreateAndBindChart:
    """Test cases for the create_and_bind_chart function."""

    @patch("src.ui.Chart")
    @patch("src.ui.plot_chart")
    @patch("src.ui.plot_indicators")
    def test_create_and_bind_chart(
        self, mock_plot_indicators, mock_plot_chart, mock_chart_class
    ):
        """Test create_and_bind_chart function."""
        from src.ui import create_and_bind_chart

        # Create mock chart instance
        mock_chart = Mock()
        mock_chart_class.return_value = mock_chart

        # Create mock chart_data
        mock_chart_data = Mock()
        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "AAPL", "date_str": "2023-01-15"}
        mock_chart_data.load_chart.return_value = (mock_df, mock_metadata)

        result = create_and_bind_chart(mock_chart_data)

        # Verify chart was created
        mock_chart_class.assert_called_once()

        # Verify data was loaded
        mock_chart_data.load_chart.assert_called_once_with(0)

        # Verify plotting functions were called
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, mock_chart)
        mock_plot_indicators.assert_called_once_with(mock_df, mock_chart)

        # Verify hotkeys were bound
        assert mock_chart.hotkey.call_count == 3

        # Check hotkey bindings
        hotkey_calls = mock_chart.hotkey.call_args_list
        assert hotkey_calls[0][0][:3] == ("shift", 1)  # on_up
        assert hotkey_calls[1][0][:3] == ("shift", 2)  # on_down
        assert hotkey_calls[2][0][:3] == ("shift", "S")  # save_screenshot

        # Verify the chart is returned
        assert result is mock_chart
