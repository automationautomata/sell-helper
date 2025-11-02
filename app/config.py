from typing import Literal

from pydantic import BaseModel

EbayDomain = Literal["api.ebay.com", "api.sandbox.ebay.com"]


class EbayConfig(BaseModel):
    class ListingPoliciesConfig(BaseModel):
        fulfillment_policy_id: str
        payment_policy_id: str
        return_policy_id: str

    domain: EbayDomain
    appid: str
    certid: str
    devid: str
    redirecturi: str
    listing_policies: ListingPoliciesConfig
    marketplace_id: str


class PerplexityConfig(BaseModel):
    model: str


class DBConfig(BaseModel):
    connection_string: str


class Config(BaseModel):
    perplexity: PerplexityConfig
    ebay: EbayConfig
    db: DBConfig
