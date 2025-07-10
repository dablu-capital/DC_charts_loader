import pytest
from unittest.mock import Mock

from src.ui import (
    plot_chart,
    plot_line,
    plot_indicators,
    save_screenshot,
    save_screenshot_dual,
    on_maximize,
    on_timeframe_change,
    FULLSCREEN,
    CLOSE,
    ChartPlotter,
    SingleChartPlotter,
    DualChartPlotter,
)


class TestUIInit:
    """Test cases for the UI module initialization."""

    def test_imports(self):
        """Test that all expected functions and classes are available."""
        # Test function imports
        assert callable(plot_chart)
        assert callable(plot_line)
        assert callable(plot_indicators)
        assert callable(save_screenshot)
        assert callable(save_screenshot_dual)
        assert callable(on_maximize)
        assert callable(on_timeframe_change)
        
        # Test constant imports
        assert FULLSCREEN == "⬜"
        assert CLOSE == "×"
        
        # Test class imports
        assert ChartPlotter is not None
        assert SingleChartPlotter is not None
        assert DualChartPlotter is not None

    def test_constants(self):
        """Test that constants have correct values."""
        assert isinstance(FULLSCREEN, str)
        assert isinstance(CLOSE, str)
        assert len(FULLSCREEN) == 1
        assert len(CLOSE) == 1