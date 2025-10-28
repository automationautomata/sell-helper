from typing import Union

from core.services.auth import AuthServiceABC
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response, status
from logger import logger

from .models.requests import UserSingInRequest
from .models.responses import ErrorResponse, TokenResponse

router = APIRouter(route_class=DishkaRoute)


@router.post("/login", response_model=Union[TokenResponse, ErrorResponse])
def login(
    user: UserSingInRequest,
    response: Response,
    auth_service: FromDishka[AuthServiceABC],
):
    try:
        check = auth_service.verify_user(user.email, user.password)
    except Exception as e:
        logger.exception(f"User verification failed: {e}", exc_info=True)

        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ErrorResponse(error="Validation failed")

    if not check:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(error="Invalid email or password")

    token = auth_service.create_access_token(user.email)
    return TokenResponse(
        token=token.token,
        expires_at=token.ttl_seconds,
    )
