from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Self

from fastapi import APIRouter, FastAPI, HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import Secrets

from . import auth, marketplace_auth, product, settings
from .errors_handler import http_handler
from .middlewares import authentication

type Lifespan = Callable[[FastAPI], AsyncGenerator[Any, None]]


class AppBuilder:
    def __init__(self, root_path: str = "", lifespan: Lifespan | None = None):
        if lifespan is not None:
            lifespan = asynccontextmanager(lifespan)
        self._app = FastAPI(root_path=root_path, lifespan=lifespan)

    def root_router(self) -> Self:
        root_router = APIRouter()
        routers = [
            auth.router,
            product.router,
            marketplace_auth.router,
            settings.router,
        ]
        for router in routers:
            root_router.include_router(router)

        self._app.include_router(root_router)
        return self

    def middlewares(self, secrets: Secrets) -> Self:
        root = self._app.root_path
        auth_prefixes = [product.PREFIX, marketplace_auth.PREFIX, settings.PREFIX]
        self._app.middleware("http")(
            authentication(*[f"{root}{p}" for p in auth_prefixes])
        )
        self._app.add_middleware(SessionMiddleware, secret_key=secrets.session)
        return self

    def http_handlers(self) -> Self:
        self._app.exception_handler(HTTPException)(http_handler)
        return self

    def app(self) -> FastAPI:
        return self._app
