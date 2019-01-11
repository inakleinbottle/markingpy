import logging

from configparser import ConfigParser
from pkgutil import get_data
from os.path import expanduser, join as pathjoin

CONFIG_PATHS = [expanduser(pathjoin("~", ".markingpy"))]

LOGGING_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def load_config():
    """
    Configuration file loader for markingpy.
    """
    parser = ConfigParser()
    parser.read_string(get_data("markingpy", "data/markingpy.conf").decode())
    parser.read(CONFIG_PATHS)
    return parser


GLOBAL_CONF = load_config()
