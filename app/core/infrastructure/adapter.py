import re
from dataclasses import make_dataclass
from typing import Any, Dict, Literal, Optional

from pydantic import TypeAdapter, ValidationError

from ..domain.entities.errors import InvalidProductData
from ..domain.entities.question import Answer, Question


class QuestionAdapterError(Exception):
    pass


class InvalidMetadata(QuestionAdapterError):
    pass


class InvalidProduct(QuestionAdapterError):
    pass


class QuestionAdapter:
    _QUESTION_DATACLASS_NAME = "Question"
    _PRODUCT_FIELD_NAME = "product"
    _METADATA_FIELD_NAME = "metadata"

    @classmethod
    def to_schema(cls, qusetion: Question) -> Dict[str, Any]:
        question_class = cls._dataclass_from_question(qusetion)
        return TypeAdapter(question_class).json_schema()

    @classmethod
    def to_answer(cls, raw_data: Dict[str, Any], qusetion: Question) -> Answer:
        product_data = raw_data.get(cls._PRODUCT_FIELD_NAME, {})
        product_data = {cls._restore_name(k): v for k, v in product_data.items()}

        raw_metadata = raw_data.get(cls._METADATA_FIELD_NAME, {})
        try:
            metadata = TypeAdapter(qusetion.metadata_type).validate_python(raw_metadata)
            metadata.description = cls.remove_sources(metadata.description)
        except ValidationError as e:
            raise InvalidMetadata() from e

        try:
            return qusetion.get_answer(metadata, product_data)
        except InvalidProductData as e:
            raise InvalidProduct() from e

    @classmethod
    def _dataclass_from_question(cls, qusetion: Question) -> type:
        fields = []
        for aspect in qusetion.product_structure.fields:
            name = cls._format_name(aspect.name)

            if aspect.allowed_values:
                data_type = Literal[tuple(aspect.allowed_values)]
            else:
                data_type = aspect.data_type.py_type()

            if aspect.is_required:
                field = name, data_type
            else:
                field = name, Optional[data_type], None

            fields.append(field)

        product_dataclass = make_dataclass("Product", fields)
        metadata_type = qusetion.metadata_type
        _class = make_dataclass(
            cls._QUESTION_DATACLASS_NAME,
            [
                (cls._PRODUCT_FIELD_NAME, product_dataclass),
                (cls._METADATA_FIELD_NAME, metadata_type),
            ],
        )
        return _class

    @staticmethod
    def remove_sources(text: str) -> str:
        """Removes reference markers such as [1], [5][7][13]"""
        cleaned = re.sub(r"(?:\[\d+\])+", "", text)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _format_name(name: str):
        return name.replace(" ", "_").replace("/", "_or_")

    @staticmethod
    def _restore_name(name: str):
        return name.replace("_or_", "/").replace("_", " ")
