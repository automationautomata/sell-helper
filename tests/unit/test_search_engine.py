import json

import pytest
from app.core.infrastructure.search import (
    CategoriesNotFoundError,
    PerplexityAndEbaySearch,
    SearchEngineError,
)
from app.external import barcode_search
from app.external.ebay.taxonomy import (
    EbayCategoriesNotFoundError,
    EbayTaxonomyClientError,
)
from pydantic import BaseModel


@pytest.fixture
def fake_perplexity_client(mocker):
    client = mocker.MagicMock()
    client.chat.completions.create = mocker.MagicMock()
    return client


@pytest.fixture
def fake_taxonomy_client(mocker):
    return mocker.MagicMock()


@pytest.fixture
def ebay_config():
    class EbayConfig:
        marketplace_id = "EBAY_US"

    return EbayConfig()


@pytest.fixture
def perplexity_config():
    class PerplexityConfig:
        model = "pplx-test-model"

    return PerplexityConfig()


class MockTestModel(BaseModel):
    """Mock model for testing search responses."""
    name: str


@pytest.fixture
def service(
    fake_perplexity_client, ebay_config, fake_taxonomy_client, perplexity_config
):
    return PerplexityAndEbaySearch(
        perplexity_config=perplexity_config,
        perplexity_client=fake_perplexity_client,
        ebay_config=ebay_config,
        taxonomy_client=fake_taxonomy_client,
    )


def test_by_product_name_success(service, fake_perplexity_client):
    """Test successful product name search returns parsed JSON dict."""
    test_json = MockTestModel(name="abc").model_dump_json()
    
    fake_perplexity_client.chat.completions.create.return_value.choices = [
        type(
            "Choice",
            (),
            {
                "message": type(
                    "Msg", (), {"content": test_json}
                )
            },
        )
    ]

    result = service.by_product_name("TV", "great one", MockTestModel.model_json_schema())
    # by_product_name returns a dict (parsed JSON), not a Pydantic model
    assert result == {"name": "abc"}
    fake_perplexity_client.chat.completions.create.assert_called_once()


def test_by_product_name_perplexity_error(service, fake_perplexity_client, mocker):
    from perplexity import PerplexityError

    fake_perplexity_client.chat.completions.create.side_effect = PerplexityError("fail")

    with pytest.raises(SearchEngineError):
        service.by_product_name("iPhone", "", {"type": "object"})


def test_by_product_name_empty_response(service, fake_perplexity_client):
    fake_perplexity_client.chat.completions.create.return_value.choices = []
    with pytest.raises(SearchEngineError):
        service.by_product_name("iPhone", "", {"type": "object"})


def test_by_barcode_success(service, mocker):
    mock_search = mocker.patch(
        "app.core.infrastructure.search.barcode_search.search",
        return_value="Product",
    )
    assert service.by_barecode("1234") == "Product"
    mock_search.assert_called_once_with("1234")


def test_by_barcode_error(service, mocker):
    mock_search = mocker.patch("app.core.infrastructure.search.barcode_search.search")
    mock_search.side_effect = barcode_search.BarcodeSearchError("Not found")

    with pytest.raises(SearchEngineError):
        service.by_barecode("0000")


def test_barcodes_on_image(service, mocker):
    mock_extract = mocker.patch(
        "app.core.infrastructure.search.recognition.extract_barcodes",
        return_value=["111"],
    )
    result = service.barecodes_on_image("path/to/image.jpg")
    assert result == ["111"]
    mock_extract.assert_called_once_with("path/to/image.jpg")


def test_categories_success(service, fake_taxonomy_client, ebay_config, mocker):
    fake_taxonomy_client.get_default_tree_id.return_value = "1"
    fake_taxonomy_client.get_category_suggestions.return_value.category_suggestions = [
        mocker.Mock(category=mocker.Mock(category_name="Phones")),
        mocker.Mock(category=mocker.Mock(category_name="Electronics")),
    ]

    result = service.categories("iPhone")
    assert result == ["Phones", "Electronics"]

    fake_taxonomy_client.get_default_tree_id.assert_called_once_with(
        ebay_config.marketplace_id
    )
    fake_taxonomy_client.get_category_suggestions.assert_called_once()


def test_categories_not_found(service, fake_taxonomy_client):
    fake_taxonomy_client.get_default_tree_id.return_value = "1"
    fake_taxonomy_client.get_category_suggestions.side_effect = (
        EbayCategoriesNotFoundError("none")
    )

    with pytest.raises(CategoriesNotFoundError):
        service.categories("Unknown")


def test_categories_client_error(service, fake_taxonomy_client):
    fake_taxonomy_client.get_default_tree_id.return_value = "1"
    fake_taxonomy_client.get_category_suggestions.side_effect = EbayTaxonomyClientError(
        "api fail"
    )

    with pytest.raises(SearchEngineError):
        service.categories("Something")


def test_product_search_text_with_comment():
    text = PerplexityAndEbaySearch._product_search_text("iPhone", "great one")
    assert "iPhone" in text
    assert "Comment" in text


def test_product_search_text_without_comment():
    text = PerplexityAndEbaySearch._product_search_text("iPhone", "")
    assert "Comment" not in text


def test_convert_creates_expected_messages():
    messages = PerplexityAndEbaySearch._convert("Find details")
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert isinstance(messages[1]["content"], list)
