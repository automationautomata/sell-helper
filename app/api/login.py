from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from ..core.domain.ports import AuthError, IAuthService, UserAuthFailedError
from ..logger import logger
from .models.requests import UserLoginRequest
from .models.responses import TokenResponse

PREFIX = "/auth"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLoginRequest, auth_service: FromDishka[IAuthService]):
    try:
        token = await auth_service.verify_user(user.email, user.password)
    except UserAuthFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    except AuthError as e:
        logger.exception(f"User authentication failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed",
        )

    return TokenResponse(token=token.token, ttl=token.ttl_seconds)
