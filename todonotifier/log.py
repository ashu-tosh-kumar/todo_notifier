"""This module centralizes the logging configuration of the package. It has no imports from the
rest of the package so that any module can import it without causing circular imports.
"""

import logging

PACKAGE_LOGGER_NAME = "todonotifier"
LOG_FORMAT = "%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO


def _configure_package_logger() -> None:
    """Configures the package level logger once. Only the package logger is configured and the root logger
    is left untouched so that applications using this library keep control of their own logging setup.
    """
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    if package_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    package_logger.addHandler(handler)
    package_logger.setLevel(LOG_LEVEL)
    package_logger.propagate = False  # Avoid duplicate records if the application configures the root logger


def get_logger(name: str) -> logging.Logger:
    """Provides a logger configured as per the package wide logging configuration

    Args:
        name (str): Name of the logger, typically `__name__` of the calling module

    Returns:
        logging.Logger: Configured logger
    """
    _configure_package_logger()
    return logging.getLogger(name)
