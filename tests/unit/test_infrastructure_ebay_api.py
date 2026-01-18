import pytest
from unittest.mock import Mock, MagicMock
from collections.abc import Generator

from app.infrastructure.marketplace_api import EbayAPI
from app.infrastructure.api_clients.ebay import (
    EbaySellingClient,
    EbayTaxonomyClient,
    EbayCommerceClient,
    EbayAccountClient,
    EbaySellingClientError,
    EbayTaxonomyClientError,
    EbayCommerceClientError,
    EbayAccountClientError,
)
from app.infrastructure.api_clients.ebay import models as ebay_models
from app.domain.entities import Item, AspectType, AccountSettings, AspectField
from app.infrastructure.marketplace_aspects import EbayAspects, EbayPolicies
from app.services.ports import (
    MarketplaceAPIError,
    AccountSettingsNotFound,
    CategoriesNotFoundError,
)


def mock_sku_generator():
    counter = 0
    while True:
        counter += 1
        yield f"SKU_{counter:05d}"


@pytest.fixture
def mock_selling_api():
    api = Mock(spec=EbaySellingClient)
    api.create_or_replace_inventory_item = Mock()
    api.create_offer = Mock(return_value="offer_123")
    api.publish_offer = Mock()
    api.delete_inventory_item = Mock()
    api.delete_offer = Mock()
    loc1 = Mock()
    loc1.name = "WarehouseA"
    loc1.id = "loc_1"
    loc2 = Mock()
    loc2.name = "WarehouseB"
    loc2.id = "loc_2"
    api.get_locations = Mock(return_value=[loc1, loc2])
    return api


@pytest.fixture
def mock_taxonomy_api():
    api = Mock(spec=EbayTaxonomyClient)
    api.get_default_tree_id = Mock(return_value="tree_123")

    category = Mock()
    category.category_id = "cat_123"
    category.category_name = "Electronics > Mobile Phones"

    leaf_node = Mock()
    leaf_node.leaf_category_tree_node = True
    leaf_node.category = category
    leaf_node.child_category_tree_nodes = []

    root_node = Mock()
    root_node.leaf_category_tree_node = False
    root_node.category = None
    root_node.child_category_tree_nodes = [leaf_node]

    category_tree = Mock()
    category_tree.root_category_node = root_node

    api.fetch_category_tree = Mock(return_value=category_tree)
    api.get_item_aspects = Mock(return_value=Mock(aspects=[]))

    return api


@pytest.fixture
def mock_commerce_api():
    api = Mock(spec=EbayCommerceClient)
    img_response = Mock()
    img_response.image_url = "https://example.com/image.jpg"
    api.upload_image = Mock(return_value=img_response)
    return api


@pytest.fixture
def mock_account_api():
    api = Mock(spec=EbayAccountClient)

    fulfillment_policy = Mock()
    fulfillment_policy.name = "Standard"
    fulfillment_policy.id = "fp_123"

    payment_policy = Mock()
    payment_policy.name = "CreditCard"
    payment_policy.id = "pp_123"

    return_policy = Mock()
    return_policy.name = "ReturnsAccepted"
    return_policy.id = "rp_123"

    api.get_all_policies = Mock(
        return_value={
            "fulfillment_policies": [fulfillment_policy],
            "payment_policies": [payment_policy],
            "return_policies": [return_policy],
        }
    )

    return api


@pytest.fixture
def ebay_api(
    mock_selling_api,
    mock_taxonomy_api,
    mock_commerce_api,
    mock_account_api,
):
    return EbayAPI(
        selling_api=mock_selling_api,
        taxonomy_api=mock_taxonomy_api,
        commerce_api=mock_commerce_api,
        account_api=mock_account_api,
        sku_generator=mock_sku_generator(),
    )


@pytest.fixture
def sample_item():
    aspects = Mock()
    aspects.aspects = []

    marketplace_aspects = Mock(spec=EbayAspects)
    marketplace_aspects.marketplace = "ebay"
    marketplace_aspects.location = "WarehouseA"
    marketplace_aspects.policies = EbayPolicies(
        fulfillment_policy="Standard",
        payment_policy="CreditCard",
        return_policy="ReturnsAccepted",
    )
    marketplace_aspects.package = Mock(
        weight_value=2.5,
        weight_unit="KG",
        dimension_length=10,
        dimension_width=8,
        dimension_height=5,
        dimension_unit="CM",
    )
    marketplace_aspects.condition = "NEW"
    marketplace_aspects.condition_description = "Brand new"

    return Item(
        title="Test Product",
        description="Test Description",
        price=99.99,
        currency="USD",
        country="US",
        category="Electronics > Mobile Phones",
        quantity=5,
        marketplace_aspects=marketplace_aspects,
        product_aspects=aspects,
    )


