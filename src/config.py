import os
from typing import Dict, Literal

import yaml
from data import EnvKeys, Pathes
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


class Config(BaseModel):
    perplexity: PerplexityConfig
    ebay: Dict[str, EbayConfig]


def _load_yaml(path: str) -> Dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_config():
    ebay_path = os.getenv(EnvKeys.EBAY_CONFIG_PATH, Pathes.EBAY_CONFIG)
    perplexity_path = os.getenv(
        EnvKeys.PERPLEXITY_CONFIG_PATH, Pathes.PERPLEXITY_CONFIG
    )
    return Config(
        perplexity=PerplexityConfig.model_validate(_load_yaml(perplexity_path)),
        ebay={
            k: EbayConfig.model_validate(v) for k, v in _load_yaml(ebay_path).items()
        },
    )
