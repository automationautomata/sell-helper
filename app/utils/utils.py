import base64
import os
import uuid
from datetime import datetime, timedelta
from typing import Callable, Optional, Type

import requests
from apscheduler.schedulers.base import BaseScheduler

from ..config import EbayConfig
from ..data import EnvKeys
from ..external.ebay.auth import EbayAuthClient, EbayAuthError
from ..logger import logger


def token_update_job(
    scheduler: BaseScheduler, config: EbayConfig, job_name: str = "ebay token updating"
):
    auth_api = EbayAuthClient(config)

    async def wrapped_updater():
        try:
            resp = await auth_api.get_token()
        except EbayAuthError as e:
            logger.critical(f"Ebay token update failed: {e}")
            return

        os.environ[EnvKeys.EBAY_USER_TOKEN] = resp.access_token

        run_date = datetime.now() + timedelta(seconds=float(resp.expires_in))
        scheduler.add_job(wrapped_updater, "date", run_date=run_date, name=job_name)

    return wrapped_updater


def image_to_base64(img_path: str) -> str:
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_file_name(filepath: str) -> str:
    path = os.path.dirname(filepath)
    _, ext = os.path.splitext(filepath)
    name = uuid.uuid4().hex
    return os.path.join(path, f"{name}{ext}")


def request_exception_chain(
    *,
    default: Optional[Type[Exception]] = RuntimeError,
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
                res = func(*args, **kwargs)
            except exceptions as e:
                ex_type = exceptions_map.get(type[e], default)
                raise ex_type() from e
            else:
                return res

        return inner

    return wrapped
