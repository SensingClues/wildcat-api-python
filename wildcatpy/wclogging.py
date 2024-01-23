# -*- coding: utf-8 -*-

"""WildCatApi logging"""

import logging
import sys

DEFAULT_LOGGER_NAME = "WildCatLogger"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = {
    "fmt": "{asctime:s} [{filename:s}:{lineno:d}] {levelname:s} - {message:s}",
    "style": "{",
    "datefmt": "%Y-%m-%d %H:%M:%S",
}


def get_wc_logger() -> logging.Logger:
    """Get the global WildCatApi logger

    Returns
    -------
    wc_logger : logging.Logger
        WildCatApi logger instance.
    """
    # get the WildCatApi logger
    wc_logger = logging.getLogger(DEFAULT_LOGGER_NAME)

    # set log level
    wc_logger.setLevel(DEFAULT_LOG_LEVEL)

    if not wc_logger.hasHandlers():
        # wc_logger.propagate = 0

        # create logging formatter
        log_fmt = logging.Formatter(**DEFAULT_LOG_FORMAT)

        # create default handler
        def_hand = logging.StreamHandler(stream=sys.stdout)
        def_hand.setFormatter(log_fmt)
        wc_logger.addHandler(def_hand)

    return wc_logger


def set_wc_log_level(level: str = None):
    """Set the WildCatApi log level

    If no level is supplied it will set the default log level.

    Parameters
    ----------
    level : str or None, optional
        Log level (default is `default_log_level` from WildCatApi config).
    """
    if level:
        log_level = level

    # get the logger; this will automatically set the level from the config
    wc_logger = get_wc_logger()
    wc_logger.debug(f'{wc_logger.name} log level set to "{log_level}".')
