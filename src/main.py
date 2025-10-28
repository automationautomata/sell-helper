from datetime import datetime

from api.search import router as search_router
from api.selling import router as selling_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import load_config
from core.domain.ebay.item import EbayMarketplaceAspects
from core.domain.ebay.question import EbayMetadata
from core.infrastructure.adapter import QuestionAdapter
from core.infrastructure.marketplace import EbayAPI
from core.infrastructure.search import PerplexityAndEbaySearch
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka, FastapiProvider
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from providers import (
    SearchServiceProvider,
    SearchSettings,
    SearchSettingsMap,
    SellingServiceProvider,
    SellingSettings,
    SellingSettingsMap,
)
from utils import utils

config = load_config()

ebay_config = config.ebay["sandbox" if __debug__ else "production"]

seacrh_engine = PerplexityAndEbaySearch(
    config.perplexity.model, ebay_config=ebay_config
)

marketplace_api = EbayAPI(ebay_config, lambda: "")


@asynccontextmanager
async def lifespan(_):
    scheduler = AsyncIOScheduler()
    job = utils.token_update_job(scheduler, ebay_config)
    scheduler.add_job(job, "date", run_date=datetime.now(), name="ebay token fetching")
    scheduler.start()

    yield

    await app.state.dishka_container.close()


app = FastAPI(lifespan=lifespan)

app.include_router(search_router, prefix="/search")
app.include_router(selling_router, prefix="/selling")


context = {
    SearchSettingsMap: SearchSettingsMap(
        map={
            "ebay": SearchSettings(
                seacrh_engine, marketplace_api, QuestionAdapter(), EbayMetadata
            )
        }
    ),
    SellingSettingsMap: SellingSettingsMap(
        map={
            "ebay": SellingSettings(
                marketplace_api=marketplace_api,
                marketplace_aspects_type=EbayMarketplaceAspects,
            ),
        }
    ),
}
container = make_async_container(
    SearchServiceProvider(),
    SellingServiceProvider(),
    FastapiProvider(),
    context=context,
)

setup_dishka(container, app)
