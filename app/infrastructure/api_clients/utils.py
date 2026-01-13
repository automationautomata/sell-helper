from collections.abc import Callable
from functools import wraps
from typing import Protocol

from requests import codes
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout


def request_exception_chain(
    default: type[Exception] = RuntimeError,
    *,
    on_request: type[Exception] | None = None,
    on_connection: type[Exception] | None = None,
    on_timeout: type[Exception] | None = None,
    on_http: type[Exception] | None = None,
) -> Callable:
    exceptions_map = {
        RequestException: on_request,
        ConnectionError: on_connection,
        Timeout: on_timeout,
        HTTPError: on_http,
    }
    exceptions = tuple(exceptions_map.keys())

    def wrapped(func: Callable):
        @wraps(func)
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


class TokenUpdater(Protocol):
    def update_token(self):
        pass


def auth_retry[T: TokenUpdater](cls: T) -> T:
    def _wrap_method(method: Callable, auth_method: Callable[[], None]):
        @wraps(method)
        def wrapper(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except HTTPError as e:
                if e.response.status_code != codes.unauthorized:
                    raise
                auth_method()
            return method(*args, **kwargs)

        return wrapper

    auth_method = cls.__dict__.get("update_token")
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and attr_name != "update_token":
            setattr(cls, attr_name, _wrap_method(attr_value, auth_method))
    return cls
