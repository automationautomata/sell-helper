import os
import tempfile
from uuid import UUID

import aiofiles
from app.domain.ports.errors import InvalidMarketplaceAspects, InvalidProductAspects
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    UploadFile,
    status,
)

from ..data import Marketplace
from ..domain.dto import ItemDTO, MarketplaceAccountDTO
from ..domain.ports import (
    InvalidCategory,
    InvalidItemStructure,
    ISearchService,
    ISellingService,
    MarketplaceAuthorizationFailed,
    SearchServiceError,
    SellingServiceError,
)
from ..logger import logger
from ..utils import utils
from .middlewares import get_user_uuid
from .models.requests import (
    EbayOptions,
    PublishItem,
    SearchOptions,
    SearchProductAspects,
)
from .models.responses import (
    Aspects,
    EbayMetadata,
    Metadata,
    MetadataUnion,
    PublishItemResponse,
    SearchAspectsResponse,
    SearchCategoriesResponse,
)

PREFIX = "/product"

router = APIRouter(route_class=DishkaRoute, prefix=PREFIX)


def _check_options(options: SearchOptions, marketplace: Marketplace):
    opt_class = None
    if marketplace == Marketplace.EBAY:
        opt_class = EbayOptions

    return opt_class is not None and isinstance(options.options, opt_class)


@router.post("/{marketplace}/recognize")
async def search_product_categories(
    options: SearchOptions,
    searcher: FromDishka[ISearchService],
    image: UploadFile = File(...),
    marketplace: Marketplace = Path(...),
) -> SearchCategoriesResponse:
    if not _check_options(options, marketplace):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Options doesn't match with markeplace",
        )

    with tempfile.TemporaryDirectory(prefix="search_by_image_") as temp_dir:
        temp_path = os.path.join(
            temp_dir, os.path.basename(utils.generate_file_name(image.filename))
        )
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(image.file.read())

        try:
            categories = searcher.recognize_product(
                temp_path, marketplace, **options.model_dump()
            )

            return SearchCategoriesResponse(
                product_name=categories.product_name,
                categories=categories.categories,
            )

        except SearchServiceError as e:
            logger.exception(f"Cannot process product: {e}", exc_info=True)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to find product categories",
            )


def _metadata_to_responese(
    metadata: dict[str], marketplace: Marketplace
) -> MetadataUnion:
    if marketplace == Marketplace.EBAY:
        return EbayMetadata.model_validate(metadata)
    return Metadata()


@router.post("/{marketplace}/aspects")
async def search_by_product_name(
    product_aspects: SearchProductAspects,
    searcher: FromDishka[ISearchService],
    marketplace: Marketplace = Path(...),
) -> SearchAspectsResponse:
    if not _check_options(product_aspects.options, marketplace):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Options doesn't match with markeplace",
        )

    try:
        product = searcher.aspects(
            product_aspects.product_name,
            product_aspects.category,
            product_aspects.comment,
            marketplace,
            **product_aspects.options.model_dump(),
        )

        aspects_resp = Aspects(values={}, required=[])
        for aspect in product.aspects:
            aspects_resp.values[aspect.name] = aspect.value
            if aspect.is_required:
                aspects_resp.required.append(aspect.name)

        return SearchAspectsResponse(
            aspects=aspects_resp,
            metadata=_metadata_to_responese(product.metadata, marketplace),
        )

    except SearchServiceError as e:
        logger.exception(f"Cannot process product: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find information about product",
        )


@router.post("/{marketplace}/publish")
async def publish_item(
    seller: FromDishka[ISellingService],
    user_uuid: UUID = Depends(get_user_uuid),
    item: PublishItem = Body(...),
    images: list[UploadFile] = File(...),
    marketplace: Marketplace = Path(...),
) -> PublishItemResponse:
    with tempfile.TemporaryDirectory(prefix="selling_images_") as tmpdir:
        pathes = []
        for img in images:
            filename = os.path.basename(utils.generate_file_name(img.filename))
            temp_path = os.path.join(tmpdir, filename)
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(img.file.read())

            pathes.append(temp_path)

        try:
            item_data = item.model_dump()
            await seller.publish(
                MarketplaceAccountDTO(user_uuid=user_uuid, marketplace=marketplace),
                ItemDTO(**item_data),
                *pathes,
            )

            return PublishItemResponse(status="success")

        except (
            InvalidCategory,
            InvalidItemStructure,
            MarketplaceAuthorizationFailed,
        ) as e:
            if isinstance(e, MarketplaceAuthorizationFailed):
                logger.debug(f"User unauthorised in {marketplace}: {e}", exc_info=True)

            detail_mapping = {
                InvalidCategory: f"Invalid category: {item.category}",
                MarketplaceAuthorizationFailed: f"User unauthorised in {marketplace}",
                InvalidProductAspects: "Invalid product aspects",
                InvalidMarketplaceAspects: "Invalid marketplace aspects",
            }

            detail = detail_mapping[type(e)]
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        except SellingServiceError as e:
            logger.exception(f"Failed to publish item: {e}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish item",
            )
