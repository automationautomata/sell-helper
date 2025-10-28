import os
import tempfile
from typing import Union

import aiofiles
from api.dependencies import SerachServicesFactory
from api.models.common import Marketplace
from core.services.search import SearchError
from dishka.integrations.fastapi import DishkaRoute, FromDishka  # noqa: F811
from fastapi import APIRouter, File, Path, Response, UploadFile, status
from logger import logger
from utils import utils

from .models.requests import ProductRequest
from .models.responses import ErrorResponse, ProductCategoriesResponse, ProductResponse

router = APIRouter(route_class=DishkaRoute)


@router.post(
    "/{marketplace}/product", response_model=Union[ProductResponse, ErrorResponse]
)
async def search_by_product_name(
    product: ProductRequest,
    response: Response,
    search_factory: FromDishka[SerachServicesFactory],
    marketplace: str = Path(...),
):
    searcher = search_factory(marketplace)
    try:
        answer = searcher.product(
            product.product_name, product.category, product.comment
        )
    except SearchError as e:
        logger.exception(f"Cannot process product: {e}", exc_info=True)

        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ErrorResponse(error="Failed to find information about product")

    return ProductResponse.from_domain(answer)


@router.post(
    "/{marketplace}/categories",
    response_model=Union[ProductCategoriesResponse, ErrorResponse],
)
async def search_product_categories(
    response: Response,
    search_factory: FromDishka[SerachServicesFactory],
    image: UploadFile = File(...),
    marketplace: Marketplace = Path(...),
):
    searcher = search_factory(marketplace)
    with tempfile.TemporaryDirectory(prefix="search_by_image_") as temp_dir:
        try:
            temp_path = os.path.join(
                temp_dir, os.path.basename(utils.generate_file_name(image.filename))
            )
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(image.file.read())

        except Exception as e:
            logger.exception(f"Failed to save files: {e}", exc_info=True)

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Failed to process image")

        try:
            categories = searcher.product_categories(temp_path)
        except SearchError as e:
            logger.exception(f"Cannot process product: {e}", exc_info=True)

            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(error="Failed to find product categories")

    return ProductCategoriesResponse(
        product_name=categories.product_name, categories=categories.categories
    )
