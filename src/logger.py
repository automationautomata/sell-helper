import logging
from logging.config import dictConfig

from colorlog import default_log_colors

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "class": "logging.Formatter",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(cyan)s%(asctime)s%(reset)s %(log_color)s[%(levelname)s]%(reset)s %(blue)s%(name)s%(reset)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": default_log_colors,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "app": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apscheduler": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


dictConfig(LOG_CONFIG)
logger = logging.getLogger("app")
