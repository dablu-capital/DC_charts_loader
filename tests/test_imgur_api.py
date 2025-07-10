import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pyimgur
import pyimgur.exceptions

from src.imgur_api import (
    upload_image,
    connect,
    create_project_folder,
    move_screenshots,
    upload_screenshots,
    make_excel,
)


class TestUploadImage:
    """Test cases for the upload_image function."""

    def test_upload_image_with_project(self):
        """Test uploading image with project name."""
        image_path = Path("test_image.png")
        im = Mock()
        uploaded_image = Mock()
        im.upload_image.return_value = uploaded_image
        
        result = upload_image(image_path, im, "test_project")
        
        im.upload_image.assert_called_once_with(str(image_path), title="test_project_test_image")
        assert result is uploaded_image

    def test_upload_image_without_project(self):
        """Test uploading image without project name."""
        image_path = Path("test_image.png")
        im = Mock()
        uploaded_image = Mock()
        im.upload_image.return_value = uploaded_image
        
        result = upload_image(image_path, im)
        
        im.upload_image.assert_called_once_with(str(image_path), title="test_image")
        assert result is uploaded_image


class TestConnect:
    """Test cases for the connect function."""

    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_success(self, mock_imgur):
        """Test successful connection with refresh token."""
        mock_im = Mock()
        mock_imgur.return_value = mock_im
        
        result = connect("client_id", "client_secret", "refresh_token")
        
        mock_imgur.assert_called_once_with(
            client_id="client_id",
            client_secret="client_secret",
            refresh_token="refresh_token"
        )
        mock_im.refresh_access_token.assert_called_once()
        assert result is mock_im

    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_initial_exception(self, mock_imgur):
        """Test connection with initial UnexpectedImgurException."""
        mock_im = Mock()
        mock_imgur.side_effect = [
            pyimgur.exceptions.UnexpectedImgurException("Error"),
            mock_im
        ]
        
        result = connect("client_id", "client_secret", "refresh_token")
        
        assert mock_imgur.call_count == 2
        mock_imgur.assert_any_call(
            client_id="client_id",
            client_secret="client_secret",
            refresh_token="refresh_token"
        )
        mock_imgur.assert_any_call(
            client_id="client_id",
            client_secret="client_secret"
        )
        assert result is mock_im

    @patch('builtins.input', return_value="test_pin")
    @patch('builtins.print')
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_authentication_failure(self, mock_imgur, mock_print, mock_input):
        """Test connection with authentication failure."""
        mock_im = Mock()
        mock_im.refresh_access_token.side_effect = pyimgur.AuthenticationError("Auth failed")
        mock_im.authorization_url.return_value = "https://auth.url"
        mock_im.exchange_pin.return_value = ("access_token", "new_refresh_token")
        
        mock_new_im = Mock()
        mock_imgur.side_effect = [mock_im, mock_new_im]
        
        result = connect("client_id", "client_secret", "refresh_token")
        
        mock_im.authorization_url.assert_called_once_with("pin")
        mock_im.exchange_pin.assert_called_once_with("test_pin")
        mock_print.assert_any_call("Authentication failed. Please re-authenticate.")
        mock_print.assert_any_call("Go to the following url to authenticate with your app")
        mock_print.assert_any_call("https://auth.url")
        mock_print.assert_any_call("refresh token: new_refresh_token save it in config.json")
        
        assert mock_imgur.call_count == 2
        mock_imgur.assert_any_call(
            client_id="client_id",
            client_secret="client_secret",
            access_token="access_token"
        )
        assert result is mock_new_im

    @patch('builtins.input', return_value="test_pin")
    @patch('builtins.print')
    @patch('src.imgur_api.pyimgur.Imgur')
    def test_connect_unexpected_exception_during_auth(self, mock_imgur, mock_print, mock_input):
        """Test connection with UnexpectedImgurException during authentication."""
        mock_im = Mock()
        mock_im.refresh_access_token.side_effect = pyimgur.exceptions.UnexpectedImgurException("Unexpected")
        mock_im.authorization_url.return_value = "https://auth.url"
        mock_im.exchange_pin.return_value = ("access_token", "new_refresh_token")
        
        mock_new_im = Mock()
        mock_imgur.side_effect = [mock_im, mock_new_im]
        
        result = connect("client_id", "client_secret", "refresh_token")
        
        mock_im.authorization_url.assert_called_once_with("pin")
        mock_im.exchange_pin.assert_called_once_with("test_pin")
        assert result is mock_new_im


class TestCreateProjectFolder:
    """Test cases for the create_project_folder function."""

    def test_create_project_folder_new(self, tmp_path):
        """Test creating a new project folder."""
        project_name = "test_project"
        
        result = create_project_folder(project_name, tmp_path)
        
        expected_path = tmp_path / project_name
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_project_folder_existing(self, tmp_path):
        """Test creating project folder when one already exists."""
        project_name = "test_project"
        
        # Create existing folder
        existing_folder = tmp_path / project_name
        existing_folder.mkdir()
        
        result = create_project_folder(project_name, tmp_path)
        
        expected_path = tmp_path / f"{project_name}_1"
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_project_folder_multiple_existing(self, tmp_path):
        """Test creating project folder when multiple already exist."""
        project_name = "test_project"
        
        # Create existing folders
        (tmp_path / project_name).mkdir()
        (tmp_path / f"{project_name}_1").mkdir()
        (tmp_path / f"{project_name}_2").mkdir()
        
        result = create_project_folder(project_name, tmp_path)
        
        expected_path = tmp_path / f"{project_name}_3"
        assert result == expected_path
        assert expected_path.exists()
        assert expected_path.is_dir()


