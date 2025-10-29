from datetime import datetime

import providers as p
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import DBConfig, EbayConfig, PerplexityConfig
from core.infrastructure.hasher import IHasher
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider
from fastapi.concurrency import asynccontextmanager
from passlib.hash import pbkdf2_sha256
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from utils import utils


def db_session(db: DBConfig) -> async_sessionmaker:
    engine = create_async_engine(db.connection_string)

    session_maker = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    return session_maker


def container(session: sessionmaker, ebay: EbayConfig, perplexity: PerplexityConfig):
    providers = [
        p.EbayProvider(),
        p.ServicesFactoriesProvider(),
        p.AuthServiceProvider(session),
        FastapiProvider(),
    ]

    mapping = p.MarketplaceComponentMap(
        mapping=[p.MarketplaceComponentPair("ebay", "ebay")]
    )
    context = {
        EbayConfig: ebay,
        PerplexityConfig: perplexity,
        p.JWTAuthSettings: p.JWTAuthSettings(20, "HS256"),
        IHasher: pbkdf2_sha256,
        p.MarketplaceComponentMap: mapping,
    }

    return make_async_container(*providers, context=context)


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
