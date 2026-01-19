from enum import Enum
from os.path import dirname, join
from typing import TypedDict


class Marketplace(str, Enum):
    EBAY = "ebay"


class OAuth2Settings(TypedDict):
    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_url: str
    access_token_url: str
    scope: str


class Pathes:
    BASE_DIR = dirname(dirname(__file__))

    CONFIG = join(BASE_DIR, "config", "config.yaml")
