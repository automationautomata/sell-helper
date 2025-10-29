import os

import setup
from api import middlewares
from api.auth import router as auth_router
from api.search import router as search_router
from api.selling import router as selling_router
from config import load_config
from data import EnvKeys
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

ebay_mode = os.getenv("EBAY_MODE", "sandbox")

config = load_config()

EnvKeys.setting_ebay_mode(ebay_mode)

ebay_config = config.ebay[ebay_mode]


app = FastAPI(lifespan=setup.lifespan(ebay_config))

app.include_router(auth_router, prefix="/auth")
app.include_router(search_router, prefix="/search")
app.include_router(selling_router, prefix="/selling")
app.middleware("http")(middlewares.verification("/search", "/selling"))


db_session = setup.db_session(config.db)
container = setup.container(db_session, ebay_config, config.perplexity)

setup_dishka(container, app)
