import os
import tempfile
from typing import Union

import aiofiles
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, File, Path, Response, UploadFile, status

from ..core.services.price_statistics.price_statistics import (
    ItemInfo,
    StatisticsServiceError,
)
from ..core.services.search import SearchError
from ..logger import logger
from ..utils import utils
from .dependencies import IPriceStatisticsServicesFactory, ISearchServicesFactory
from .models.common import Marketplace
from .models.requests import ProductRequest, StatisticsRequest
from .models.responses import (
    ErrorResponse,
    ProductCategoriesResponse,
    ProductResponse,
    StatisticsResponse,
)

PREFIX = "/search"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


@router.post(
    "/{marketplace}/product", response_model=Union[ProductResponse, ErrorResponse]
)
async def search_by_product_name(
    product: ProductRequest,
    response: Response,
    search_factory: FromDishka[ISearchServicesFactory],
    marketplace: Marketplace = Path(...),
):
    searcher = search_factory.get(marketplace)
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
    search_factory: FromDishka[ISearchServicesFactory],
    image: UploadFile = File(...),
    marketplace: Marketplace = Path(...),
):
    searcher = search_factory.get(marketplace)
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


@router.post(
    "/{marketplace}/price_statistics",
    response_model=Union[StatisticsResponse, ErrorResponse],
)
async def price_statistics(
    response: Response,
    request: StatisticsRequest,
    statistics_factory: FromDishka[IPriceStatisticsServicesFactory],
    marketplace: Marketplace = Path(...),
):
    statistics_service = statistics_factory.get(marketplace)

    try:
        info = ItemInfo(
            name=request.name,
            category_name=request.category,
            currency=request.currency,
        )
        stat = statistics_service.calc_statistics(info, **(request.filters or {}))
    except StatisticsServiceError as e:
        logger.exception(f"Cannot calculate statistics: {e}", exc_info=True)

        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ErrorResponse(error="Failed to find product categories")

    return StatisticsResponse(
        min_price=stat.min_price,
        max_price=stat.max_price,
        mean_price=stat.mean_price,
        mode_price=stat.mode_price,
        median_price=stat.median_price,
    )
