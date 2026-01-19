from typing import Optional

import requests

from ..utils import request_exception_chain
from .base_client import EbayClientBase
from .errors import EbayRequestError
from .models import EbaySearchResponse


class EbayBrowseClientError(EbayRequestError):
    pass


class EbayBrowseClient(EbayClientBase):
    API_ENDPOINT = "/buy/browse/v1"

    @request_exception_chain(default=EbayBrowseClientError)
    def search_items(
        self,
        name: str,
        categories_ids: Optional[list[str]] = None,
        fieldgroups: Optional[list[str]] = None,
    ) -> EbaySearchResponse:
        url = f"{self.url_base}/item_summary/search"

        params = {"q": name}
        if categories_ids:
            params.update({"category_ids": tuple(categories_ids)})
        if fieldgroups:
            params.update({"fieldgroups": tuple(fieldgroups)})

        resp = requests.get(url, params=params, headers=self._auth_header())
        resp.raise_for_status()
        return EbaySearchResponse.model_validate(resp.json())
