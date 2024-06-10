import logging.config

from infrastructure.config import LoggingSettings


def configure_logging() -> None:
    logging_settings = LoggingSettings()
    console_formatter = {"verbose": {"format": logging_settings.log_format}}
    console_handlers = {
        "console": {
            "level": logging_settings.log_level,
            "class": "logging.StreamHandler",
            "formatter": "verbose"
        }
    }
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": console_formatter,
        "handlers": console_handlers,
        "loggers": {"": {"handlers": ["console"]}},
        "root": {"level": logging_settings.log_level, "handlers": ["console"]}
    }
    logging.config.dictConfig(logging_config)
