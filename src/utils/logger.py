"""
mr.nightwatch
27.07.2026

logger.py
Logging configuration for the nullmeta CLI.

This module provides the setup_logging function which configures the
application's logging with Rich Handlers for beautiful terminal output.
"""

# General libraries
import logging

# rich
from rich.logging import RichHandler


def setup_logging(verbose: bool = False):
    """
    Method setup_logging(
    verbose: bool (by default is False)
    )
    Explanation:
        Configure application logging with Rich formatting

    Functioning:
        Sets up the logger with appropriate level and Rich Handlers for
        beautiful terminal output including colorful Stack Traces.

    Args:
        verbose : If True, enables DEBUG level Logging.
                  If False (default), enables INFO level Logging.

    Returns:
        Logger instance for "nullmeta".
    """

    # Define the log level
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure the logger
    # Remove the existing Handlers to avoid duplicate lines if the app restarts
    logging.getLogger().handlers.clear()

    logging.basicConfig(
        level    = level,
        format   = "%(message)s",
        datefmt  = "[%X]",
        handlers = [
            RichHandler(
                rich_tracebacks = True,  # Beautiful colorful Stack Traces
                markup          = True,  # Allow [bold red] styles in logs
                show_path       = False,
            )
        ],
    )

    # Return the logger instance
    return logging.getLogger("nullmeta")