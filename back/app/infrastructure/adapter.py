from dataclasses import dataclass, is_dataclass

from pydantic import TypeAdapter, ValidationError

from app.domain.entities import (
    AspectField,
    AspectType,
    IMetadata,
    Product,
    ProductStructure,
)
from app.domain.entities.errors import AspectsValidationError


class ProductAdapterError(Exception):
    pass


class InvalidMetadataError(ProductAdapterError):
    pass


class InvalidAspectsError(ProductAdapterError):
    pass


@dataclass
class ProductAdapter[M: IMetadata]:
    _ASPECTS_FIELD_NAME = "aspects"
    _METADATA_FIELD_NAME = "metadata"

    metadata_type: type[M]

    def to_product(
        self,
        raw_data: dict[str],
        product_structure: ProductStructure,
    ) -> Product[M]:
        try:
            aspect_values = product_structure.validate(
                raw_data.get(self._ASPECTS_FIELD_NAME, {})
            )
            metadata = TypeAdapter(self.metadata_type).validate_python(
                raw_data.get(self._METADATA_FIELD_NAME, {})
            )
            return Product(metadata=metadata, aspects=aspect_values)
        except AspectsValidationError as e:
            raise InvalidAspectsError() from e
        except ValidationError as e:
            raise InvalidMetadataError() from e

    def to_schema(
        self,
        aspects: list[AspectField],
        allow_additional_aspects: bool = False,
    ) -> dict[str]:
        aspects_schema = self._build_aspects_schema(
            aspects,
            allow_additional_properties=allow_additional_aspects,
        )

        metadata_schema, metadata_defs = self._build_metadata_schema(self.metadata_type)

        aspecs_def_name = self._ASPECTS_FIELD_NAME.capitalize()
        metadata_def_name = self._METADATA_FIELD_NAME.capitalize()
        return {
            "type": "object",
            "properties": {
                self._ASPECTS_FIELD_NAME: {"$ref": f"#/$defs/{aspecs_def_name}"},
                self._METADATA_FIELD_NAME: {"$ref": f"#/$defs/{metadata_def_name}"},
            },
            "required": ["aspects", "meatadata"],
            "additionalProperties": False,
            "$defs": {
                aspecs_def_name: aspects_schema,
                metadata_def_name: metadata_schema,
                **metadata_defs,
            },
        }

    @classmethod
    def _build_aspects_schema(
        cls, aspects: list[AspectField], allow_additional_properties: bool
    ) -> dict[str]:
        def to_json_type(aspect_type):
            mapping = {
                AspectType.STR: "string",
                AspectType.INT: "integer",
                AspectType.FLOAT: "number",
                AspectType.LIST: "array",
                AspectType.DICT: "object",
            }
            return mapping[aspect_type]

        properties = {}
        required = []
        defs = {}

        for aspect in aspects:
            defs[aspect.name] = {
                "type": to_json_type(aspect.data_type),
            }
            if aspect.allowed_values:
                defs[aspect.name].update({"enum": list(aspect.allowed_values)})

            properties[aspect.name] = {"$ref": f"#/$defs/{aspect.name}"}

            if aspect.is_required:
                required.append(aspect.name)

        schema: dict[str] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": allow_additional_properties,
            "$defs": defs,
        }

        if required:
            schema["required"] = required

        return schema

    @classmethod
    def _build_metadata_schema(
        cls, metadata_type: type[IMetadata]
    ) -> tuple[dict[str], dict[str]]:
        if not is_dataclass(metadata_type):
            raise ProductAdapterError("metadata must be a dataclass")

        full_schema = TypeAdapter(metadata_type).json_schema()

        defs = full_schema.get("$defs", {}).copy()

        if "$ref" in full_schema:
            ref_name = full_schema["$ref"].split("/")[-1]
            product_schema = defs.pop(ref_name)
        else:
            product_schema = full_schema

        product_schema.setdefault("type", "object")
        product_schema.setdefault("additionalProperties", False)

        return product_schema, defs