class TestMoveScreenshots:
    """Test cases for the move_screenshots function."""

    @patch('src.imgur_api.shutil.move')
    @patch('src.imgur_api.create_project_folder')
    def test_move_screenshots(self, mock_create_project_folder, mock_move, tmp_path):
        """Test moving screenshots to project folder."""
        project_name = "test_project"
        project_path = tmp_path / project_name
        
        # Create test PNG files
        file1 = tmp_path / "test1.png"
        file2 = tmp_path / "test2.png"
        file1.touch()
        file2.touch()
        
        mock_create_project_folder.return_value = project_path
        
        result = move_screenshots(project_name, tmp_path)
        
        mock_create_project_folder.assert_called_once_with(project_name, tmp_path)
        assert result == project_path
        
        # Check that move was called for each file
        assert mock_move.call_count == 2
        mock_move.assert_any_call(str(file1), project_path / "test1.png")
        mock_move.assert_any_call(str(file2), project_path / "test2.png")

    @patch('src.imgur_api.shutil.move')
    @patch('src.imgur_api.create_project_folder')
    def test_move_screenshots_no_files(self, mock_create_project_folder, mock_move, tmp_path):
        """Test moving screenshots when no PNG files exist."""
        project_name = "test_project"
        project_path = tmp_path / project_name
        
        mock_create_project_folder.return_value = project_path
        
        result = move_screenshots(project_name, tmp_path)
        
        mock_create_project_folder.assert_called_once_with(project_name, tmp_path)
        assert result == project_path
        mock_move.assert_not_called()


class TestUploadScreenshots:
    """Test cases for the upload_screenshots function."""

    @patch('src.imgur_api.upload_image')
    def test_upload_screenshots(self, mock_upload_image, tmp_path):
        """Test uploading screenshots."""
        # Create test PNG files
        file1 = tmp_path / "test1.png"
        file2 = tmp_path / "test2.png"
        file1.touch()
        file2.touch()
        
        im = Mock()
        project_name = "test_project"
        
        mock_image1 = Mock()
        mock_image2 = Mock()
        mock_upload_image.side_effect = [mock_image1, mock_image2]
        
        result = upload_screenshots(tmp_path, im, project_name)
        
        assert mock_upload_image.call_count == 2
        mock_upload_image.assert_any_call(file1, im, project_name)
        mock_upload_image.assert_any_call(file2, im, project_name)
        
        assert result == [mock_image1, mock_image2]

    @patch('src.imgur_api.upload_image')
    def test_upload_screenshots_no_files(self, mock_upload_image, tmp_path):
        """Test uploading screenshots when no PNG files exist."""
        im = Mock()
        project_name = "test_project"
        
        result = upload_screenshots(tmp_path, im, project_name)
        
        mock_upload_image.assert_not_called()
        assert result == []


class TestMakeExcel:
    """Test cases for the make_excel function."""

    def test_make_excel(self, tmp_path):
        """Test creating Excel file."""
        # Create mock file list
        file1 = Mock()
        file1.stem = "AAPL_2023-01-15_screenshot"
        file2 = Mock()
        file2.stem = "MSFT_2023-01-16_screenshot"
        file_list = [file1, file2]
        
        # Create mock image list
        img1 = Mock()
        img1.link = "https://imgur.com/image1"
        img2 = Mock()
        img2.link = "https://imgur.com/image2"
        img_list = [img1, img2]
        
        project_name = "test_project"
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            result = make_excel(file_list, img_list, tmp_path, project_name)
            
            expected_path = tmp_path / f"{project_name}_screenshots.xlsx"
            assert result == expected_path
            
            # Verify DataFrame was created correctly
            mock_to_excel.assert_called_once_with(expected_path, index=False)
            
            # Check that DataFrame was created with correct data
            # We need to check the DataFrame construction through the to_excel call
            # Since we can't directly access the DataFrame, we'll verify the call was made

    @patch('pandas.DataFrame')
    def test_make_excel_data_structure(self, mock_dataframe, tmp_path):
        """Test Excel file data structure."""
        # Create mock file list
        file1 = Mock()
        file1.stem = "AAPL_2023-01-15_screenshot"
        file2 = Mock()
        file2.stem = "MSFT_2023-01-16_screenshot"
        file_list = [file1, file2]
        
        # Create mock image list
        img1 = Mock()
        img1.link = "https://imgur.com/image1"
        img2 = Mock()
        img2.link = "https://imgur.com/image2"
        img_list = [img1, img2]
        
        project_name = "test_project"
        
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        result = make_excel(file_list, img_list, tmp_path, project_name)
        
        # Verify DataFrame was created with correct structure
        expected_data = {
            "ticker": ["AAPL", "MSFT"],
            "date": ["2023-01-15", "2023-01-16"],
            "link": ["https://imgur.com/image1", "https://imgur.com/image2"]
        }
        mock_dataframe.assert_called_once_with(expected_data)
        
        # Verify to_excel was called
        expected_path = tmp_path / f"{project_name}_screenshots.xlsx"
        mock_df.to_excel.assert_called_once_with(expected_path, index=False)
        assert result == expected_path