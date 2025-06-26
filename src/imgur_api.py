from typing import Optional
from pathlib import Path
import pyimgur
import pyimgur.exceptions
from src.config import config
import shutil
import pandas as pd


def upload_image(
    image_path: Path,
    im: pyimgur.Imgur,
    project: Optional[str] = None,
) -> pyimgur.Image:
    """
    Uploads an image to Imgur and returns the link.
    """

    image_name = image_path.stem
    if project:
        title = f"{project}_{image_name}"
    else:
        title = image_name
    # handle failed connection or upload
    uploaded_image = im.upload_image(str(image_path), title=title)
    return uploaded_image


def connect(
    client_id: str, client_secret: str, refresh_token: Optional[str] = None
) -> pyimgur.Imgur:
    """
    requests authorization token
    """
    try:
        im = pyimgur.Imgur(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
    except pyimgur.exceptions.UnexpectedImgurException:
        im = pyimgur.Imgur(client_id=client_id, client_secret=client_secret)

    try:
        # Try to authenticate using the refresh token
        im.refresh_access_token()
    except (pyimgur.AuthenticationError, pyimgur.exceptions.UnexpectedImgurException):
        # If authentication fails, request a new authorization URL
        print("Authentication failed. Please re-authenticate.")
        auth_url = im.authorization_url("pin")
        print("Go to the following url to authenticate with your app")
        print(auth_url)

        pin = input("What is the pin? ")
        access_token, refresh_token = im.exchange_pin(pin)
        print(f"refresh token: {refresh_token} save it in config.json")

        return pyimgur.Imgur(
            client_id=client_id, client_secret=client_secret, access_token=access_token
        )
    return im


def create_project_folder(project_name: str, screenshot_folder: Path) -> Path:
    """
    Creates a new project folder in the screenshot folder.
    If a folder with the same name exists, it appends an incrementing number to the name.
    """
    project_path = screenshot_folder / project_name

    # If folder exists, rename it by adding "_1", "_2", etc.
    i = 1
    while project_path.exists():
        project_path = screenshot_folder / f"{project_name}_{i}"
        i += 1

    # Create the new project folder
    project_path.mkdir(exist_ok=True)

    return project_path


def move_screenshots(project_name: str, screenshots_path: Path) -> Path:
    """
    Moves all screenshots from the current directory to the project folder.
    """

    project_path = create_project_folder(project_name, screenshots_path)

    file_list = list(screenshots_path.glob("*.png"))

    # Move all screenshots to the new project folder
    for file in file_list:
        shutil.move(str(file), project_path / file.name)

    return project_path


def upload_screenshots(
    screenshots_path: Path, im: pyimgur.Imgur, project_name: str
) -> list[pyimgur.Image]:
    """
    Uploads all screenshots in the project folder to Imgur.
    """
    file_list = list(screenshots_path.glob("*.png"))

    uploaded_images = []
    for file in file_list:
        uploaded_image = upload_image(file, im, project_name)
        uploaded_images.append(uploaded_image)

    return uploaded_images


def make_excel(
    file_list: list, img_list: list, project_path: Path, project_name: str
) -> Path:
    """
    Creates an Excel file with the screenshot information.
    """
    ticker_list = [file.stem.split("_")[0] for file in file_list]
    date_list = [file.stem.split("_")[1] for file in file_list]
    link_list = [img.link for img in img_list]

    df = pd.DataFrame({"ticker": ticker_list, "date": date_list, "link": link_list})

    file_path = project_path / f"{project_name}_screenshots.xlsx"

    df.to_excel(file_path, index=False)

    return file_path
