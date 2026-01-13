from dataclasses import dataclass
from uuid import UUID


@dataclass
class MarketplaceAccount:
    user_uuid: UUID
    marketplace: str
