from dishka.integrations.fastapi import setup_dishka

from app import setup

config = setup.load_config()

app = setup.app(config)

container = setup.container(config)

setup_dishka(container, app)
