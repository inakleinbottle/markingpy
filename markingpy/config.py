import logging
import os

from configparser import ConfigParser
from pkgutil import get_data
from pathlib import Path

__all__ = ['CONFIG_PATHS', 'LOGGING_LEVELS', 'GLOBAL_CONF', 'logger']
CONFIG_PATHS = [Path.home() / ".markingpy"]
LOGGING_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def load_config() -> ConfigParser:
    """
    Configuration file loader for markingpy.
    """
    parser = ConfigParser()
    parser.read_string(get_data("markingpy", "data/markingpy.conf").decode())
    parser.read(CONFIG_PATHS)
    DEBUG_FLAG = os.getenv("MARKINGPY_DEBUG", None)
    if DEBUG_FLAG:
        parser["logging"]["level"] = "debug"
    return parser


GLOBAL_CONF = load_config()
logging.basicConfig(level=LOGGING_LEVELS[GLOBAL_CONF["logging"]["level"]])
logger = logging.getLogger(__name__)
