import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ui.models import (
    ChartPlotter,
    SingleChartPlotter,
    DualChartPlotter,
    DoubleClickTracker,
    double_click_tracker,
    on_chart_click2,
)
from src.models import ChartsData, ChartsMinuteData


class TestChartPlotter:
    """Test cases for the abstract ChartPlotter class."""

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        chart_data = Mock()
        plotter = ChartPlotter()

        with pytest.raises(NotImplementedError):
            plotter.setup()

        with pytest.raises(NotImplementedError):
            plotter.update_chart()

        with pytest.raises(NotImplementedError):
            plotter.clear_drawings()

        with pytest.raises(NotImplementedError):
            plotter.bind_hotkeys()


class TestSingleChartPlotter:
    """Test cases for the SingleChartPlotter class."""

    @patch("src.ui.models.plot_indicators")
    @patch("src.ui.models.plot_chart")
    def test_setup(self, mock_plot_chart, mock_plot_indicators):
        """Test SingleChartPlotter setup."""
        chart_data = Mock()
        chart = Mock()

        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "AAPL", "timeframe": "1D"}
        chart_data.load_chart.return_value = (mock_df, mock_metadata)
        mock_plot_chart.return_value = ["drawing1", "drawing2"]

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.setup()

        # Verify chart setup
        chart_data.load_chart.assert_called_once_with(0)
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, chart)
        mock_plot_indicators.assert_called_once_with(mock_df, chart)

        # Verify chart configuration
        chart.legend.assert_called_once_with(
            visible=True,
            ohlc=True,
            lines=True,
            font_family="arial",
            font_size=12,
            percent=False,
        )
        chart.price_line.assert_called_once_with(line_visible=False)

        # Verify hotkeys bound
        assert chart.hotkey.call_count == 3

        # Verify drawing IDs stored
        assert plotter.drawing_ids == ["drawing1", "drawing2"]

    @patch("src.ui.models.plot_chart")
    def test_update_chart_next(self, mock_plot_chart):
        """Test updating chart with next direction."""
        chart_data = Mock()
        chart = Mock()

        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "AAPL", "timeframe": "1D"}
        chart_data.next_chart.return_value = (mock_df, mock_metadata)
        mock_plot_chart.return_value = ["new_drawing"]

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.drawing_ids = ["old_drawing1", "old_drawing2"]

        # Mock the drawings
        old_drawing1 = Mock()
        old_drawing2 = Mock()
        plotter.drawing_ids = [old_drawing1, old_drawing2]

        plotter.update_chart("next")

        # Verify old drawings cleared
        old_drawing1.delete.assert_called_once()
        old_drawing2.delete.assert_called_once()

        # Verify new chart loaded
        chart_data.next_chart.assert_called_once()
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, chart)

        # Verify new drawing IDs stored
        assert plotter.drawing_ids == ["new_drawing"]

    @patch("src.ui.models.plot_chart")
    def test_update_chart_previous(self, mock_plot_chart):
        """Test updating chart with previous direction."""
        chart_data = Mock()
        chart = Mock()

        mock_df = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata = {"ticker": "AAPL", "timeframe": "1D"}
        chart_data.previous_chart.return_value = (mock_df, mock_metadata)
        mock_plot_chart.return_value = ["new_drawing"]

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.drawing_ids = []

        plotter.update_chart("previous")

        # Verify chart loaded
        chart_data.previous_chart.assert_called_once()
        mock_plot_chart.assert_called_once_with(mock_df, mock_metadata, chart)

    def test_clear_drawings(self):
        """Test clearing drawings."""
        chart_data = Mock()
        chart = Mock()

        drawing1 = Mock()
        drawing2 = Mock()

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.drawing_ids = [drawing1, drawing2]

        plotter.clear_drawings()

        drawing1.delete.assert_called_once()
        drawing2.delete.assert_called_once()

    def test_clear_drawings_empty(self):
        """Test clearing drawings when list is empty."""
        chart_data = Mock()
        chart = Mock()

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.drawing_ids = []

        # Should not raise an error
        plotter.clear_drawings()

    @patch("src.ui.models.save_screenshot")
    def test_bind_hotkeys(self, mock_save_screenshot):
        """Test hotkey binding."""
        chart_data = Mock()
        chart = Mock()

        plotter = SingleChartPlotter(chart_data, chart)
        plotter.bind_hotkeys()

        # Verify hotkeys were bound
        assert chart.hotkey.call_count == 3

        # Test the hotkey functions
        calls = chart.hotkey.call_args_list

        # First hotkey should be for "next"
        assert calls[0][0] == ("shift", 1)
        next_func = calls[0][1]["func"]

        # Second hotkey should be for "previous"
        assert calls[1][0] == ("shift", 2)
        prev_func = calls[1][1]["func"]

        # Third hotkey should be for save screenshot
        assert calls[2][0] == ("shift", "S")
        screenshot_func = calls[2][1]["func"]

        # Test next function
        with patch.object(plotter, "update_chart") as mock_update:
            next_func(None)
            mock_update.assert_called_once_with("next")

        # Test previous function
        with patch.object(plotter, "update_chart") as mock_update:
            prev_func(None)
            mock_update.assert_called_once_with("previous")

        # Test screenshot function
        screenshot_func(None)
        mock_save_screenshot.assert_called_once_with(chart, chart_data)


