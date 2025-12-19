from typing import Callable, Optional, Type

import requests


def request_exception_chain(
    default: Type[Exception] = RuntimeError,
    *,
    on_request: Optional[Type[Exception]] = None,
    on_connection: Optional[Type[Exception]] = None,
    on_timeout: Optional[Type[Exception]] = None,
    on_http: Optional[Type[Exception]] = None,
) -> Callable:
    exceptions_map = {
        requests.exceptions.RequestException: on_request,
        requests.exceptions.ConnectionError: on_connection,
        requests.exceptions.Timeout: on_timeout,
        requests.exceptions.HTTPError: on_http,
    }
    exceptions = tuple(exceptions_map.keys())

    def wrapped(func: Callable):
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                ex_type = exceptions_map.get(type(e))
                if ex_type is None:
                    ex_type = default

                raise ex_type() from e

        return inner

    return wrapped
