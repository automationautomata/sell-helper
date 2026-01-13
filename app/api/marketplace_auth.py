from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import RedirectResponse

from ..data import Marketplace
from ..domain.dto import MarketplaceAccountDTO
from ..domain.ports import (
    IMarketplaceOAuthService,
    MarketplaceOAuthServiceError,
    MarketplaceUnauthorised,
)
from ..logger import logger
from .dependencies import (
    OAuth2ClientMapping,
)
from .middlewares import get_user_uuid
from .models.responses import MarketplaceLogoutResponse
from .oauth_callback import OAUTH_CALLBACK_NAME

PREFIX = "/marketplace"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.get("/login/{marketplace}")
async def login(
    request: Request,
    oauth_mapping: FromDishka[OAuth2ClientMapping],
    service: FromDishka[IMarketplaceOAuthService],
    user_uuid: UUID = Depends(get_user_uuid),
    marketplace: Marketplace = Path(...),
) -> RedirectResponse:
    oauth = oauth_mapping[marketplace]
    redirect_uri = request.url_for(OAUTH_CALLBACK_NAME, marketplace=marketplace)

    try:
        token = await service.generate_token(user_uuid)
        return await oauth.authorize_redirect(redirect_uri, state=token)
    except MarketplaceOAuthServiceError as e:
        logger.exception(
            f"Failed to generate token in {marketplace} marketplace "
            f"for user {user_uuid}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication in {marketplace} failed",
        )


@router.get("/logout/{marketplace}")
async def logout(
    service: FromDishka[IMarketplaceOAuthService],
    user_uuid: UUID = Depends(get_user_uuid),
    marketplace: Marketplace = Path(...),
) -> MarketplaceLogoutResponse:
    try:
        await service.logout(MarketplaceAccountDTO(user_uuid, marketplace))
        return MarketplaceLogoutResponse(status="success")

    except MarketplaceUnauthorised:
        return MarketplaceLogoutResponse(status="user already logged out")

    except MarketplaceOAuthServiceError as e:
        logger.exception(
            f"Failed to generate token in {marketplace} marketplace "
            f"for user {user_uuid}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication in {marketplace} failed",
        )
