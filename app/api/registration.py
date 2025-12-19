import uuid

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.domain.ports import AuthError, IAuthService
from ..core.services.ports import UserAlreadyExistsError
from ..logger import logger
from .middlewares import get_user_uuid
from .models.requests import UseRegistrationRequest
from .models.responses import TokenResponse

PREFIX = "/registration"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post("/registration", response_model=TokenResponse)
async def registration(
    user: UseRegistrationRequest,
    auth_service: FromDishka[IAuthService],
    user_uuid: uuid.UUID = Depends(get_user_uuid),
):
    try:
        token = await auth_service.add_user(user.email, user.password)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    except AuthError as e:
        logger.exception(f"Cannot create user: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )

    return TokenResponse(token=token.token, ttl=token.ttl_seconds)
