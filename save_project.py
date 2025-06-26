import src.imgur_api as imgur_api
from pathlib import Path
from src.config import config
import pyimgur

PROJECT_NAME = input("Enter project name (default: test): ") or "test"

screenshots_path = Path().cwd() / "screenshots"
client_id = config.imgur.client_id
client_secret = config.imgur.client_secret
refresh_token = config.imgur.refresh_token

if client_id == "my_client_id":
    raise ValueError(
        "Please set your Imgur client_id in config.json. "
        "You can get it from https://api.imgur.com/oauth2/addclient"
    )

# connection to imgur api
im = imgur_api.connect(client_id, client_secret, refresh_token)
# im = pyimgur.Imgur(client_id=client_id, client_secret=client_secret)  # debug
# upload
img_list = imgur_api.upload_screenshots(
    screenshots_path=screenshots_path, project_name=PROJECT_NAME, im=im
)
print(f"moved screenshots to IMGUR:")
for img in img_list:
    print(img.link)

# move screenshots to project folder
project_path = imgur_api.move_screenshots(
    screenshots_path=screenshots_path, project_name=PROJECT_NAME
)
print(f"moved screenshots to project folder: {project_path}")

# create lists for excel file
file_list = list(project_path.glob("*.png"))


# make excel file
xl_path = imgur_api.make_excel(
    file_list=file_list,
    img_list=img_list,
    project_path=project_path,
    project_name=PROJECT_NAME,
)

print(f"Project folder created: {xl_path}")
