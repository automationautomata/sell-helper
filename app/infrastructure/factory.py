class InfraFactory[T]:
    def __init__(self, mapping: dict[str, T]):
        self.mapping = mapping

    def get(self, marketplace: str) -> T:
        val = self.mapping.get(marketplace, None)
        if val is None:
            return ValueError(f"marketplace {marketplace} not found")
        return val
