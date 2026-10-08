"""Structured logging configuration for VrikshaVision backend."""

import logging
import sys
from app.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"


def setup_logging() -> logging.Logger:
    """Configures root logger with consistent console formatting."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logger = logging.getLogger("vrikshavision")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
