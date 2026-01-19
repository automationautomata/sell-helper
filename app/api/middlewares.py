import uuid
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status

from ..domain.ports import AuthError, IAuthService, InvalidUserToken
from ..logger import logger


def get_user_uuid(request: Request) -> uuid.UUID:
    return request.state.user_uuid


class authentication:
    def __init__(self, *prefixes: str):
        self._prefixes = set(prefixes)

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        container = request.state.dishka_container
        auth_service: IAuthService = await container.get(IAuthService)

        path = request.url.path
        if not any(path.startswith(p) for p in self._prefixes):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                detail="Authorization header missing or invalid",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = await auth_service.validate(auth_header.removeprefix("Bearer "))
            request.state.user_uuid = user.uuid

            return await call_next(request)

        except AuthError as e:
            logger.exception(f"Validation failed: {e}", exc_info=True)

            raise HTTPException(
                detail="Validation failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except InvalidUserToken:
            raise HTTPException(
                detail="Authorization token missing or invalid",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