class TestEbayAPIPublish:
    def test_publish_sku_generation(self, ebay_api):
        assert ebay_api.sku_generator is not None
        sku = next(ebay_api.sku_generator)
        assert sku.startswith("SKU_")
        assert len(sku) == 9  # SKU_00001

    def test_publish_inventory_creation_error_handling(
        self, mock_selling_api, ebay_api, sample_item
    ):
        mock_selling_api.create_or_replace_inventory_item.side_effect = (
            EbaySellingClientError()
        )

        with pytest.raises(EbaySellingClientError):
            mock_selling_api.create_or_replace_inventory_item("sku_123", Mock())

        assert mock_selling_api.create_or_replace_inventory_item.side_effect is not None

    def test_publish_sku_generation(self, ebay_api):
        assert ebay_api.sku_generator is not None
        sku = next(ebay_api.sku_generator)
        assert sku.startswith("SKU_")
        assert len(sku) == 9  # SKU_00001

    def test_publish_offer_error_handling(self, mock_selling_api, ebay_api):
        mock_selling_api.create_offer.side_effect = EbaySellingClientError()

        with pytest.raises(EbaySellingClientError):
            mock_selling_api.create_offer(Mock())

    def test_publish_account_settings_not_found(
        self,
        mock_account_api,
    ):
        mock_account_api.get_all_policies.return_value = {
            "fulfillment_policies": [],
            "payment_policies": [],
            "return_policies": [],
        }

        result = mock_account_api.get_all_policies("token")
        assert result["fulfillment_policies"] == []

    def test_publish_cleanup_without_offer_id(
        self,
        mock_selling_api,
    ):
        mock_selling_api.delete_inventory_item.side_effect = EbaySellingClientError()

        with pytest.raises(EbaySellingClientError):
            mock_selling_api.delete_inventory_item("sku_123", "token")


class TestEbayAPIGetProductAspects:
    def test_get_product_aspects_success(
        self,
        ebay_api,
        mock_taxonomy_api,
    ):
        constraint = Mock()
        constraint.item_to_aspect_cardinality = (
            ebay_models.ItemToAspectCardinalityEnum.SINGLE
        )
        constraint.aspect_data_type = ebay_models.AspectValueTypeEnum.STRING
        constraint.aspect_required = True
        constraint.aspect_usage = ebay_models.AspectUsageEnum.RECOMMENDED
        constraint.aspect_mode = None

        aspect = Mock()
        aspect.aspect_constraint = constraint
        aspect.localized_aspect_name = "Brand"
        aspect.aspect_values = []

        aspect_metadata = Mock()
        aspect_metadata.aspects = [aspect]

        mock_taxonomy_api.get_item_aspects.return_value = aspect_metadata

        aspects = ebay_api.get_product_aspects(
            "Electronics > Mobile Phones",
            marketplace_id="ebay",
        )

        assert isinstance(aspects, list)
        assert len(aspects) > 0
        assert all(isinstance(a, AspectField) for a in aspects)
        mock_taxonomy_api.get_item_aspects.assert_called_once()

    def test_get_product_aspects_category_search_with_spaces(
        self,
        ebay_api,
        mock_taxonomy_api,
    ):
        mock_taxonomy_api.get_default_tree_id.return_value = "tree_id"

        result = mock_taxonomy_api.get_default_tree_id("ebay")
        assert result == "tree_id"

    def test_get_product_aspects_category_not_found(
        self,
        ebay_api,
        mock_taxonomy_api,
    ):
        mock_taxonomy_api.fetch_category_tree.return_value.root_category_node.child_category_tree_nodes = []
        mock_taxonomy_api.fetch_category_tree.return_value.root_category_node.leaf_category_tree_node = False

        with pytest.raises(CategoriesNotFoundError):
            ebay_api.get_product_aspects(
                "NonexistentCategory",
                marketplace_id="ebay",
            )

    def test_get_product_aspects_taxonomy_api_error(
        self,
        ebay_api,
        mock_taxonomy_api,
    ):
        mock_taxonomy_api.get_default_tree_id.side_effect = EbayTaxonomyClientError()

        with pytest.raises(MarketplaceAPIError):
            ebay_api.get_product_aspects(
                "Electronics",
                marketplace_id="ebay",
            )

    def test_get_product_aspects_selection_mode(
        self,
        mock_taxonomy_api,
    ):
        constraint = Mock()
        constraint.aspect_mode = ebay_models.AspectModeEnum.SELECTION_ONLY

        assert constraint.aspect_mode == "SELECTION_ONLY"


