"""
Tests for the imgur_api module.
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pyimgur
import pyimgur.exceptions

from src.imgur_api import (
    upload_image,
    connect,
    create_project_folder,
    move_screenshots,
    upload_screenshots,
    make_excel
)


class TestUploadImage:
    """Test cases for upload_image function."""
    
    def test_upload_image_with_project(self):
        """Test uploading an image with a project name."""
        # Setup
        image_path = Path("test_image.png")
        mock_imgur = Mock()
        mock_uploaded_image = Mock()
        mock_imgur.upload_image.return_value = mock_uploaded_image
        
        # Execute
        result = upload_image(image_path, mock_imgur, project="test_project")
        
        # Verify
        mock_imgur.upload_image.assert_called_once_with(
            str(image_path), 
            title="test_project_test_image"
        )
        assert result == mock_uploaded_image
    
    def test_upload_image_without_project(self):
        """Test uploading an image without a project name."""
        # Setup
        image_path = Path("test_image.png")
        mock_imgur = Mock()
        mock_uploaded_image = Mock()
        mock_imgur.upload_image.return_value = mock_uploaded_image
        
        # Execute
        result = upload_image(image_path, mock_imgur, project=None)
        
        # Verify
        mock_imgur.upload_image.assert_called_once_with(
            str(image_path), 
            title="test_image"
        )
        assert result == mock_uploaded_image
    
    def test_upload_image_with_complex_filename(self):
        """Test uploading an image with a complex filename."""
        # Setup
        image_path = Path("AAPL_2023-01-15_chart.png")
        mock_imgur = Mock()
        mock_uploaded_image = Mock()
        mock_imgur.upload_image.return_value = mock_uploaded_image
        
        # Execute
        result = upload_image(image_path, mock_imgur, project="portfolio")
        
        # Verify
        mock_imgur.upload_image.assert_called_once_with(
            str(image_path), 
            title="portfolio_AAPL_2023-01-15_chart"
        )
        assert result == mock_uploaded_image


class TestConnect:
    """Test cases for connect function."""
    
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_successful_with_refresh_token(self, mock_imgur_class):
        """Test successful connection with valid refresh token."""
        # Setup
        mock_imgur = Mock()
        mock_imgur_class.return_value = mock_imgur
        mock_imgur.refresh_access_token.return_value = None  # Success
        
        # Execute
        result = connect("client_id", "client_secret", "refresh_token")
        
        # Verify
        mock_imgur_class.assert_called_once_with(
            client_id="client_id",
            client_secret="client_secret", 
            refresh_token="refresh_token"
        )
        mock_imgur.refresh_access_token.assert_called_once()
        assert result == mock_imgur
    
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_without_refresh_token(self, mock_imgur_class):
        """Test connection without refresh token."""
        # Setup
        mock_imgur = Mock()
        mock_imgur_class.return_value = mock_imgur
        mock_imgur.refresh_access_token.return_value = None
        
        # Execute
        result = connect("client_id", "client_secret", None)
        
        # Verify
        mock_imgur_class.assert_called_once_with(
            client_id="client_id",
            client_secret="client_secret", 
            refresh_token=None
        )
        mock_imgur.refresh_access_token.assert_called_once()
        assert result == mock_imgur
    
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_unexpected_exception_during_init(self, mock_imgur_class):
        """Test handling UnexpectedImgurException during initialization."""
        # Setup
        mock_imgur = Mock()
        mock_imgur.refresh_access_token.return_value = None
        
        mock_imgur_class.side_effect = [
            pyimgur.exceptions.UnexpectedImgurException("Init failed"),
            mock_imgur  # Second call succeeds
        ]
        
        # Execute
        result = connect("client_id", "client_secret", "refresh_token")
        
        # Verify
        assert mock_imgur_class.call_count == 2
        # First call with refresh_token
        mock_imgur_class.assert_any_call(
            client_id="client_id",
            client_secret="client_secret",
            refresh_token="refresh_token"
        )
        # Second call without refresh_token
        mock_imgur_class.assert_any_call(
            client_id="client_id",
            client_secret="client_secret"
        )
        assert result == mock_imgur
    
    @patch('builtins.input', return_value="test_pin")
    @patch('builtins.print')
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_authentication_error_requires_pin(self, mock_imgur_class, mock_print, mock_input):
        """Test handling authentication error that requires PIN input."""
        # Setup
        mock_imgur = Mock()
        mock_imgur_class.return_value = mock_imgur
        mock_imgur.refresh_access_token.side_effect = pyimgur.AuthenticationError("Auth failed")
        mock_imgur.authorization_url.return_value = "http://auth.url"
        mock_imgur.exchange_pin.return_value = ("access_token", "new_refresh_token")
        
        # Mock the final Imgur instance
        mock_final_imgur = Mock()
        mock_imgur_class.side_effect = [mock_imgur, mock_final_imgur]
        
        # Execute
        result = connect("client_id", "client_secret", "refresh_token")
        
        # Verify
        mock_imgur.authorization_url.assert_called_once_with("pin")
        mock_imgur.exchange_pin.assert_called_once_with("test_pin")
        
        # Check that print was called with expected messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "Authentication failed. Please re-authenticate." in print_calls
        assert "Go to the following url to authenticate with your app" in print_calls
        assert "http://auth.url" in print_calls
        assert "refresh token: new_refresh_token save it in config.json" in print_calls
        
        # Verify final Imgur instance creation
        mock_imgur_class.assert_called_with(
            client_id="client_id",
            client_secret="client_secret",
            access_token="access_token"
        )
        assert result == mock_final_imgur
    
    @patch('builtins.input', return_value="test_pin")
    @patch('builtins.print')
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_unexpected_exception_during_auth(self, mock_imgur_class, mock_print, mock_input):
        """Test handling UnexpectedImgurException during authentication."""
        # Setup
        mock_imgur = Mock()
        mock_imgur_class.return_value = mock_imgur
        mock_imgur.refresh_access_token.side_effect = pyimgur.exceptions.UnexpectedImgurException("Auth failed")
        mock_imgur.authorization_url.return_value = "http://auth.url"
        mock_imgur.exchange_pin.return_value = ("access_token", "new_refresh_token")
        
        # Mock the final Imgur instance
        mock_final_imgur = Mock()
        mock_imgur_class.side_effect = [mock_imgur, mock_final_imgur]
        
        # Execute
        result = connect("client_id", "client_secret", "refresh_token")
        
        # Verify authentication flow was triggered
        mock_imgur.authorization_url.assert_called_once_with("pin")
        mock_imgur.exchange_pin.assert_called_once_with("test_pin")
        assert result == mock_final_imgur


class TestCreateProjectFolder:
    """Test cases for create_project_folder function."""
    
    def test_create_project_folder_new_folder(self):
        """Test creating a new project folder when it doesn't exist."""
        # Setup
        mock_screenshot_folder = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path.exists.return_value = False
        mock_screenshot_folder.__truediv__.return_value = mock_project_path
        
        # Execute
        result = create_project_folder("test_project", mock_screenshot_folder)
        
        # Verify
        mock_screenshot_folder.__truediv__.assert_called_once_with("test_project")
        mock_project_path.exists.assert_called_once()
        mock_project_path.mkdir.assert_called_once_with(exist_ok=True)
        assert result == mock_project_path
    
    def test_create_project_folder_existing_folder(self):
        """Test creating a project folder when the name already exists."""
        # Setup
        mock_screenshot_folder = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path_1 = MagicMock()
        
        # First path exists, second doesn't
        mock_project_path.exists.return_value = True
        mock_project_path_1.exists.return_value = False
        
        mock_screenshot_folder.__truediv__.side_effect = [
            mock_project_path,  # "test_project"
            mock_project_path_1  # "test_project_1"
        ]
        
        # Execute
        result = create_project_folder("test_project", mock_screenshot_folder)
        
        # Verify
        assert mock_screenshot_folder.__truediv__.call_count == 2
        mock_screenshot_folder.__truediv__.assert_any_call("test_project")
        mock_screenshot_folder.__truediv__.assert_any_call("test_project_1")
        mock_project_path_1.mkdir.assert_called_once_with(exist_ok=True)
        assert result == mock_project_path_1
    
    def test_create_project_folder_multiple_existing_folders(self):
        """Test creating a project folder when multiple incremented names exist."""
        # Setup
        mock_screenshot_folder = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path_1 = MagicMock()
        mock_project_path_2 = MagicMock()
        
        # First two paths exist, third doesn't
        mock_project_path.exists.return_value = True
        mock_project_path_1.exists.return_value = True
        mock_project_path_2.exists.return_value = False
        
        mock_screenshot_folder.__truediv__.side_effect = [
            mock_project_path,    # "test_project"
            mock_project_path_1,  # "test_project_1"
            mock_project_path_2   # "test_project_2"
        ]
        
        # Execute
        result = create_project_folder("test_project", mock_screenshot_folder)
        
        # Verify
        assert mock_screenshot_folder.__truediv__.call_count == 3
        mock_screenshot_folder.__truediv__.assert_any_call("test_project")
        mock_screenshot_folder.__truediv__.assert_any_call("test_project_1")
        mock_screenshot_folder.__truediv__.assert_any_call("test_project_2")
        mock_project_path_2.mkdir.assert_called_once_with(exist_ok=True)
        assert result == mock_project_path_2


