import logging
import logging.config
import sys


def get_level() -> str:
    from tg_filtering_bot.config import settings
    return "DEBUG" if settings.DEBUG else "INFO"


LOG_CONFIG = dict(
    version=1,
    disable_existing_loggers=False,
    handlers={
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout,
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stderr,
            "level": "ERROR"
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout,
        },
    },
    formatters={
        "generic": {
            "format": "%(asctime)s | [%(process)d] | [%(levelname)s] | %(name)s | %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
        "access": {
            "format": "%(asctime)s | [%(process)d] | [%(levelname)s] | %(name)s | [%(host)s]: "
                      + "%(request)s %(message)s %(status)d %(byte)d",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
    loggers={
        '': {
            "level": get_level(),
            "handlers": ["stderr", "stdout"]
        },
        # "FilteringBot": {
        #     "level": "INFO",
        #     "handlers": ["stderr", "stdout"]
        # },
        # "MonitoringClient": {
        #     "level": "INFO",
        #     "handlers": ["stderr", "stdout"]
        # },
        # "MainService": {
        #     "level": "INFO",
        #     "handlers": ["stderr", "stdout"]
        # }
    },
)

logging.config.dictConfig(LOG_CONFIG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
