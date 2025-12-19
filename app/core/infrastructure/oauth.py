from uuid import UUID

from app.core.domain.entities.user import User
from shared.ebay_api.auth import EbayAuthClient

from ...config import EbayConfig


class EbayOAuth:
    def __init__(self, auth_api: EbayAuthClient):
        self._auth_api = auth_api

    def auth(self, user: User, code: str):
        self._auth_api.tokens_by_authorization_code(code, user.uuid)

    def generate_auth_url(self, uuid: UUID) -> str:
        return self._auth_api.authorization_url(uuid.hex)
