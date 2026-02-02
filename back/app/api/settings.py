import uuid

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, HTTPException, Path, status

from ..data import Marketplace
from ..domain.dto import MarketplaceAccountDTO
from ..domain.ports import (
    IMarketplaceAccountService,
    MarketplaceAccountServiceError,
    MarketplaceAuthorizationFailed,
    MarketplaceUnauthorised,
)
from ..logger import logger
from .middlewares import get_user_uuid
from .models.responses import MarketplaceAccountSettingsResponse

PREFIX = "/settings"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.get("/{marketplace}")
async def get_marketplace_account_settings(
    service: FromDishka[IMarketplaceAccountService],
    marketplace: Marketplace = Path(),
    user_uuid: uuid.UUID = Depends(get_user_uuid),
):
    try:
        settings = await service.find_settings(
            MarketplaceAccountDTO(user_uuid, marketplace)
        )
        return MarketplaceAccountSettingsResponse(settings=settings)

    except MarketplaceAuthorizationFailed as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if not isinstance(e, MarketplaceUnauthorised):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            logger.exception(f"User authorization failed: {e}", exc_info=True)

        raise HTTPException(
            status_code=status_code,
            detail="User unauthorised in marketplace",
        )
    except MarketplaceAccountServiceError as e:
        logger.exception(f"Failed to get settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get settings",
        )
