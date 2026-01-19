from typing import Optional

import requests


class EbayRequestError(Exception):
    @property
    def response_content(self) -> Optional[str]:
        cause = self.__cause__
        if isinstance(cause, requests.HTTPError):
            return cause.response.text