class TestDualChartPlotter:
    """Test cases for the DualChartPlotter class."""

    @patch("src.ui.models.ChartsMinuteData")
    @patch("src.ui.models.Chart")
    def test_init_without_chart2_data(self, mock_chart_class, mock_charts_minute_data):
        """Test DualChartPlotter initialization without chart2_data."""
        chart_data = Mock()
        chart_data.dict_filename = Path("test.feather")

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart
        mock_chart_class.return_value = mock_chart

        mock_minute_data = Mock()
        mock_charts_minute_data.return_value = mock_minute_data

        plotter = DualChartPlotter(chart_data)

        assert plotter.chart_data is chart_data
        assert plotter.chart2_data is mock_minute_data
        assert plotter.chart is mock_chart
        assert plotter.right_chart is mock_right_chart
        assert plotter.drawing_ids == []

        # Verify chart creation
        mock_chart_class.assert_called_once_with(inner_width=0.5, inner_height=1.0)
        mock_chart.create_subchart.assert_called_once_with(
            position="right", width=0.5, height=1.0
        )

    @patch("src.ui.models.Chart")
    def test_init_with_chart2_data(self, mock_chart_class):
        """Test DualChartPlotter initialization with chart2_data."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart
        mock_chart_class.return_value = mock_chart

        plotter = DualChartPlotter(chart_data, chart2_data)

        assert plotter.chart_data is chart_data
        assert plotter.chart2_data is chart2_data

    @patch("src.ui.models.on_timeframe_change")
    @patch("src.ui.models.on_maximize")
    @patch("src.ui.models.plot_indicators")
    @patch("src.ui.models.plot_chart")
    def test_setup(
        self,
        mock_plot_chart,
        mock_plot_indicators,
        mock_on_maximize,
        mock_on_timeframe_change,
    ):
        """Test DualChartPlotter setup."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart
        mock_chart.topbar.textbox = Mock()
        mock_chart.topbar.button = Mock()
        mock_chart.topbar.switcher = Mock()
        mock_right_chart.topbar.textbox = Mock()
        mock_right_chart.topbar.button = Mock()
        mock_right_chart.topbar.switcher = Mock()

        chart_data.current_timeframe = "1D"
        chart2_data.current_timeframe = "1m"

        mock_df1 = pd.DataFrame({"close": [100, 101, 102]})
        mock_metadata1 = {"ticker": "AAPL", "timeframe": "1D"}
        chart_data.load_chart.return_value = (mock_df1, mock_metadata1)

        mock_df2 = pd.DataFrame({"close": [200, 201, 202]})
        mock_metadata2 = {"ticker": "AAPL", "timeframe": "1m"}
        chart2_data.load_chart.return_value = (mock_df2, mock_metadata2)

        mock_plot_chart.return_value = ["drawing1"]

        with patch("src.ui.models.Chart", return_value=mock_chart):
            plotter = DualChartPlotter(chart_data, chart2_data)
            plotter.setup()

        # Verify data loading
        chart_data.load_chart.assert_called_once_with(0)
        chart2_data.load_chart.assert_called_once_with(0)

        # Verify plotting
        assert mock_plot_chart.call_count == 2
        assert mock_plot_indicators.call_count == 2

        # Verify UI elements added
        assert mock_chart.topbar.textbox.call_count == 2  # number and separator
        assert mock_chart.topbar.button.call_count == 1  # maximize button
        assert mock_chart.topbar.switcher.call_count == 1  # timeframe switcher

        # Verify hotkeys bound
        assert mock_chart.hotkey.call_count == 3

    @patch("src.ui.models.plot_chart")
    def test_update_chart_next(self, mock_plot_chart):
        """Test updating dual chart with next direction."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart

        chart_data.next_chart.return_value = (
            pd.DataFrame({"close": [100]}),
            {"ticker": "AAPL"},
        )
        chart2_data.next_chart.return_value = (
            pd.DataFrame({"close": [200]}),
            {"ticker": "AAPL"},
        )
        mock_plot_chart.return_value = ["drawing"]

        with patch("src.ui.models.Chart", return_value=mock_chart):
            plotter = DualChartPlotter(chart_data, chart2_data)
            plotter.drawing_ids = []

            plotter.update_chart("next")

        # Verify both charts updated
        chart_data.next_chart.assert_called_once()
        chart2_data.next_chart.assert_called_once()
        assert mock_plot_chart.call_count == 2

    @patch("src.ui.models.plot_chart")
    def test_update_chart_previous(self, mock_plot_chart):
        """Test updating dual chart with previous direction."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart

        chart_data.previous_chart.return_value = (
            pd.DataFrame({"close": [100]}),
            {"ticker": "AAPL"},
        )
        chart2_data.previous_chart.return_value = (
            pd.DataFrame({"close": [200]}),
            {"ticker": "AAPL"},
        )
        mock_plot_chart.return_value = ["drawing"]

        with patch("src.ui.models.Chart", return_value=mock_chart):
            plotter = DualChartPlotter(chart_data, chart2_data)
            plotter.drawing_ids = []

            plotter.update_chart("previous")

        # Verify both charts updated
        chart_data.previous_chart.assert_called_once()
        chart2_data.previous_chart.assert_called_once()
        assert mock_plot_chart.call_count == 2

    def test_clear_drawings(self):
        """Test clearing drawings in dual chart."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart

        drawing1 = Mock()
        drawing2 = Mock()

        with patch("src.ui.models.Chart", return_value=mock_chart):
            plotter = DualChartPlotter(chart_data, chart2_data)
            plotter.drawing_ids = [drawing1, drawing2]

            plotter.clear_drawings()

        drawing1.delete.assert_called_once()
        drawing2.delete.assert_called_once()

    @patch("src.ui.models.save_screenshot_dual")
    def test_bind_hotkeys(self, mock_save_screenshot_dual):
        """Test hotkey binding in dual chart."""
        chart_data = Mock()
        chart2_data = Mock()

        mock_chart = Mock()
        mock_right_chart = Mock()
        mock_chart.create_subchart.return_value = mock_right_chart

        with patch("src.ui.models.Chart", return_value=mock_chart):
            plotter = DualChartPlotter(chart_data, chart2_data)
            plotter.bind_hotkeys()

        # Verify hotkeys were bound
        assert mock_chart.hotkey.call_count == 3

        # Test screenshot function
        calls = mock_chart.hotkey.call_args_list
        screenshot_func = calls[2][1]["func"]

        screenshot_func(None)
        mock_save_screenshot_dual.assert_called_once_with(
            mock_chart, mock_right_chart, chart_data, chart2_data
        )


class TestDoubleClickTracker:
    """Test cases for the DoubleClickTracker class."""

    def test_init(self):
        """Test DoubleClickTracker initialization."""
        tracker = DoubleClickTracker()
        assert tracker.first_click is None
        assert tracker.click_count == 0
        assert tracker.current_drawings == {}

    def test_first_click(self):
        """Test handling first click."""
        tracker = DoubleClickTracker()
        test_data = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        
        with patch('src.ui.models.logger') as mock_logger:
            tracker.handle_click(test_data)
        
        assert tracker.click_count == 1
        assert tracker.first_click == test_data
        mock_logger.info.assert_called_once()

    def test_second_click_distance_calculation(self):
        """Test distance calculation on second click."""
        tracker = DoubleClickTracker()
        
        # First click
        first_click = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        tracker.handle_click(first_click)
        
        # Second click - 1 day later, $50 higher
        second_click = {
            'timestamp': datetime(2023, 1, 2, 10, 0, 0),
            'price': 150.0
        }
        
        with patch('src.ui.models.logger') as mock_logger:
            tracker.handle_click(second_click)
        
        # Should have logged distance calculation
        calls = mock_logger.info.call_args_list
        assert len(calls) == 2  # First click + distance calculation
        
        # Check that the distance calculation was logged
        distance_log = calls[1][0][0]
        assert "Distance calculation" in distance_log
        assert "Days: 1.00" in distance_log
        assert "Price difference: 50.00" in distance_log
        
        # Tracker should be reset after second click
        assert tracker.click_count == 0
        assert tracker.first_click is None

    def test_reset(self):
        """Test tracker reset functionality."""
        tracker = DoubleClickTracker()
        tracker.first_click = {'timestamp': datetime.now(), 'price': 100.0}
        tracker.click_count = 1
        
        tracker.reset()
        
        assert tracker.first_click is None
        assert tracker.click_count == 0

    def test_price_difference_calculation(self):
        """Test price difference calculation with different scenarios."""
        tracker = DoubleClickTracker()
        
        # Test case: second price lower than first
        first_click = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 200.0
        }
        second_click = {
            'timestamp': datetime(2023, 1, 1, 11, 0, 0),
            'price': 150.0
        }
        
        tracker.handle_click(first_click)
        
        with patch('src.ui.models.logger') as mock_logger:
            tracker.handle_click(second_click)
        
        # Should calculate absolute difference
        distance_log = mock_logger.info.call_args_list[1][0][0]
        assert "Price difference: 50.00" in distance_log

    def test_time_difference_calculation(self):
        """Test time difference calculation in days."""
        tracker = DoubleClickTracker()
        
        # Test case: 12 hours difference
        first_click = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        second_click = {
            'timestamp': datetime(2023, 1, 1, 22, 0, 0),
            'price': 100.0
        }
        
        tracker.handle_click(first_click)
        
        with patch('src.ui.models.logger') as mock_logger:
            tracker.handle_click(second_click)
        
        # Should calculate 0.5 days (12 hours)
        distance_log = mock_logger.info.call_args_list[1][0][0]
        assert "Days: 0.50" in distance_log

    def test_set_chart(self):
        """Test setting chart instance."""
        tracker = DoubleClickTracker()
        mock_chart = Mock()
        mock_chart.id = "test_chart"
        
        tracker.set_chart(mock_chart)
        
        assert tracker.chart == mock_chart
        assert "test_chart" in tracker.current_drawings

    def test_visual_markers_first_click(self):
        """Test adding visual marker for first click."""
        tracker = DoubleClickTracker()
        mock_chart = Mock()
        mock_chart.id = "test_chart"
        mock_marker = Mock()
        mock_chart.marker.return_value = mock_marker
        
        tracker.set_chart(mock_chart)
        
        test_data = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        
        tracker.handle_click(test_data)
        
        # Should have called chart.marker
        mock_chart.marker.assert_called_once_with(
            time=test_data['timestamp'],
            position='below',
            shape='circle',
            color='blue',
            text='1'
        )
        
        # Should have stored the marker in drawings
        assert mock_marker in tracker.current_drawings["test_chart"]

    def test_visual_markers_second_click(self):
        """Test adding visual markers for second click with distance measurement."""
        tracker = DoubleClickTracker()
        mock_chart = Mock()
        mock_chart.id = "test_chart"
        mock_marker1 = Mock()
        mock_marker2 = Mock()
        mock_trend_line = Mock()
        mock_horizontal_line = Mock()
        
        mock_chart.marker.side_effect = [mock_marker1, mock_marker2]
        mock_chart.trend_line.return_value = mock_trend_line
        mock_chart.horizontal_line.return_value = mock_horizontal_line
        
        tracker.set_chart(mock_chart)
        
        # First click
        first_click = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        tracker.handle_click(first_click)
        
        # Second click
        second_click = {
            'timestamp': datetime(2023, 1, 2, 10, 0, 0),
            'price': 150.0
        }
        
        with patch('src.ui.models.logger'):
            tracker.handle_click(second_click)
        
        # Should have called chart methods
        assert mock_chart.marker.call_count == 2
        mock_chart.trend_line.assert_called_once()
        mock_chart.horizontal_line.assert_called_once()
        
        # Tracker should be reset after second click (click count and first_click)
        assert tracker.click_count == 0
        assert tracker.first_click is None

    def test_clear_drawings(self):
        """Test clearing visual drawings."""
        tracker = DoubleClickTracker()
        
        # Mock drawings with delete method
        drawing1 = Mock()
        drawing2 = Mock()
        tracker.current_drawings = {"chart1": [drawing1], "chart2": [drawing2]}
        
        tracker.clear_drawings()
        
        # Should have called delete on all drawings
        drawing1.delete.assert_called_once()
        drawing2.delete.assert_called_once()
        
        # Should have cleared the dictionary
        assert len(tracker.current_drawings) == 0

    def test_on_chart_click2_callback(self):
        """Test the chart click callback function."""
        mock_chart = Mock()
        test_data = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        
        # Reset the global tracker for clean test
        double_click_tracker.reset()
        
        with patch('src.ui.models.double_click_tracker') as mock_tracker:
            on_chart_click2(test_data, mock_chart)
            
            # Should have set chart and handled click
            mock_tracker.set_chart.assert_called_once_with(mock_chart)
            mock_tracker.handle_click.assert_called_once_with(test_data)

    def test_multi_chart_support(self):
        """Test that tracker can handle multiple charts."""
        tracker = DoubleClickTracker()
        
        # Setup two mock charts
        chart1 = Mock()
        chart1.id = "chart1"
        chart2 = Mock()
        chart2.id = "chart2"
        
        marker1 = Mock()
        marker2 = Mock()
        chart1.marker.return_value = marker1
        chart2.marker.return_value = marker2
        
        # First click on chart1
        tracker.set_chart(chart1)
        test_data1 = {
            'timestamp': datetime(2023, 1, 1, 10, 0, 0),
            'price': 100.0
        }
        tracker.handle_click(test_data1)
        
        # Second click on chart2 (should work across charts)
        tracker.set_chart(chart2)
        test_data2 = {
            'timestamp': datetime(2023, 1, 2, 10, 0, 0),
            'price': 150.0
        }
        
        with patch('src.ui.models.logger'):
            tracker.handle_click(test_data2)
        
        # Should have drawings in both charts
        assert len(tracker.current_drawings) == 2
        assert "chart1" in tracker.current_drawings
        assert "chart2" in tracker.current_drawings
        assert marker1 in tracker.current_drawings["chart1"]
        assert marker2 in tracker.current_drawings["chart2"]