class TestMoveScreenshots:
    """Test cases for move_screenshots function."""
    
    @patch('src.imgur_api.shutil.move')
    @patch('src.imgur_api.create_project_folder')
    def test_move_screenshots_success(self, mock_create_folder, mock_shutil_move):
        """Test successfully moving screenshots to project folder."""
        # Setup
        mock_screenshots_path = MagicMock()
        mock_project_path = MagicMock()
        mock_create_folder.return_value = mock_project_path
        
        # Mock file list
        mock_file1 = MagicMock()
        mock_file1.name = "file1.png"
        mock_file2 = MagicMock()
        mock_file2.name = "file2.png"
        mock_screenshots_path.glob.return_value = [mock_file1, mock_file2]
        
        # Mock project_path / file.name
        mock_project_path.__truediv__.side_effect = lambda x: f"project/{x}"
        
        # Execute
        result = move_screenshots("test_project", mock_screenshots_path)
        
        # Verify
        mock_create_folder.assert_called_once_with("test_project", mock_screenshots_path)
        mock_screenshots_path.glob.assert_called_once_with("*.png")
        
        # Verify shutil.move calls
        assert mock_shutil_move.call_count == 2
        mock_shutil_move.assert_any_call(str(mock_file1), "project/file1.png")
        mock_shutil_move.assert_any_call(str(mock_file2), "project/file2.png")
        
        assert result == mock_project_path
    
    @patch('src.imgur_api.shutil.move')
    @patch('src.imgur_api.create_project_folder')
    def test_move_screenshots_no_files(self, mock_create_folder, mock_shutil_move):
        """Test moving screenshots when no PNG files exist."""
        # Setup
        mock_screenshots_path = MagicMock()
        mock_project_path = MagicMock()
        mock_create_folder.return_value = mock_project_path
        mock_screenshots_path.glob.return_value = []  # No files
        
        # Execute
        result = move_screenshots("test_project", mock_screenshots_path)
        
        # Verify
        mock_create_folder.assert_called_once_with("test_project", mock_screenshots_path)
        mock_screenshots_path.glob.assert_called_once_with("*.png")
        mock_shutil_move.assert_not_called()  # No files to move
        assert result == mock_project_path


