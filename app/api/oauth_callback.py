from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, Path, Request, status

from ..data import Marketplace
from ..domain.ports import IMarketplaceOAuthService, MarketplaceOAuthServiceError
from ..logger import logger
from .dependencies import (
    OAuth2ClientMapping,
)

PREFIX = "/oauth"

OAUTH_CALLBACK_NAME = "auth_callback"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.get("/auth_callback/{marketplace}", name=OAUTH_CALLBACK_NAME)
async def auth_callback(
    request: Request,
    oauth_mapping: FromDishka[OAuth2ClientMapping],
    service: FromDishka[IMarketplaceOAuthService],
    marketplace: Marketplace = Path(...),
):
    oauth = oauth_mapping[marketplace]

    token: dict = await oauth.authorize_access_token(request)

    state_param = token.pop("state", None)
    if state_param is None:
        logger.warning(f"Invalid state in {marketplace}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        user_uuid = await service.save_tokens(state_param, token, marketplace)
        if user_uuid is None:
            logger.warning(
                f"Authentication in {marketplace} failed: incorrect state",
                exc_info=True,
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.debug(f"User {user_uuid} successfully authenticated in {marketplace}")

    except MarketplaceOAuthServiceError as e:
        logger.exception(
            f"Authentication in {marketplace} failed for user {user_uuid}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication in {marketplace} failed",
        )
    except HTTPException:
        raise
