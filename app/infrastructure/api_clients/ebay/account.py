from itertools import product
from typing import TypedDict

import requests

from ..utils import request_exception_chain
from .base import EbayRequestError, EbayUserClient
from .models import MarketplaceIdEnum


class EbayAccountClientError(EbayRequestError):
    pass


class Policy(TypedDict):
    id: str
    name: str
    marketplace_id: str
    category_types: list[str]


class Policies(TypedDict):
    fulfillment_policies: list[Policy]
    payment_policies: list[Policy]
    return_policies: list[Policy]


class EbayAccountClient(EbayUserClient):
    _api_endpoint = "sell/account/v1"

    @request_exception_chain(default=EbayAccountClientError)
    def get_all_policies(self, token: str) -> Policies:
        policy_types = ["fulfillment", "payment", "return"]

        policies = Policies(
            fulfillment_policies=[],
            payment_policies=[],
            return_policies=[],
        )
        for marketplace_id, policy_type in product(policy_types, MarketplaceIdEnum):
            resp = requests.get(
                url=self.url(f"/{policy_type}_policy"),
                params={"marketplace_id": marketplace_id},
                headers={
                    **self._user_auth_header(token),
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()

            for policy in data[f"{policy_type}Policies"]:
                category_types = policy["categoryTypes"]

                policies[f"{policy_type}_policies"].append(
                    Policy(
                        id=policy[f"{policy_type}PolicyId"],
                        name=policy["name"],
                        marketplace_id=marketplace_id,
                        category_types=[t["name"] for t in category_types],
                    )
                )
            return policies
