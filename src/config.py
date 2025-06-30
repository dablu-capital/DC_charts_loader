import json
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Annotated
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


class GeneralValidator(BaseModel):
    """
    General configuration validator.
    """

    version: str
    data_path: str
    data_filename: str


class ChartValidator(BaseModel):
    use_intraday_tf: bool
    intraday_tf: Literal["1m", "5m", "30m", "1h", "4h"]
    n_days_intraday: Annotated[int, Field(gt=0, le=20)]
    n_days_daily: Annotated[int, Field(gt=0, le=365)]
    show_watermark: bool


class Indicator(BaseModel):
    """
    Represents a technical indicator configuration.
    """

    name: str
    parameters: Optional[dict]


class ImgurValidator(BaseModel):
    """
    Validator for Imgur configuration.
    """

    client_id: str
    client_secret: str
    refresh_token: Optional[str] = None


class Configuration(BaseModel):
    """
    Main configuration class that includes general settings and specific configurations.
    """

    general: GeneralValidator
    chart: ChartValidator
    indicators: Optional[List[Indicator]]
    imgur: ImgurValidator


# Load the JSON data from the file into a dictionary
with open(CONFIG_PATH, "r") as file:
    config_dict = json.load(file)

# Parse the dictionary into a Configuration object
config = Configuration(**config_dict)
