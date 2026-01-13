from dataclasses import dataclass

from .common import AspectField, AspectValue
from .errors import AspectsValidationError


@dataclass
class ProductStructure:
    """Collection of aspects that define a product's structure."""

    fields: list[AspectField]

    def validate(self, raw_data: dict[str]) -> list[AspectValue]:
        names = {f.name: f for f in self.fields}
        required = {f.name for f in self.fields if f.is_required}

        values: list[AspectValue] = []

        for name, value in raw_data.items():
            field = names.get(name)
            if field is None:
                raise AspectsValidationError(
                    f"Unexpected aspect '{name}' in product data."
                )

            if not field.is_value_valid(value):
                expected_type_name = field.data_type.py_type().__name__
                raise AspectsValidationError(
                    f"Aspect '{name}' has incorrect or disallowed value. "
                    f"Expected type {expected_type_name}, got {type(value).__name__}."
                )

            values.append(
                AspectValue(name=name, value=value, is_required=field.is_required)
            )
            required.discard(name)

        if required:
            missing = ", ".join(sorted(required))
            raise AspectsValidationError(f"Missing required aspects: {missing}")

        return values
