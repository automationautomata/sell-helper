from core.services.auth import AuthServiceABC
from dishka import FromDishka
from fastapi import Request, Response, status
from logger import logger

from .models.responses import ErrorResponse


class verification:
    def __init__(self, *endoints: str):
        self._endpoints = set(endoints)

    async def __call__(
        self,
        request: Request,
        response: Response,
        auth_service: FromDishka[AuthServiceABC],
        call_next,
    ):
        path = request.url.path
        if not any(map(path.startswith, self._endpoints)):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return ErrorResponse(error="Authorization header missing or invalid")

        try:
            user = auth_service.validate(request)
        except Exception as e:
            logger.exception(f"Validation failed: {e}", exc_info=True)

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Validation failed")

        if user is None:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return ErrorResponse(error="Authorization header missing or invalid")

        return await call_next(request)
