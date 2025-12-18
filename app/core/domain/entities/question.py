from dataclasses import dataclass
from typing import Any, Final, Generic, List, Type, TypeVar, final

from .errors import InvalidProductData
from .value_objects import (
    AspectData,
    AspectField,
)


@dataclass
class ProductData:
    aspects: list[AspectData]


@dataclass
class ProductStructure:
    """Collection of aspects that define a product's structure."""

    fields: List[AspectField]

    def validate(self, raw_data: dict[str, Any]) -> ProductData:
        names = {f.name: f for f in self.fields}
        required = {f.name for f in self.fields if f.is_required}

        aspects: list[AspectData] = []

        for name, value in raw_data.items():
            field = names.get(name)
            if field is None:
                raise InvalidProductData(f"Unexpected aspect '{name}' in product data.")

            if not field.is_value_valid(value):
                expected_type_name = field.data_type.py_type().__name__
                raise InvalidProductData(
                    f"Aspect '{name}' has incorrect or disallowed value. "
                    f"Expected type {expected_type_name}, got {type(value).__name__}."
                )

            aspects.append(
                AspectData(name=name, value=value, is_required=field.is_required)
            )
            required.discard(name)

        if required:
            missing = ", ".join(sorted(required))
            raise InvalidProductData(f"Missing required aspects: {missing}")

        return ProductData(aspects=aspects)


@dataclass
class Metadata:
    description: str


TMetadata = TypeVar("TMetadata", bound=Metadata)


@final
@dataclass
class Answer(Generic[TMetadata]):
    metadata: TMetadata
    product_data: ProductData


@final
@dataclass
class Question(Generic[TMetadata]):
    product_structure: ProductStructure
    metadata_type: Final[Type[TMetadata]]

    def get_answer(
        self, metadata: TMetadata, product_data: dict[str, Any]
    ) -> Answer[TMetadata]:
        """raises InvalidProductData if product_data does not match ProductStructure"""

        product = self.product_structure.validate(product_data)
        return Answer(metadata=metadata, product_data=product)
