from typing import Any, Optional

import requests

from ..utils import auth_retry, request_exception_chain
from .base import EbayApplicationClient, EbayRequestError


class EbayBrowseClientError(EbayRequestError):
    pass


@auth_retry()
class EbayBrowseClient(EbayApplicationClient):
    _api_endpoint = "/buy/browse/v1"

    @request_exception_chain(default=EbayBrowseClientError)
    def search_items(
        self,
        name: str,
        categories_ids: Optional[list[str]] = None,
        fieldgroups: Optional[list[str]] = None,
    ) -> Any:
        params = {"q": name}
        if categories_ids:
            params["category_ids"] = tuple(categories_ids)
        if fieldgroups:
            params["fieldgroups"] = tuple(fieldgroups)

        resp = requests.get(
            url=self.url("/item_summary/search"),
            params=params,
            headers=self._user_auth_header(),
        )
        resp.raise_for_status()
        return resp.json()