class TestUploadScreenshots:
    """Test cases for upload_screenshots function."""
    
    @patch('src.imgur_api.upload_image')
    def test_upload_screenshots_success(self, mock_upload_image):
        """Test successfully uploading all screenshots."""
        # Setup
        mock_screenshots_path = MagicMock()
        mock_imgur = MagicMock()
        
        # Mock file list
        mock_file1 = MagicMock()
        mock_file2 = MagicMock()
        mock_screenshots_path.glob.return_value = [mock_file1, mock_file2]
        
        # Mock uploaded images
        mock_img1 = MagicMock()
        mock_img2 = MagicMock()
        mock_upload_image.side_effect = [mock_img1, mock_img2]
        
        # Execute
        result = upload_screenshots(mock_screenshots_path, mock_imgur, "test_project")
        
        # Verify
        mock_screenshots_path.glob.assert_called_once_with("*.png")
        assert mock_upload_image.call_count == 2
        mock_upload_image.assert_any_call(mock_file1, mock_imgur, "test_project")
        mock_upload_image.assert_any_call(mock_file2, mock_imgur, "test_project")
        
        assert result == [mock_img1, mock_img2]
    
    @patch('src.imgur_api.upload_image')
    def test_upload_screenshots_no_files(self, mock_upload_image):
        """Test uploading screenshots when no files exist."""
        # Setup
        mock_screenshots_path = MagicMock()
        mock_imgur = MagicMock()
        mock_screenshots_path.glob.return_value = []  # No files
        
        # Execute
        result = upload_screenshots(mock_screenshots_path, mock_imgur, "test_project")
        
        # Verify
        mock_screenshots_path.glob.assert_called_once_with("*.png")
        mock_upload_image.assert_not_called()
        assert result == []


