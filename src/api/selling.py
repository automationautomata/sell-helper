import os
import tempfile
from typing import List, Union

import aiofiles
from api.dependencies import SellingServicesFactory
from api.models.common import Marketplace
from core.services.selling import (
    CategoryNotFound,
    ItemData,
    SellingError,
)
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute, FromDishka  # noqa: F811
from fastapi import (
    APIRouter,
    Body,
    File,
    Path,
    Response,
    UploadFile,
    status,
)
from logger import logger
from utils import utils

from .models.requests import SellItemRequest
from .models.responses import ErrorResponse, ItemResponse

router = APIRouter(route_class=DishkaRoute)


@router.post("/{marketplace}/sell", response_model=Union[ItemResponse, ErrorResponse])
async def sell_item(
    response: Response,
    selling_factory: FromDishka[SellingServicesFactory],
    item: SellItemRequest = Body(...),
    images: List[UploadFile] = File(...),
    marketplace: Marketplace = Path(...),
):
    seller = selling_factory(marketplace)
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
            published_item = seller.sell_item(
                ItemData(**data), marketplace_aspects_data, product_data, *images_pathes
            )
        except SellingError as e:
            logger.exception(f"Failed to publish item: {e}")

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Failed to publish item")

        except CategoryNotFound:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ErrorResponse(error=f"Invalid category: {item.category}")

        return ItemResponse.from_domain(published_item)
