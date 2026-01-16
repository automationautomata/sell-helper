from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class MarketplaceAccount:
    user_uuid: UUID
    marketplace: str


@dataclass
class AccountSettings:
    settings: dict[str, list] = field(default_factory=dict)
