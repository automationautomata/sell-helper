import os

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from . import setup
from .api.middlewares import authentication
from .api.search import PREFIX as SEARCH_PREFIX
from .api.selling import PREFIX as SELLING_PREFIX

ebay_mode = os.getenv("EBAY_MODE", "sandbox")

config = setup.load_config(ebay_mode)

app = FastAPI()

root_prefix = "/api"
app.include_router(setup.root_router(root_prefix))

auth_prefixes = [f"{root_prefix}{SEARCH_PREFIX}", f"{root_prefix}{SELLING_PREFIX}"]
app.middleware("http")(authentication(*auth_prefixes))

db_session = setup.db_session(config.db)
container = setup.container(db_session, config.ebay, config.perplexity)

setup_dishka(container, app)
