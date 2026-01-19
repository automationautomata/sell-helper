from pydantic import BaseModel


class Weight(BaseModel):
    unit: str
    value: float


class Dimension(BaseModel):
    height: float
    length: float
    width: float
    unit: str


class Package(BaseModel):
    weight: Weight
    dimensions: Dimension | None = None
