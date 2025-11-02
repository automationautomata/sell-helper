from typing import Callable

from ..core.services.search import SearchServiceABC
from ..core.services.selling import SellingServiceABC
from .models.common import Marketplace

SearchServicesFactory = Callable[[Marketplace], SearchServiceABC]

SellingServicesFactory = Callable[[Marketplace], SellingServiceABC]
