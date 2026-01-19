from typing import Self
import pytest
from dataclasses import asdict, dataclass
from pydantic import TypeAdapter

from app.infrastructure.adapter import (
    ProductAdapter,
    ProductAdapterError,
    InvalidMetadataError,
    InvalidAspectsError,
)
from app.domain.entities import (
    AspectField,
    AspectType,
    Product,
    ProductStructure,
)


@dataclass
class MockMetadata:
    title: str
    description: str
    price: float

    @classmethod
    def validate(cls, data: dict[str]) -> Self | None:
        return TypeAdapter(cls).validate_python(data)

    def asdict(self) -> dict[str]:
        return asdict(self)


@pytest.fixture
def product_structure():
    return ProductStructure(
        fields=[
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
            AspectField(name="color", data_type=AspectType.STR, is_required=False),
            AspectField(name="quantity", data_type=AspectType.INT, is_required=False),
        ]
    )


@pytest.fixture
def valid_raw_data():
    return {
        "aspects": {
            "brand": "Apple",
            "color": "Black",
            "quantity": 5,
        },
        "metadata": {
            "title": "iPhone 13",
            "description": "Latest smartphone",
            "price": 999.99,
        },
    }


class TestProductAdapterToProduct:
    def test_to_product_success(self, product_structure, valid_raw_data):
        adapter = ProductAdapter(metadata_type=MockMetadata)

        product = adapter.to_product(valid_raw_data, product_structure)

        assert isinstance(product, Product)
        assert product.metadata.title == "iPhone 13"
        assert product.metadata.price == 999.99
        assert len(product.aspects) == 3

    def test_to_product_with_missing_optional_aspects(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {
            "aspects": {
                "brand": "Samsung",
            },
            "metadata": {
                "title": "Galaxy S21",
                "description": "Samsung smartphone",
                "price": 799.99,
            },
        }

        product = adapter.to_product(raw_data, product_structure)

        assert product.metadata.title == "Galaxy S21"
        assert len([a for a in product.aspects if a.name == "brand"]) == 1

    def test_to_product_with_empty_aspects(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {
            "aspects": {},
            "metadata": {
                "title": "Test Product",
                "description": "Test",
                "price": 100.0,
            },
        }
        with pytest.raises(InvalidAspectsError):
            adapter.to_product(raw_data, product_structure)

    def test_to_product_invalid_metadata_raises_error(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {
            "aspects": {"brand": "Apple"},
            "metadata": {
                "title": "iPhone",
            },
        }

        with pytest.raises(InvalidMetadataError):
            adapter.to_product(raw_data, product_structure)

    def test_to_product_invalid_metadata_type_raises_error(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {
            "aspects": {"brand": "Apple"},
            "metadata": {
                "title": 123,
                "description": "Test",
                "price": "not a number",
            },
        }

        with pytest.raises(InvalidMetadataError):
            adapter.to_product(raw_data, product_structure)

    def test_to_product_missing_aspects_section(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        product_structure = ProductStructure(fields=[])
        raw_data = {
            "metadata": {
                "title": "Test",
                "description": "Test",
                "price": 50.0,
            }
        }

        product = adapter.to_product(raw_data, product_structure)

        assert isinstance(product, Product)
        assert product.metadata.title == "Test"

    def test_to_product_missing_metadata_section(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {"aspects": {"brand": "Sony"}}

        with pytest.raises(InvalidMetadataError):
            adapter.to_product(raw_data, product_structure)


class TestProductAdapterToSchema:
    def test_to_schema_with_aspects(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        aspects = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
            AspectField(name="size", data_type=AspectType.INT, is_required=False),
        ]

        schema = adapter.to_schema(aspects)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "aspects" in schema["properties"]
        assert "metadata" in schema["properties"]
        assert "$defs" in schema

    def test_to_schema_without_aspects(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)

        schema = adapter.to_schema([])

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_to_schema_allows_additional_aspects(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        aspects = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
        ]

        schema = adapter.to_schema(aspects, allow_additional_aspects=True)

        assert "properties" in schema
        assert "$defs" in schema

    def test_to_schema_structure(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        aspects = [
            AspectField(name="test", data_type=AspectType.STR, is_required=True),
        ]

        schema = adapter.to_schema(aspects)

        assert schema["required"] is not None
        assert "additionalProperties" in schema


class TestProductAdapterAspectsSchema:
    def test_build_aspects_schema_with_different_types(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        aspects = [
            AspectField(name="name", data_type=AspectType.STR, is_required=True),
            AspectField(name="count", data_type=AspectType.INT, is_required=False),
            AspectField(name="price", data_type=AspectType.FLOAT, is_required=False),
        ]

        schema = adapter._build_aspects_schema(
            aspects, allow_additional_properties=False
        )

        assert schema["type"] == "object"
        assert "properties" in schema

    def test_build_aspects_schema_required_fields(self):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        aspects = [
            AspectField(
                name="required_field", data_type=AspectType.STR, is_required=True
            ),
            AspectField(
                name="optional_field", data_type=AspectType.STR, is_required=False
            ),
        ]

        schema = adapter._build_aspects_schema(
            aspects, allow_additional_properties=False
        )

        if "required" in schema:
            assert "required_field" in schema["required"]


class TestProductAdapterErrors:
    def test_invalid_aspects_error_from_aspects_validation(self, product_structure):
        adapter = ProductAdapter(metadata_type=MockMetadata)
        raw_data = {
            "aspects": {},
            "metadata": {
                "title": "Test",
                "description": "Test",
                "price": 100.0,
            },
        }

        with pytest.raises(InvalidAspectsError):
            adapter.to_product(raw_data, product_structure)

    def test_product_adapter_error_is_base_exception(self):
        assert issubclass(ProductAdapterError, Exception)

    def test_invalid_metadata_error_inheritance(self):
        assert issubclass(InvalidMetadataError, ProductAdapterError)

    def test_invalid_aspects_error_inheritance(self):
        assert issubclass(InvalidAspectsError, ProductAdapterError)
