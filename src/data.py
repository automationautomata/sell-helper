from os.path import dirname, join
from typing import Literal


class Pathes:
    BASE_DIR = dirname(dirname(__file__))

    CONFIG_DIR = join(BASE_DIR, "config")

    EBAY_CONFIG = join(CONFIG_DIR, "ebay.yaml")

    PERPLEXITY_CONFIG = join(CONFIG_DIR, "search.yaml")

    SCHEMA = join(CONFIG_DIR, "schema.json")

    QUESTIONS = join(CONFIG_DIR, "questions.yaml")


class EnvKeys:
    EBAY_CONFIG_PATH = "EBAY_CONFIG_PATH"

    PERPLEXITY_CONFIG_PATH = "PERPLEXITY_CONFIG_PATH"

    EBAY_USER_TOKEN = "EBAY_USER_TOKEN"

    BARCODE_SEARCH_TOKEN = "BARCODE_SEARCH_TOKEN"

    EBAY_SANDBOX_REFRESH_TOKEN = "EBAY_SANDBOX_REFRESH_TOKEN"

    EBAY_PRODUCTION_REFRESH_TOKEN = "EBAY_PRODUCTION_REFRESH_TOKEN"

    JWT_SECRET = "JWT_SECRET"

    DB_URI = "DB_URI"

    @staticmethod
    def setting_ebay_mode(mode: Literal["sandbox", "production"]):
        if mode == "sandbox":
            EnvKeys.EBAY_REFRESH_TOKEN = EnvKeys.EBAY_SANDBOX_REFRESH_TOKEN
            return
        EnvKeys.EBAY_REFRESH_TOKEN = EnvKeys.EBAY_PRODUCTION_REFRESH_TOKEN
