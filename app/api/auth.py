from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from ..core.domain.ports import IAuthService
from ..logger import logger
from .models.requests import UserSingInRequest
from .models.responses import TokenResponse

PREFIX = "/auth"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post("/login", response_model=TokenResponse)
async def login(user: UserSingInRequest, auth_service: FromDishka[IAuthService]):
    try:
        check = await auth_service.verify_user(user.email, user.password)
    except Exception as e:
        logger.exception(f"User authentication failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed",
        )

    if not check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password"
        )

    token = auth_service.create_access_token(user.email)
    return TokenResponse(
        token=token.token,
        ttl=token.ttl_seconds,
    )
