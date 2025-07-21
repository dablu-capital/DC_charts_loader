"""Integration tests for CLI functionality."""

import json
import tempfile
from pathlib import Path
import pytest
from src.cli import FileSelector, MainMenu


class TestFileSelector:
    """Test FileSelector functionality."""
    
    def test_get_available_files_empty_dir(self):
        """Test file selection with empty data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fs = FileSelector(data_dir=temp_dir)
            files = fs.get_available_files()
            assert files == []
    
    def test_get_available_files_filters_correctly(self):
        """Test that file filtering works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.feather").touch()
            (temp_path / "main_data.feather").touch()  # Should be filtered out
            (temp_path / "main_min_data.feather").touch()  # Should be filtered out
            (temp_path / "other.feather").touch()
            (temp_path / "not_feather.txt").touch()  # Should be ignored
            
            fs = FileSelector(data_dir=temp_dir)
            files = fs.get_available_files()
            
            # Only main.feather and other.feather should be returned
            assert sorted(files) == ["main.feather", "other.feather"]
    
    def test_save_and_load_last_file(self):
        """Test saving and loading last selected file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write('{}')
            temp_file_path = temp_file.name
        
        try:
            fs = FileSelector(config_file=temp_file_path)
            
            # Initially no last file
            assert fs.load_last_file() is None
            
            # Save a file
            fs.save_last_file("test.feather")
            
            # Load it back
            assert fs.load_last_file() == "test.feather"
            
            # Verify it's in the config file
            with open(temp_file_path, 'r') as f:
                config_data = json.load(f)
            assert config_data["cli"]["last_file"] == "test.feather"
            
        finally:
            Path(temp_file_path).unlink()
    
    def test_save_last_file_creates_cli_section(self):
        """Test that CLI section is created if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            # Write config without CLI section
            temp_file.write('{"existing": "data"}')
            temp_file_path = temp_file.name
        
        try:
            fs = FileSelector(config_file=temp_file_path)
            fs.save_last_file("test.feather")
            
            # Verify CLI section was created
            with open(temp_file_path, 'r') as f:
                config_data = json.load(f)
            
            assert "cli" in config_data
            assert config_data["cli"]["last_file"] == "test.feather"
            assert config_data["existing"] == "data"  # Existing data preserved
            
        finally:
            Path(temp_file_path).unlink()


class TestMainMenu:
    """Test MainMenu functionality."""
    
    def test_main_menu_initialization(self):
        """Test that MainMenu initializes correctly."""
        menu = MainMenu()
        assert menu.project_root.exists()
        assert menu.project_root.name == "DC_charts_loader"


class TestCLIIntegration:
    """Test CLI integration with existing codebase."""
    
    def test_file_selector_with_real_data_dir(self):
        """Test file selector with the actual data directory."""
        fs = FileSelector(data_dir="data")
        files = fs.get_available_files()
        
        # Should find at least the default.feather file
        assert "default.feather" in files
        
        # Verify filtering works - no _data.feather or _min_data.feather files
        for file in files:
            assert not file.endswith("_data.feather")
            assert not file.endswith("_min_data.feather")
            assert file.endswith(".feather")
    
    def test_config_integration(self):
        """Test that the config system works with CLI additions."""
        from src.config import config
        
        # Verify CLI config is loaded
        assert hasattr(config, 'cli')
        assert config.cli is not None
        assert hasattr(config.cli, 'last_file')
        assert hasattr(config.cli, 'data_directory')
        assert hasattr(config.cli, 'screenshot_directory')