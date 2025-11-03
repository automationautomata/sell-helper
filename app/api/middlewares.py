from fastapi import Request, status
from fastapi.responses import JSONResponse

from ..core.services.auth import AuthServiceABC
from ..logger import logger
from .models.responses import ErrorResponse


class authentication:
    def __init__(self, *prefixes: str):
        self._prefixes = set(prefixes)

    async def __call__(self, request: Request, call_next):
        container = request.state.dishka_container
        auth_service: AuthServiceABC = await container.get(AuthServiceABC)

        path = request.url.path
        if not any(map(path.startswith, self._prefixes)):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                content=ErrorResponse(error="Authorization header missing or invalid"),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = await auth_service.validate(auth_header.removeprefix("Bearer "))
        except Exception as e:
            logger.exception(f"Validation failed: {e}", exc_info=True)

            return JSONResponse(
                content=ErrorResponse(error="Validation failed"),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if user is None:
            return JSONResponse(
                content=ErrorResponse("Authorization header missing or invalid"),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return await call_next(request)
