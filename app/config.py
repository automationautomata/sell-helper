import os
from typing import ClassVar, Literal, Self

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .data import Pathes


class YAMLConfig(BaseModel):
    path: ClassVar[str] = ""

    @classmethod
    def load(cls) -> Self:
        with open(cls.path, "r") as f:
            data = yaml.safe_load(f)
            return cls.model_validate(data)


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", str_to_lower=True)
    env_prefix: ClassVar[str] = ""

    def __init__(self):
        self.model_config.update(env_prefix=self.env_prefix)
        super().__init__()


class EbayConfig(BaseModel):
    domain: Literal["api.ebay.com", "api.sandbox.ebay.com"]
    appid: str
    certid: str
    devid: str
    redirect_uri: str


class PerplexityConfig(BaseModel):
    model: str


class ExternalServicesConfig(YAMLConfig):
    path = os.getenv("CONFIG_PATH", Pathes.CONFIG)

    ebay: EbayConfig
    perplexity: PerplexityConfig


class Tokens(EnvConfig):
    barcode_searcher_token: str
    perplexity_token: str


class Secrets(EnvConfig):
    env_prefix = "secret_"

    jwt: str
    session: str


class DBConfig(EnvConfig):
    env_prefix = "db_"

    driver: str
    host: str
    port: int
    user: str
    password: str
    name: str

    def get_url(self) -> str:
        return (
            f"{self.driver}://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


class RedisConfig(EnvConfig):
    env_prefix = "redis_"

    host: str
    port: int
    db_number: int = 0

    def get_url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db_number}"


class Config(BaseModel):
    external_services: ExternalServicesConfig = Field(
        default_factory=ExternalServicesConfig.load
    )
    db: DBConfig = Field(default_factory=DBConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    secrets: Secrets = Field(default_factory=Secrets)
    tokens: Tokens = Field(default_factory=Tokens)