class TestMakeExcel:
    """Test cases for make_excel function."""
    
    @patch('pandas.DataFrame.to_excel')
    @patch('pandas.DataFrame')
    def test_make_excel_success(self, mock_dataframe_class, mock_to_excel):
        """Test successfully creating an Excel file."""
        # Setup
        mock_project_path = MagicMock()
        mock_file_path = MagicMock()
        mock_project_path.__truediv__.return_value = mock_file_path
        
        # Mock files with proper stem attributes
        mock_file1 = Mock()
        mock_file1.stem = "AAPL_2023-01-15"
        mock_file2 = Mock()
        mock_file2.stem = "MSFT_2023-01-16"
        file_list = [mock_file1, mock_file2]
        
        # Mock images with link attributes
        mock_img1 = Mock()
        mock_img1.link = "http://imgur.com/img1"
        mock_img2 = Mock()
        mock_img2.link = "http://imgur.com/img2"
        img_list = [mock_img1, mock_img2]
        
        # Mock DataFrame
        mock_df = Mock()
        mock_dataframe_class.return_value = mock_df
        
        # Execute
        result = make_excel(file_list, img_list, mock_project_path, "test_project")
        
        # Verify DataFrame creation
        expected_data = {
            "ticker": ["AAPL", "MSFT"],
            "date": ["2023-01-15", "2023-01-16"],
            "link": ["http://imgur.com/img1", "http://imgur.com/img2"]
        }
        mock_dataframe_class.assert_called_once_with(expected_data)
        
        # Verify file path creation
        mock_project_path.__truediv__.assert_called_once_with("test_project_screenshots.xlsx")
        
        # Verify Excel export
        mock_df.to_excel.assert_called_once_with(mock_file_path, index=False)
        
        assert result == mock_file_path
    
    @patch('pandas.DataFrame.to_excel')
    @patch('pandas.DataFrame')
    def test_make_excel_complex_filenames(self, mock_dataframe_class, mock_to_excel):
        """Test creating Excel file with complex filenames."""
        # Setup
        mock_project_path = MagicMock()
        mock_file_path = MagicMock()
        mock_project_path.__truediv__.return_value = mock_file_path
        
        # Mock files with complex stem attributes
        mock_file1 = Mock()
        mock_file1.stem = "AAPL_2023-01-15_chart_v2"  # More complex filename
        mock_file2 = Mock()
        mock_file2.stem = "GOOGL_2023-12-31_analysis"
        file_list = [mock_file1, mock_file2]
        
        # Mock images
        mock_img1 = Mock()
        mock_img1.link = "http://imgur.com/complex1"
        mock_img2 = Mock()
        mock_img2.link = "http://imgur.com/complex2"
        img_list = [mock_img1, mock_img2]
        
        # Mock DataFrame
        mock_df = Mock()
        mock_dataframe_class.return_value = mock_df
        
        # Execute
        result = make_excel(file_list, img_list, mock_project_path, "complex_project")
        
        # Verify DataFrame creation with split filenames
        expected_data = {
            "ticker": ["AAPL", "GOOGL"],  # First part before underscore
            "date": ["2023-01-15", "2023-12-31"],  # Second part before underscore
            "link": ["http://imgur.com/complex1", "http://imgur.com/complex2"]
        }
        mock_dataframe_class.assert_called_once_with(expected_data)
        
        # Verify file path creation
        mock_project_path.__truediv__.assert_called_once_with("complex_project_screenshots.xlsx")
        
        assert result == mock_file_path
    
    @patch('pandas.DataFrame.to_excel')
    @patch('pandas.DataFrame')
    def test_make_excel_empty_lists(self, mock_dataframe_class, mock_to_excel):
        """Test creating Excel file with empty file and image lists."""
        # Setup
        mock_project_path = MagicMock()
        mock_file_path = MagicMock()
        mock_project_path.__truediv__.return_value = mock_file_path
        
        file_list = []
        img_list = []
        
        # Mock DataFrame
        mock_df = Mock()
        mock_dataframe_class.return_value = mock_df
        
        # Execute
        result = make_excel(file_list, img_list, mock_project_path, "empty_project")
        
        # Verify DataFrame creation with empty data
        expected_data = {
            "ticker": [],
            "date": [],
            "link": []
        }
        mock_dataframe_class.assert_called_once_with(expected_data)
        
        # Verify file operations
        mock_project_path.__truediv__.assert_called_once_with("empty_project_screenshots.xlsx")
        mock_df.to_excel.assert_called_once_with(mock_file_path, index=False)
        
        assert result == mock_file_path