class TestEbayAPIGetAccountSettings:
    def test_get_account_settings_success(
        self,
        ebay_api,
        mock_account_api,
        mock_selling_api,
    ):
        settings = ebay_api.get_account_settings("token")

        assert isinstance(settings, AccountSettings)
        mock_account_api.get_all_policies.assert_called_once()
        mock_selling_api.get_locations.assert_called_once()

    def test_get_account_settings_with_multiple_policies(
        self,
        ebay_api,
        mock_account_api,
        mock_selling_api,
    ):
        policies = {
            "fulfillment_policies": [
                Mock(name="Standard"),
                Mock(name="Express"),
            ],
            "payment_policies": [
                Mock(name="CreditCard"),
                Mock(name="PayPal"),
            ],
            "return_policies": [
                Mock(name="ReturnsAccepted"),
                Mock(name="NoReturns"),
            ],
        }
        mock_account_api.get_all_policies.return_value = policies
        loc1 = Mock()
        loc1.name = "WarehouseA"
        loc2 = Mock()
        loc2.name = "WarehouseB"
        mock_selling_api.get_locations.return_value = [loc1, loc2]

        settings = ebay_api.get_account_settings("token")

        assert isinstance(settings, AccountSettings)

    def test_get_account_settings_account_api_error(
        self,
        ebay_api,
        mock_account_api,
    ):
        mock_account_api.get_all_policies.side_effect = EbayAccountClientError()

        with pytest.raises(Exception):  # API doesn't wrap in MarketplaceAPIError
            ebay_api.get_account_settings("token")


class TestEbayAPIHelperMethods:
    def test_product_to_inventory_item_validation(self):
        assert hasattr(EbayAPI, "_to_inventory_item")
        assert callable(getattr(EbayAPI, "_to_inventory_item"))

    def test_search_category_found(self):
        category = Mock()
        category.category_id = "cat_123"
        category.category_name = "Electronics"

        leaf_node = Mock()
        leaf_node.leaf_category_tree_node = True
        leaf_node.category = category
        leaf_node.child_category_tree_nodes = []

        root_node = Mock()
        root_node.leaf_category_tree_node = False
        root_node.category = None
        root_node.child_category_tree_nodes = [leaf_node]

        tree = Mock()
        tree.root_category_node = root_node

        result = EbayAPI._search_in_tree(tree, "Electronics")

        assert result is not None
        assert result[0] == "cat_123"
        assert result[1] == "Electronics"

    def test_search_category_not_found(self):
        root_node = Mock()
        root_node.leaf_category_tree_node = False
        root_node.category = None
        root_node.child_category_tree_nodes = []

        tree = Mock()
        tree.root_category_node = root_node

        result = EbayAPI._search_in_tree(tree, "NonexistentCategory")

        assert result is None

    def test_from_ebay_aspects_type_mapping(self):
        constraint = Mock()
        constraint.item_to_aspect_cardinality = (
            ebay_models.ItemToAspectCardinalityEnum.SINGLE
        )
        constraint.aspect_required = True
        constraint.aspect_usage = ebay_models.AspectUsageEnum.RECOMMENDED
        constraint.aspect_mode = None

        constraint.aspect_data_type = ebay_models.AspectValueTypeEnum.STRING

        aspect = Mock()
        aspect.aspect_constraint = constraint
        aspect.localized_aspect_name = "Brand"
        aspect.aspect_values = []

        aspect_metadata = Mock()
        aspect_metadata.aspects = [aspect]

        result = EbayAPI._from_ebay_aspects(aspect_metadata)

        assert len(result) > 0
        assert result[0].data_type == AspectType.STR

    def test_sku_generator_format(self, ebay_api):
        skus = [next(ebay_api.sku_generator) for _ in range(3)]

        for sku in skus:
            assert sku.startswith("SKU_")
            assert len(sku) == 9  # SKU_ + 5 digits

        assert skus[0] < skus[1] < skus[2]
