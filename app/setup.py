import os
from datetime import datetime
from typing import Literal

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider
from fastapi import APIRouter
from fastapi.concurrency import asynccontextmanager
from passlib.hash import pbkdf2_sha256
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from . import dependencies as dep
from .api.auth import router as auth_router
from .api.search import router as search_router
from .api.selling import router as selling_router
from .config import Config, DBConfig, EbayConfig, PerplexityConfig
from .core.infrastructure.hasher import IHasher
from .data import EnvKeys, Pathes
from .utils import utils


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
        class_=AsyncSession
    )
    return session_maker


def lifespan(ebay_config: EbayConfig):
    @asynccontextmanager
    async def lifespan(app):
        scheduler = AsyncIOScheduler()
        job = utils.token_update_job(scheduler, ebay_config)
        scheduler.add_job(
            job, "date", run_date=datetime.now(), name="ebay token fetching"
        )
        scheduler.start()

        yield

        await app.state.dishka_container.close()

    return lifespan


def root_router(prefix: str):
    root_router = APIRouter(prefix=prefix)
    root_router.include_router(auth_router)
    root_router.include_router(search_router)
    root_router.include_router(selling_router)
    return root_router


def container(session: sessionmaker, ebay: EbayConfig, perplexity: PerplexityConfig):
    providers = [
        dep.EbayProvider(),
        dep.ServicesFactoriesProvider(),
        dep.AuthServiceProvider(session),
        FastapiProvider(),
    ]

    context = {
        EbayConfig: ebay,
        PerplexityConfig: perplexity,
        dep.JWTAuthSettings: dep.JWTAuthSettings(20, "HS256"),
        IHasher: pbkdf2_sha256,
    }

    return make_async_container(*providers, context=context)
