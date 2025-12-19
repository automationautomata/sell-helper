import os
import tempfile
from typing import List, Union
from uuid import UUID

import aiofiles
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Path,
    Response,
    UploadFile,
    status,
)

from ..core.services.selling import (
    CategoryNotFound,
    ItemData,
    SellingError,
)
from ..logger import logger
from ..utils import utils
from .dependencies import ISellingServicesFactory
from .middlewares import get_user_uuid
from .models.common import Marketplace
from .models.requests import SellItemRequest
from .models.responses import ErrorResponse, PublishItemResponse

PREFIX = "/selling"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post(
    "/{marketplace}/publish", response_model=Union[PublishItemResponse, ErrorResponse]
)
async def publish_item(
    response: Response,
    selling_factory: FromDishka[ISellingServicesFactory],
    user_uuid: UUID = Depends(get_user_uuid),
    item: SellItemRequest = Body(...),
    images: List[UploadFile] = File(...),
    marketplace: Marketplace = Path(...),
):
    seller = selling_factory.get(marketplace)
    with tempfile.TemporaryDirectory(prefix="selling_images_") as tmpdir:
        try:
            images_pathes = []
            for img in images:
                filename = os.path.basename(utils.generate_file_name(img.filename))
                temp_path = os.path.join(tmpdir, filename)
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(img.file.read())

                images_pathes.append(temp_path)

        except Exception as e:
            logger.exception(f"Failed to save files: {e}")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Failed to save files")

        try:
            data = item.model_dump()
            marketplace_aspects_data = data.pop("marketplace_aspects")
            product_data = data.pop("product")
            seller.sell_item(
                user_uuid,
                ItemData(**data),
                marketplace_aspects_data,
                product_data,
                *images_pathes,
            )
        except SellingError as e:
            logger.exception(f"Failed to publish item: {e}")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Failed to publish item")

        except CategoryNotFound:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ErrorResponse(error=f"Invalid category: {item.category}")

        return PublishItemResponse(status="success")
