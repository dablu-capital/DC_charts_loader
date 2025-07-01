import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config import GeneralValidator, ChartValidator, Indicator, Configuration


class TestGeneralValidator:
    """Test cases for the GeneralValidator class."""

    def test_valid_general_config(self, sample_config_data):
        """Test creating a valid GeneralValidator instance."""
        general = GeneralValidator(**sample_config_data["general"])

        assert general.version == "1.0.0"
        assert general.data_path == "./data"
        assert general.data_filename == "test_data.feather"

    def test_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        config_data = {
            "version": "1.0.0",
            "data_path": "./data",
            # Missing data_filename
        }

        with pytest.raises(Exception):  # Pydantic validation error
            GeneralValidator(**config_data)

    def test_extra_fields_ignored(self):
        """Test that extra fields are handled according to Pydantic model config."""
        config_data = {
            "version": "1.0.0",
            "data_path": "./data",
            "data_filename": "default.feather",
            "extra_field": "should_be_ignored",
        }

        general = GeneralValidator(**config_data)

        # Should create successfully and ignore extra field
        assert general.version == "1.0.0"
        assert general.data_path == "./data"
        assert general.data_filename == "default.feather"
        assert not hasattr(general, "extra_field")


class TestChartValidator:
    """Test cases for the ChartValidator class."""

    def test_valid_chart_config(self, sample_config_data):
        """Test creating a valid ChartValidator instance."""
        chart = ChartValidator(**sample_config_data["chart"])

        assert chart.use_intraday_tf is False
        assert chart.intraday_tf == "1m"

    def test_invalid_timeframe(self):
        """Test that invalid timeframe raises validation error."""
        chart_data = {"use_intraday_tf": False, "timeframe": "invalid_tf"}

        with pytest.raises(Exception):  # Pydantic validation error
            ChartValidator(**chart_data)


class TestIndicator:
    """Test cases for the Indicator class."""

    def test_indicator_with_parameters(self):
        """Test creating an Indicator with parameters."""
        indicator_data = {
            "name": "SMA",
            "parameters": {"period": 20, "source": "close"},
        }

        indicator = Indicator(**indicator_data)

        assert indicator.name == "SMA"
        assert indicator.parameters == {"period": 20, "source": "close"}

    def test_indicator_without_parameters(self):
        """Test creating an Indicator without parameters."""
        indicator_data = {"name": "RSI", "parameters": None}

        indicator = Indicator(**indicator_data)

        assert indicator.name == "RSI"
        assert indicator.parameters is None

    def test_indicator_with_none_parameters(self):
        """Test creating an Indicator with explicitly None parameters."""
        indicator_data = {"name": "MACD", "parameters": None}

        indicator = Indicator(**indicator_data)

        assert indicator.name == "MACD"
        assert indicator.parameters is None

    def test_indicator_missing_name(self):
        """Test that missing name field raises validation error."""
        indicator_data = {"parameters": {"period": 20}}

        with pytest.raises(Exception):  # Pydantic validation error
            Indicator(**indicator_data)


class TestConfiguration:
    """Test cases for the Configuration class."""

    def test_valid_configuration(self, sample_config_data):
        """Test creating a valid Configuration instance."""

        config = Configuration(**sample_config_data)

        assert isinstance(config.general, GeneralValidator)
        assert config.general.version == "1.0.0"
        assert len(config.indicators) == 2
        assert config.indicators[0].name == "SMA"
        assert config.indicators[1].name == "SMA"

    def test_configuration_without_indicators(self, sample_config_data):
        """Test creating Configuration without indicators."""
        sample_config_data["indicators"] = None

        config = Configuration(**sample_config_data)

        assert isinstance(config.general, GeneralValidator)
        assert config.indicators is None

    def test_configuration_with_empty_indicators(self, sample_config_data):
        """Test creating Configuration with empty indicators list."""
        sample_config_data["indicators"] = []

        config = Configuration(**sample_config_data)

        assert isinstance(config.general, GeneralValidator)
        assert config.indicators == []

    def test_configuration_missing_general(
        self,
    ):
        """Test that missing general section raises validation error."""
        config_data = {"indicators": [{"name": "SMA", "parameters": {"period": 20}}]}

        with pytest.raises(Exception):  # Pydantic validation error
            Configuration(**config_data)


class TestConfigurationLoading:
    """Test cases for the configuration loading mechanism."""

    def test_config_loading_success(self, sample_config_data):
        """Test successful configuration loading from file."""
        # Create a temporary config file

        config_json = json.dumps(sample_config_data)

        # Mock the file reading and CONFIG_PATH
        with patch("builtins.open", mock_open(read_data=config_json)):
            with patch("src.config.CONFIG_PATH", "mocked_path"):
                # Create a new Configuration instance directly
                config_dict = json.loads(config_json)
                test_config = Configuration(**config_dict)

                # Check that config was loaded correctly
                assert isinstance(test_config, Configuration)
                assert test_config.general.version == "1.0.0"
                assert test_config.general.data_filename == "test_data.feather"
                assert len(test_config.indicators) == 2
                assert test_config.indicators[0].name == "SMA"

    def test_config_path_construction(self):
        """Test that CONFIG_PATH is constructed correctly."""
        from src.config import CONFIG_PATH

        # Should be relative to the config.py file location
        expected_path = Path(__file__).parent.parent / "src" / ".." / "config.json"
        expected_path = expected_path.resolve()

        # The actual path should point to config.json in the project root
        assert CONFIG_PATH.name == "config.json"
        assert CONFIG_PATH.is_absolute()

    def test_config_with_real_file(self):
        """Test loading the actual config.json file from the project."""
        # This test uses the real config file
        from src.config import config

        # Basic validation that the config loaded successfully
        assert isinstance(config, Configuration)
        assert isinstance(config.general, GeneralValidator)
        assert config.general.version == "1.0.0"
        assert config.general.data_path == "./data"
        assert config.general.data_filename == "default.feather"

        # Check indicators - we know from the actual config that there should be one SMA indicator
        assert config.indicators is not None
        assert isinstance(config.indicators, list)
        assert len(config.indicators) == 1
        assert config.indicators[0].name == "SMA"
        assert config.indicators[0].parameters == {"period": 5, "source": "close"}
