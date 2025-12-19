import os
from typing import Literal

import yaml
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider
from fastapi import APIRouter
from passlib.hash import pbkdf2_sha256
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .api.login import router as login_router
from .api.registration import router as reg_router
from .api.search import router as search_router
from .api.selling import router as selling_router
from .config import Config, DBConfig, EbayConfig, PerplexityConfig
from .core.infrastructure.providers import (
    EbayInfrastructureProvider,
    JWTAuthProvider,
    JWTAuthSettings,
    PerplexitySettings,
)
from .core.repository.providers import RepositoryProvider
from .core.services.ports import IHasher
from .core.services.providers import AuthServiceProvider, ServicesProvider
from .data import EnvKeys, Pathes
from .providers import (
    DBProvider,
    EbayProvider,
    PerplexityClientProvider,
    ServicesFactoriesProvider,
)


def _load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_config(ebay_mode: Literal["sandbox", "production"]) -> Config:
    ebay_path = os.getenv(EnvKeys.EBAY_CONFIG_PATH, Pathes.EBAY_CONFIG)
    perplexity_path = os.getenv(
        EnvKeys.PERPLEXITY_CONFIG_PATH, Pathes.PERPLEXITY_CONFIG
    )
    ebay_configs = {
        k: EbayConfig.model_validate(v) for k, v in _load_yaml(ebay_path).items()
    }
    EnvKeys.setting_ebay_mode(ebay_mode)
    return Config(
        db=DBConfig(connection_string=os.getenv(EnvKeys.DB_URL)),
        perplexity=PerplexityConfig.model_validate(_load_yaml(perplexity_path)),
        ebay=ebay_configs[ebay_mode],
    )


def db_session(db: DBConfig) -> sessionmaker:
    engine = create_async_engine(db.connection_string)

    session_maker = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return session_maker


def root_router(prefix: str):
    root_router = APIRouter(prefix=prefix)
    root_router.include_router(reg_router)
    root_router.include_router(login_router)
    root_router.include_router(search_router)
    root_router.include_router(selling_router)
    return root_router


def container(session: sessionmaker, ebay: EbayConfig, perplexity: PerplexityConfig):
    providers = [
        DBProvider(session),
        EbayProvider(),
        PerplexityClientProvider(),
        JWTAuthProvider(),
        EbayInfrastructureProvider(),
        RepositoryProvider(),
        AuthServiceProvider(),
        ServicesProvider().to_component("ebay"),
        ServicesFactoriesProvider(),
        FastapiProvider(),
    ]

    context = {
        EbayConfig: ebay,
        PerplexitySettings: PerplexitySettings(model=perplexity.model),
        JWTAuthSettings: JWTAuthSettings(20, "HS256"),
        IHasher: pbkdf2_sha256,
    }
    return make_async_container(*providers, context=context)
