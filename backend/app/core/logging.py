"""
Logging configuration module.

Provides centralized logging setup for the ProcureAI backend.
Ensures consistent log formatting and levels across all modules.
"""

import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """
    Configure application-wide logging.

    Args:
        debug: When True, sets log level to DEBUG; otherwise INFO.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Reduce noise from third-party libraries in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger for a module.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
