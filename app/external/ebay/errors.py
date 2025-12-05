from typing import Optional

import requests


class EbayRequestError(Exception):
    @property
    def response_content(self) -> Optional[str]:
        cause = self.__cause__
        if isinstance(cause, requests.HTTPError):
            return cause.response.text

    def __str__(self) -> str:
        repr = super().__str__()
        response_content = self.response_content
        if response_content:
            return f"{repr}, response_content: {response_content}"

        return repr
