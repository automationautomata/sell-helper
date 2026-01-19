from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, status

from ..domain.ports import (
    AuthError,
    IAuthService,
    InvalidUserToken,
    IRegistrationService,
    RegistrationError,
    UserAlreadyExists,
)
from ..logger import logger
from .models.requests import UserLogin, UserRegistration
from .models.responses import TokenResponse

PREFIX = "/auth"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post("/login")
async def login(
    user: UserLogin, auth_service: FromDishka[IAuthService]
) -> TokenResponse:
    try:
        token = await auth_service.verify_user(user.email, user.password)

        return TokenResponse(token=token.token, ttl=token.ttl_seconds)

    except InvalidUserToken:
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


@router.post("/registration")
async def registration(
    user: UserRegistration, reg_service: FromDishka[IRegistrationService]
) -> TokenResponse:
    try:
        token = await reg_service.add_user(user.email, user.password)

        return TokenResponse(token=token.token, ttl=token.ttl_seconds)

    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    except RegistrationError as e:
        logger.exception(f"Cannot create user: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )
