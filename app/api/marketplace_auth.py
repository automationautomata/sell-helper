from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Path, Query

from ..core.domain.ports import MarketplaceAuthServiceError
from ..logger import logger
from .dependencies import IMarketplaceAuthServicesFactory
from .middlewares import get_user_uuid
from .models.common import Marketplace
from .models.requests import OAuthCodeRequest
from .models.responses import AuthURLResponse, ErrorResponse

PREFIX = "/auth"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.get("/{marketplace}/receive_tokens")
async def receive_tokens(
    factory: FromDishka[IMarketplaceAuthServicesFactory],
    q: OAuthCodeRequest = Query(...),
    marketplace: Marketplace = Path(...),
):
    marketplace_auth = factory.get(marketplace)
    try:
        await marketplace_auth.auth(q.state, q.code)
    except MarketplaceAuthServiceError as e:
        logger.exception(f"Authentication in {marketplace} failed: {e}", exc_info=True)
        return ErrorResponse(message=f"Authentication in {marketplace} failed")


@router.get("/{marketplace}/auth_url", response_model=AuthURLResponse)
async def auth_url(
    factory: FromDishka[IMarketplaceAuthServicesFactory],
    uuid: UUID = Depends(get_user_uuid),
    marketplace: Marketplace = Path(...),
):
    marketplace_auth = factory.get(marketplace)
    auth_url = marketplace_auth.get_auth_url(uuid)
    return AuthURLResponse(auth_url=auth_url)
