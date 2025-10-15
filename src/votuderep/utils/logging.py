"""Logging configuration using rich for pretty output."""

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


# Global console instance for rich output
console = Console(stderr=True)


def setup_logger(
    name: str = "votuderep", level: int = logging.INFO, verbose: bool = False
) -> logging.Logger:
    """
    Set up a logger with rich handler.

    Args:
        name: Logger name
        level: Logging level
        verbose: If True, set level to DEBUG

    Returns:
        Configured logger instance
    """
    # Adjust level if verbose
    if verbose:
        level = logging.DEBUG

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create rich handler
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
    )
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name, defaults to 'votuderep'

    Returns:
        Logger instance
    """
    if name is None:
        name = "votuderep"
    return logging.getLogger(name)
