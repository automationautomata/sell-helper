from typing import TypeVar

from authlib.integrations.starlette_client import StarletteOAuth2App

from ..data import Marketplace

T = TypeVar("T")

MarketplaceMapping = dict[Marketplace, T]

OAuth2ClientMapping = MarketplaceMapping[StarletteOAuth2App]
