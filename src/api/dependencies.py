from typing import Callable

from api.models.common import Marketplace
from core.services.search import SearchServiceABC
from core.services.selling import SellingServiceABC


SerachServicesFactory = Callable[[Marketplace], SearchServiceABC]

SellingServicesFactory = Callable[[Marketplace], SellingServiceABC]
