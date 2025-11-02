from typing import Protocol


class IHasher(Protocol):
    def verify(plain: str, hash: str) -> bool:
        pass
