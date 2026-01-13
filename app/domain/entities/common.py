from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, Self, Type


class AspectType(str, Enum):
    FLOAT = "float"
    DICT = "dict"
    LIST = "list"
    STR = "str"
    INT = "int"

    def py_type(self) -> Type:
        type_mapping = {
            AspectType.STR: str,
            AspectType.INT: int,
            AspectType.FLOAT: float,
            AspectType.LIST: list,
            AspectType.DICT: dict,
        }
        return type_mapping[self]


@dataclass(frozen=True)
class AspectField:
    name: str
    data_type: AspectType
    is_required: bool
    allowed_values: frozenset = field(default_factory=frozenset)

    def is_value_valid(self, value: Any) -> bool:
        if not isinstance(value, self.data_type.py_type()):
            return False
        if not self.allowed_values:
            return True
        return value in self.allowed_values


@dataclass(frozen=True)
class AspectValue:
    name: str
    value: Any
    is_required: bool


class Validatable(Protocol):
    @classmethod
    def validate(cls, data: dict[str]) -> Self | None:
        pass

    def asdict(self) -> dict[str]:
        pass
