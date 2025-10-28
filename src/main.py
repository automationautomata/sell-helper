import os
from datetime import datetime

import providers as dep
from api.auth import router as auth_router
from api.search import router as search_router
from api.selling import router as selling_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import EbayConfig, PerplexityConfig, load_config
from core.infrastructure.hasher import IHasher
from data import EnvKeys
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from passlib.hash import pbkdf2_sha256
from utils import utils
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


ebay_mode = os.getenv("EBAY_MODE", "sandbox")

config = load_config()

EnvKeys.setting_ebay_mode(ebay_mode)

engine = create_async_engine(config.db.connection_string)

AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def lifespan(_):
    scheduler = AsyncIOScheduler()
    job = utils.token_update_job(scheduler, config.ebay[ebay_mode])
    scheduler.add_job(job, "date", run_date=datetime.now(), name="ebay token fetching")
    scheduler.start()

    yield

    await app.state.dishka_container.close()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/auth")
app.include_router(search_router, prefix="/search")
app.include_router(selling_router, prefix="/selling")
# app.middleware("http")(middleware.verification("/search", "/selling"))


providers = [
    dep.EbayProvider(),
    dep.ServicesFactoriesProvider(),
    dep.AuthServiceProvider(AsyncSessionLocal),
    FastapiProvider(),
]

mapping = dep.MarketplaceComponentMap(
    mapping=[dep.MarketplaceComponentPair("ebay", "ebay")]
)
context = {
    EbayConfig: config.ebay[ebay_mode],
    PerplexityConfig: config.perplexity,
    dep.JWTAuthSettings: dep.JWTAuthSettings(20, "HS256"),
    IHasher: pbkdf2_sha256,
    dep.MarketplaceComponentMap: mapping,
}

container = make_async_container(*providers, context=context)

setup_dishka(container, app)
