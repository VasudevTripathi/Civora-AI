import logging
import sys
from loguru import logger
from backend.app.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # Remove existing standard logging handlers
    logging.root.handlers = []

    # Configure intercept handler for uvicorn & other standard libraries
    intercept_handler = InterceptHandler()
    logging.root.setLevel(settings.LOG_LEVEL)

    for logger_name in ("uvicorn.error", "uvicorn.access", "fastapi"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [intercept_handler]
        mod_logger.propagate = False

    # Configure Loguru
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": settings.LOG_LEVEL,
                "format": log_format,
                "colorize": True,
            }
        ]
    )

    logger.info("Structured logging has been initialized.")
